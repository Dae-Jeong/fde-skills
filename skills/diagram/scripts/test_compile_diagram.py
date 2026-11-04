"""Regression checks for geometry, schema, themes, cache ownership and CLI behavior."""
import base64
import copy
import html
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import compile_diagram as compiler
import fetch_icons
import render_png

ROOT = pathlib.Path(__file__).resolve().parents[1]


class DiagramRegressionTests(unittest.TestCase):
    def spec(self, row=0, col=1):
        return {'nodes': [{'id': 'a', 'name': 'A', 'row': 0, 'col': 0},
                          {'id': 'b', 'name': 'B', 'row': row, 'col': col}],
                'edges': [{'from': 'a', 'to': 'b', 'label': 'send'}]}

    def examples(self):
        return sorted((ROOT / 'examples').glob('0[1-5]*.json'))

    def html(self, spec, icons=None):
        return compiler.render_html(spec, *compiler.compute_layout(spec),
                                    icons or ROOT / 'examples/icons', ROOT / 'assets/fonts')

    def stress_specs(self):
        fanout = {'nodes': [{'id': 'gw', 'row': 0, 'col': 2, 'name': 'Gateway'}]
                  + [{'id': f's{i}', 'row': 1, 'col': i, 'name': f'S{i}'} for i in range(5)]
                  + [{'id': 'db', 'row': 2, 'col': 2, 'name': 'DB'}],
                  'edges': [{'from': 'gw', 'to': f's{i}', 'label': f'call service {i}'} for i in range(5)]
                  + [{'from': f's{i}', 'to': 'db', 'label': f'write table {i}', 'type': 'internal'} for i in range(5)]}
        skip = {'nodes': [{'id': 'a', 'row': 0, 'col': 1, 'name': 'A'},
                          {'id': 'b', 'row': 1, 'col': 0, 'name': 'B'},
                          {'id': 'c', 'row': 1, 'col': 1, 'name': 'C'},
                          {'id': 'd', 'row': 1, 'col': 2, 'name': 'D'},
                          {'id': 'e', 'row': 2, 'col': 1, 'name': 'E'}],
                'edges': [{'from': 'a', 'to': 'b', 'label': 'sync call'},
                          {'from': 'a', 'to': 'd', 'label': 'async call', 'type': 'dashed'},
                          {'from': 'a', 'to': 'c', 'label': 'adjacent'},
                          {'from': 'a', 'to': 'e', 'label': 'skip row'}]}
        ko = {'lang': 'ko', 'groups': [
            {'id': 'g1', 'label': '한글 그룹 라벨이 충분히 긴 경우의 배치', 'nodes': ['a', 'b']},
            {'id': 'g2', 'label': '저장소 계층', 'nodes': ['c', 'd']}],
            'nodes': [{'id': 'a', 'row': 0, 'col': 0, 'name': '주문 서비스'},
                      {'id': 'b', 'row': 0, 'col': 1, 'name': '결제 서비스'},
                      {'id': 'c', 'row': 1, 'col': 0, 'name': '주문 DB'},
                      {'id': 'd', 'row': 1, 'col': 1, 'name': '결제 DB'}],
            'edges': [{'from': a, 'to': b, 'label': text} for a, b, text in [
                ('a', 'b', '결제 요청 전송'), ('b', 'a', '결제 결과 콜백'),
                ('a', 'd', '교차 조회'), ('b', 'c', '역방향 조회'),
                ('a', 'c', '주문 저장'), ('b', 'd', '결제 저장')]]}
        return fanout, skip, ko

    def test_no_label_conflicts(self):
        specs = [json.loads(p.read_text()) for p in self.examples()] + list(self.stress_specs())
        for i, spec in enumerate(specs):
            with self.subTest(spec=i):
                layout = compiler.compute_layout(spec)
                self.assertEqual(compiler.collect_conflicts(*layout[:4]), [])
                self.assertEqual(layout, compiler.compute_layout(spec))

    def test_final_checker_detects_candidate_conflicts(self):
        layout = compiler.compute_layout(self.spec())
        nodes, groups, boxes, edges = layout[:4]
        edges[0].update(lx=nodes['a']['cx'], ly=nodes['a']['top'] + 30, anchor='middle')
        self.assertTrue(compiler.collect_conflicts(nodes, groups, boxes, edges))
        with self.assertRaises(compiler.DiagramError):
            compiler.verify_no_collisions(nodes, groups, boxes, edges)

    def test_expected_legends(self):
        expected = [('primary', 'internal', 'dashed'), ('primary', 'internal', 'dashed'),
                    ('primary', 'internal'), ('primary', 'dashed', 'warn'), ()]
        for path, kinds in zip(self.examples(), expected):
            with self.subTest(example=path.name):
                spec = json.loads(path.read_text())
                document = self.html(spec)
                match = re.search(r'<div class="legend">(.*?)</div>', document, re.S)
                self.assertEqual(bool(match), bool(kinds))
                if match:
                    self.assertEqual(len(re.findall('<span><span', match[1])), len(kinds))
                    for kind in kinds:
                        self.assertIn(html.escape(spec['legend_labels'][kind]), match[1])
                self.assertEqual(compiler.spec_warnings(spec), [])

    def test_token_contrast(self):
        def lum(color):
            rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
            return sum(v * w for v, w in zip(linear, (.2126, .7152, .0722)))
        def contrast(a, b):
            x, y = sorted((lum(a), lum(b)))
            return (y + .05) / (x + .05)
        for tokens in (compiler.TOKENS_LIGHT, compiler.TOKENS_DARK):
            for status in ('primary', 'warn', 'danger', 'success'):
                self.assertGreaterEqual(contrast(tokens[f'status-{status}-fg'], tokens[f'status-{status}-bg']), 4.5)
                if status != 'primary':
                    self.assertGreaterEqual(contrast(tokens[f'status-{status}-stripe'], tokens['color-paper-2']), 3)
            for text in ('color-muted', 'color-accent-ink', 'color-purple-ink'):
                for surface in ('color-paper', 'color-paper-2'):
                    self.assertGreaterEqual(contrast(tokens[text], tokens[surface]), 4.5)

    def test_all_examples_labeled(self):
        for path in self.examples():
            self.assertTrue(all(e.get('label') for e in json.loads(path.read_text())['edges']))

    def test_cli_errors_no_traceback(self):
        bad = [[], {}, dict(self.spec(), unexpected=True), dict(self.spec(), legend=False),
               dict(self.spec(), legend_labels={'nonsense': 'Wrong'})]
        mutations = [('row', True), ('id', 3), ('wide', 'false'), ('tile', 'accent'),
                     ('status', 'warn'), ('name', 'x' * 37), ('badge', 3), ('rowz', 1)]
        for key, value in mutations:
            spec = self.spec()
            spec['nodes'][0][key] = value
            bad.append(spec)
        card = self.spec()
        card['mode'] = 'flow'
        card['nodes'][0]['step'] = []
        bad.append(card)
        with tempfile.TemporaryDirectory() as directory:
            source, out = pathlib.Path(directory) / 'spec.json', pathlib.Path(directory) / 'out.html'
            out.write_text('preserve')
            for text in [json.dumps(s) for s in bad] + ['{', '{"nodes":[],"nodes":[]}', '{"nodes":NaN}']:
                with self.subTest(text=text):
                    source.write_text(text)
                    result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/compile_diagram.py'),
                                             'build', str(source), str(out)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn('diagram: error:', result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertEqual(out.read_text(), 'preserve')

    def test_preflight_before_assets_and_png_write(self):
        with tempfile.TemporaryDirectory() as directory:
            source, out = pathlib.Path(directory) / 'spec.json', pathlib.Path(directory) / 'out.html'
            source.write_text(json.dumps(self.spec()))
            with patch.object(sys, 'argv', ['diagram', 'build', str(source), str(out), '--png']), \
                 patch.object(compiler.importlib.util, 'find_spec', return_value=None), \
                 patch.object(compiler, 'ensure_icons') as fetch:
                with self.assertRaises(compiler.DiagramError):
                    compiler.run()
                fetch.assert_not_called()
                self.assertFalse(out.exists())

    def test_png_requests_light_theme(self):
        calls = []
        class FakePage:
            def evaluate(self, script):
                calls.append(script)
                return 800 if 'offsetWidth' in script else None
            def goto(self, *args): pass
            def add_style_tag(self, **kwargs): pass
            def query_selector(self, *args): return self
            def screenshot(self, **kwargs): calls.append(kwargs)
        class FakeBrowser:
            def new_page(self, **kwargs): return FakePage()
            def close(self): pass
        class FakePlaywright:
            chromium = types.SimpleNamespace(launch=lambda **kwargs: FakeBrowser())
            def __enter__(self): return self
            def __exit__(self, *args): pass
        module = types.ModuleType('playwright.sync_api')
        module.sync_playwright = FakePlaywright
        with patch.dict(sys.modules, {'playwright': types.ModuleType('playwright'), 'playwright.sync_api': module}), \
             patch.object(sys, 'argv', ['render_png.py', 'in.html', 'out.png']), redirect_stdout(io.StringIO()):
            render_png.main()
        self.assertIn("document.documentElement.setAttribute('data-theme','light')", calls)
        self.assertIn("document.documentElement.setAttribute('data-theme','dark')", calls)
        self.assertEqual(sum(isinstance(c, dict) and 'path' in c for c in calls), 2)

    def test_icon_key_variant_no_collision(self):
        svg = lambda color: ('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60"><path fill="'
                             + color + '" d="M0 0h60v60H0z"/></svg>').encode()
        assets = {'mark-light': svg('red'), 'mark-dark': svg('blue'), 'mark_dark-light': svg('green'),
                  'mark_dark-dark': svg('yellow')}
        for order in (['mark', 'mark_dark'], ['mark_dark', 'mark']):
            with self.subTest(order=order), tempfile.TemporaryDirectory() as directory:
                icons = pathlib.Path(directory)
                def lookup(slug):
                    return [('test', slug + '-light', slug + '-dark')]
                for key in order + ['mark']:
                    with patch.object(fetch_icons, 'sources', side_effect=lookup), \
                         patch.object(fetch_icons, 'read', side_effect=assets.__getitem__), \
                         patch.object(sys, 'argv', ['fetch_icons.py', directory, key]), redirect_stdout(io.StringIO()):
                        with self.assertRaises(SystemExit) as exited:
                            fetch_icons.main()
                        self.assertEqual(exited.exception.code, 0)
                manifest = json.loads((icons / 'manifest.json').read_text())
                self.assertEqual(manifest['mark']['dark_file'], 'mark.dark.svg')
                self.assertEqual((icons / 'mark_dark.svg').read_bytes(), assets['mark_dark-light'])
                spec = self.spec()
                spec['icons'] = ['mark', 'mark_dark']
                spec['nodes'][0]['icon'], spec['nodes'][1]['icon'] = 'mark', 'mark_dark'
                spec['groups'] = [{'id': 'g', 'label': 'Group', 'nodes': ['a', 'b'], 'icon': 'mark'}]
                document = self.html(spec, icons)
                for key in ('mark-light', 'mark-dark', 'mark_dark-light'):
                    self.assertIn(base64.b64encode(assets[key]).decode(), document)

    def test_duplicate_edge_rejected(self):
        spec = self.spec()
        spec['edges'].append(dict(spec['edges'][0], label='reply'))
        with self.assertRaisesRegex(compiler.DiagramError, 'duplicate a->b; merge labels'):
            compiler.compute_layout(spec)

    def test_cjk_width_and_bidirectional_tracks(self):
        ascii_spec = self.spec()
        cjk_spec = copy.deepcopy(ascii_spec)
        cjk_spec['edges'][0]['label'] = '한글요청'
        self.assertGreater(compiler.compute_layout(cjk_spec)[3][0]['lw'], compiler.compute_layout(ascii_spec)[3][0]['lw'])
        for row, col in [(0, 1), (1, 0), (1, 1)]:
            spec = self.spec(row, col)
            spec['edges'].append({'from': 'b', 'to': 'a', 'label': 'reply'})
            layout = compiler.compute_layout(spec)
            self.assertNotEqual(layout[3][0]['path'], layout[3][1]['path'])
            self.assertEqual(compiler.collect_conflicts(*layout[:4]), [])

    def test_recovery_edges_do_not_cross(self):
        spec = json.loads((ROOT / 'examples/04-engineering-flow.json').read_text())
        edges = compiler.compute_layout(spec)[3]
        failed, replay = [e for e in edges if e['label'] in ('failed ×3', 'replay same key')]
        for a, b in compiler.edge_segments(failed['path']):
            for c, d in compiler.edge_segments(replay['path']):
                self.assertFalse(max(min(a[0], b[0]), min(c[0], d[0])) <= min(max(a[0], b[0]), max(c[0], d[0]))
                                 and max(min(a[1], b[1]), min(c[1], d[1])) <= min(max(a[1], b[1]), max(c[1], d[1])))

    def test_html_accessibility_determinism_and_escaping(self):
        spec = self.spec()
        spec['nodes'][0]['name'] = '<A>'
        spec['mode'] = 'flow'
        spec['nodes'][0].update(status='warn', step=0)
        document = self.html(spec)
        self.assertEqual(document, self.html(spec))
        self.assertIn('<figure aria-label=', document)
        self.assertIn('<ul class="sr-only">', document)
        self.assertIn('&lt;A&gt;', document)
        self.assertIn('aria-label="warning"', document)
        self.assertNotIn('aria-pressed', document)
        self.assertNotIn('<p class="lede"></p>', document)
        self.assertNotIn('icons: none', document)
        self.assertLess(document.index("localStorage.getItem"), document.index('</head>'))

    def test_icon_cache_refresh_and_empty_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            icons = pathlib.Path(directory) / 'icons'
            compiler.ensure_icons({}, icons, ROOT)
            self.assertFalse(icons.exists())
            icons.mkdir()
            (icons / 'manifest.json').write_text(json.dumps({'go': {'spec': 'go:old', 'file': 'go.svg'}}))
            with patch.object(compiler.subprocess, 'run') as run:
                compiler.ensure_icons({'icons': ['go:go']}, icons, ROOT)
                self.assertIn('go:go', run.call_args.args[0])

    def test_templates_metadata(self):
        refs = compiler.template_reference()
        self.assertEqual([r['template'] for r in refs], ['infra', 'layers', 'sharded', 'flow', 'hybrid'])
        self.assertTrue(all('pattern' not in r for r in refs))
        self.assertLess(len(json.dumps(refs)), 3000)

    def test_installer_preserves_unmanaged_paths(self):
        repo = ROOT.parents[1]
        with tempfile.TemporaryDirectory(prefix='.diagram-install-', dir=repo) as directory:
            home = pathlib.Path(directory)
            preserved = {
                '.local/bin/diagram': 'custom CLI',
                '.claude/CLAUDE.md': 'custom rules',
                '.codex/skills/diagram': 'custom skill file',
                '.gemini/config/skills/aux-test': 'custom auxiliary skill',
            }
            for relative, content in preserved.items():
                path = home / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            skill_directory = home / '.claude/skills/diagram'
            skill_directory.mkdir(parents=True)
            (skill_directory / 'owned').write_text('keep directory')
            aux = home / '.agents/skills/aux-test'
            aux.mkdir(parents=True)
            (aux / 'SKILL.md').write_text('auxiliary fixture')
            result = subprocess.run(['bash', str(repo / 'scripts/install.sh')],
                                    env=dict(os.environ, HOME=str(home)), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for relative, content in preserved.items():
                path = home / relative
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.read_text(), content)
            self.assertEqual((skill_directory / 'owned').read_text(), 'keep directory')
            self.assertTrue((home / '.agents/skills/diagram').is_symlink())


if __name__ == '__main__':
    unittest.main()
