#!/usr/bin/env python3
"""Deterministic JSON-to-HTML engineering blueprint compiler for diagram.

Supports:
1. Dynamic Row & Column spacing accounting for nested group border thicknesses.
2. Bottom-up group bounding boxes + AABB overlap solver (pushes apart disjoint sibling groups,
   while allowing intentional cross-cutting/overlapping groups that share nodes or set allow_overlap=true).
3. Stacked multi-instance / sharded nodes (`replicas: N` renders 3D stacked cards behind the tile + badge).
4. Orthogonal SVG routing and static group/label collision verification.
"""
import argparse, base64, difflib, heapq, html as html_lib, importlib.util, json, math, os, pathlib, re, subprocess, sys, tempfile, unicodedata


def text_display_units(text: str) -> float:
    return sum(1.75 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1.0 for ch in text)


def icon_specs(spec):
    icons = spec.get('icons', {})
    return {k: (f'{k}={v}' if v.startswith(('https://', 'http://', 'data:')) else f'{k}:{v.removeprefix("svgl:")}') for k, v in icons.items()} if isinstance(icons, dict) else {s.split('=', 1)[0].split(':', 1)[0]: s for s in icons}


def ensure_icons(spec, icons_dir, skill_dir):
    mpath = icons_dir / 'manifest.json'
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    missing = []
    for key, raw in icon_specs(spec).items():
        entry = manifest.get(key, {})
        if (entry.get('spec') != raw or not entry.get('file')
                or any(not (icons_dir / entry[field]).is_file() for field in ('file', 'dark_file') if entry.get(field))):
            missing.append(raw)
    if missing:
        subprocess.run([sys.executable, str(skill_dir / 'scripts' / 'fetch_icons.py'), str(icons_dir), *missing], check=True)

MIME = {"svg": "image/svg+xml", "png": "image/png", "webp": "image/webp", "jpg": "image/jpeg", "jpeg": "image/jpeg"}

# Geometry constants
NODE_W = 132
NODE_WIDE_W = 152
TILE_SIZE = 60
TILE_HALF = 30
NODE_BOX_H = 100
BASE_COL_PITCH = 200
LEFT_MARGIN = 110
TOP_MARGIN = 60

GROUP_INNER_PAD_X = 32
MIN_NODE_GAP_X = 64
CANVAS_MARGIN_X = 36
LEAF_PAD_TOP = 52
LEAF_PAD_BOTTOM = 118

NEST_PAD_X = 28
NEST_PAD_TOP = 48
NEST_PAD_BOTTOM = 24
SIBLING_GROUP_GAP = 28


def b64_file(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def data_uri(path: pathlib.Path) -> str:
    ext = path.suffix.lstrip(".").lower()
    return f"data:{MIME[ext]};base64,{b64_file(path)}"


class DiagramError(ValueError):
    """An actionable input or geometry error."""


ROOT_FIELDS = set('mode title kicker lede lang icons nodes groups edges legend_labels'.split())
NODE_FIELDS = set('id row col name kind icon'.split())
TILE_FIELDS = set('role wide replicas badge tile'.split())
CARD_FIELDS = set('step detail status'.split())
GROUP_FIELDS = set('id label icon nodes children style allow_overlap pad_offset label_pos'.split())
EDGE_FIELDS = set('from to label type'.split())
LINE_TYPES = ('primary', 'internal', 'dashed')
STATUSES = ('warn', 'danger', 'success')


def unknown_fields(obj, allowed, path):
    if not isinstance(obj, dict):
        raise DiagramError(f'{path}: expected object')
    for key in obj.keys() - allowed:
        suggestion = difflib.get_close_matches(key, sorted(allowed), n=1)
        hint = f'; did you mean {suggestion[0]}?' if suggestion else ''
        raise DiagramError(f'{path}.{key}: unknown field{hint}')


def text_value(value, path, nonempty=False):
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise DiagramError(f'{path}: expected {"nonempty " if nonempty else ""}string')
    if len(value) > 512 or any(ord(c) < 32 for c in value):
        raise DiagramError(f'{path}: text exceeds 512 characters or contains control characters')
    return value


def encoding_counts(spec):
    counts = {k: sum(e.get('type', 'primary') == k for e in spec.get('edges', [])) for k in LINE_TYPES}
    counts.update({k: sum(n.get('kind', 'card' if spec.get('mode') == 'flow' else 'tile') == 'card'
                         and n.get('status', 'primary') == k for n in spec['nodes']) for k in STATUSES})
    return counts


def spec_warnings(spec):
    warnings = []
    edges = spec.get('edges', [])
    missing = sum(not e.get('label') for e in edges)
    if edges and missing / len(edges) > .25:
        warnings.append(f'{missing}/{len(edges)} edges have no label; state the verb, port or failure rule')
    counts = encoding_counts(spec)
    labels = spec.get('legend_labels', {})
    for key in labels:
        if counts[key] == 1:
            warnings.append(f'legend_labels.{key}: used once; label it directly')
    active = sum(counts[k] > 0 for k in LINE_TYPES)
    if active >= 2 and not labels:
        warnings.append(f'edges use {active} line styles but legend_labels is missing')
    for i, n in enumerate(spec['nodes']):
        if n.get('kind', 'card' if spec.get('mode') == 'flow' else 'tile') == 'card':
            for field, cap in (('name', 20), ('detail', 26)):
                if text_display_units(n.get(field, '')) > cap:
                    warnings.append(f'nodes[{i}].{field}: exceeds {cap} display units; card text may truncate')
    return warnings


def validate_spec(spec):
    unknown_fields(spec, ROOT_FIELDS, 'root')
    if spec.get('mode', 'stack') not in ('stack', 'flow'):
        raise DiagramError('mode: expected stack or flow')
    for key in ('title', 'kicker', 'lede', 'lang'):
        if key in spec:
            text_value(spec[key], key)
    if not re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*', spec.get('lang', 'en')):
        raise DiagramError('lang: expected BCP47 language tag')
    for key, limit in (('nodes', 200), ('groups', 100), ('edges', 400)):
        value = spec.get(key, [])
        if not isinstance(value, list) or len(value) > limit or (key == 'nodes' and not value):
            raise DiagramError(f'{key}: expected {"nonempty " if key == "nodes" else ""}array, maximum {limit}')
    icons = spec.get('icons', {})
    if not isinstance(icons, (list, dict)):
        raise DiagramError('icons: expected array or object')
    if isinstance(icons, dict):
        for k, v in icons.items():
            text_value(k, 'icons key', True)
            text_value(v, f'icons.{k}', True)
    else:
        for i, v in enumerate(icons):
            text_value(v, f'icons[{i}]', True)
        keys = [v.split('=', 1)[0].split(':', 1)[0] for v in icons]
        if len(set(keys)) != len(keys):
            raise DiagramError('icons: duplicate key')
    keys = set(icon_specs(spec))
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+', key) for key in keys):
        raise DiagramError('icons: invalid icon key')
    ids, cells = set(), set()
    for i, n in enumerate(spec['nodes']):
        path = f'nodes[{i}]'
        if not isinstance(n, dict):
            raise DiagramError(f'{path}: expected object')
        kind = n.get('kind', 'card' if spec.get('mode') == 'flow' else 'tile')
        if kind not in ('tile', 'card'):
            raise DiagramError(f'{path}.kind: expected tile or card')
        unknown_fields(n, NODE_FIELDS | (TILE_FIELDS if kind == 'tile' else CARD_FIELDS), path)
        for key in ('id', 'name', 'row', 'col'):
            if key not in n:
                raise DiagramError(f'{path}.{key}: required')
        for key in ('id', 'name'):
            text_value(n[key], f'{path}.{key}', True)
        if n['id'] in ids:
            raise DiagramError(f'{path}.id: duplicate ID')
        ids.add(n['id'])
        if type(n['row']) is not int or type(n['col']) is not int:
            raise DiagramError(f'{path}: row and col must be integers')
        cell = n['row'], n['col']
        if cell in cells:
            raise DiagramError(f'{path}: one node per grid cell required')
        cells.add(cell)
        for key in ('role', 'detail', 'badge', 'icon'):
            if key in n:
                text_value(n[key], f'{path}.{key}')
        if 'icon' in n and n['icon'] not in keys:
            raise DiagramError(f'{path}.icon: undeclared icon')
        if kind == 'tile':
            if type(n.get('wide', False)) is not bool:
                raise DiagramError(f'{path}.wide: expected boolean')
            if type(n.get('replicas', 1)) is not int or n.get('replicas', 1) < 1:
                raise DiagramError(f'{path}.replicas: expected positive integer')
            if 'tile' in n and n['tile'] not in ('dark', 'bare'):
                raise DiagramError(f'{path}.tile: expected dark or bare')
            for key, cap in (('name', 36), ('role', 42)):
                if text_display_units(n.get(key, '')) > cap:
                    raise DiagramError(f'{path}.{key}: exceeds {cap} display units')
        else:
            if n.get('status', 'primary') not in ('primary', *STATUSES):
                raise DiagramError(f'{path}.status: invalid card status')
            if 'step' in n:
                v = n['step']
                if not isinstance(v, str) and not (type(v) in (int, float) and math.isfinite(v)):
                    raise DiagramError(f'{path}.step: expected string or finite number')
                text_value(str(v), f'{path}.step')
    gs = {}
    for i, g in enumerate(spec.get('groups', [])):
        path = f'groups[{i}]'
        unknown_fields(g, GROUP_FIELDS, path)
        for key in ('id', 'label'):
            text_value(g.get(key), f'{path}.{key}', True)
        if g['id'] in gs:
            raise DiagramError(f'{path}.id: duplicate ID')
        gs[g['id']] = g
        if g.get('style', 'ga') not in ('ga', 'ga-nested', 'gb', 'gp', 'aws', 'aws vpc', 'aws private', 'aws public'):
            raise DiagramError(f'{path}.style: invalid group style')
        if type(g.get('allow_overlap', False)) is not bool:
            raise DiagramError(f'{path}.allow_overlap: expected boolean')
        pad = g.get('pad_offset', 0)
        if type(pad) not in (int, float) or not math.isfinite(pad) or not -24 <= pad <= 80:
            raise DiagramError(f'{path}.pad_offset: expected finite number in [-24, 80]')
        if 'label_pos' in g and g['label_pos'] not in ('top-left', 'top-right'):
            raise DiagramError(f'{path}.label_pos: expected top-left or top-right')
        if 'icon' in g:
            text_value(g['icon'], f'{path}.icon', True)
            if g['icon'] not in keys:
                raise DiagramError(f'{path}.icon: undeclared icon')
        for key in ('nodes', 'children'):
            val = g.get(key, [])
            if not isinstance(val, list) or any(not isinstance(x, str) for x in val) or len(set(val)) != len(val):
                raise DiagramError(f'{path}.{key}: expected unique string array')
        if not g.get('nodes') and not g.get('children'):
            raise DiagramError(f'{path}: empty group')
        if not set(g.get('nodes', [])) <= ids:
            raise DiagramError(f'{path}.nodes: unknown node')
    visited, active, parents = set(), set(), {}
    def visit(gid, depth=0):
        if gid not in gs or gid in active or depth > 32:
            raise DiagramError(f'groups: cyclic, unknown or too deeply nested group {gid}')
        if gid in visited:
            return
        active.add(gid)
        for child in gs[gid].get('children', []):
            if child in parents and parents[child] != gid:
                raise DiagramError(f'groups: multiple parents for {child}')
            parents[child] = gid
            visit(child, depth + 1)
        active.remove(gid)
        visited.add(gid)
    for gid in gs:
        visit(gid)
    pairs = set()
    for i, e in enumerate(spec.get('edges', [])):
        path = f'edges[{i}]'
        unknown_fields(e, EDGE_FIELDS, path)
        for key in ('from', 'to'):
            text_value(e.get(key), f'{path}.{key}', True)
        if e['from'] not in ids or e['to'] not in ids or e['from'] == e['to']:
            raise DiagramError(f'{path}: edges need distinct existing endpoints')
        pair = e['from'], e['to']
        if pair in pairs:
            raise DiagramError(f'{path}: duplicate {pair[0]}->{pair[1]}; merge labels')
        pairs.add(pair)
        if e.get('type', 'primary') not in LINE_TYPES:
            raise DiagramError(f'{path}.type: invalid edge type')
        text_value(e.get('label', ''), f'{path}.label')
        if text_display_units(e.get('label', '')) > 32:
            raise DiagramError(f'{path}.label: exceeds 32 display units')
    labels = spec.get('legend_labels', {})
    unknown_fields(labels, set(LINE_TYPES + STATUSES), 'legend_labels')
    counts = encoding_counts(spec)
    for key, label in labels.items():
        text_value(label, f'legend_labels.{key}', True)
        if not counts[key]:
            raise DiagramError(f'legend_labels.{key}: no encoding uses it')


def segment_hits_node(a, b, node):
    # Tile side routes intentionally pass above the label area.
    left, right = node['left'], node['right']
    top, bottom = node['top'], node['bottom']
    if node['kind'] == 'tile' and max(a[1], b[1]) <= top + TILE_SIZE:
        left = node['cx'] - TILE_HALF
        right = node['cx'] + TILE_HALF + (8 if node.get('replicas', 1) > 1 else 0)
    if a[0] == b[0]:
        return left < a[0] < right and max(min(a[1], b[1]), top) < min(max(a[1], b[1]), bottom)
    return top < a[1] < bottom and max(min(a[0], b[0]), left) < min(max(a[0], b[0]), right)


def route_around_nodes(start, end, nodes):
    """Shortest deterministic rectilinear path on node-boundary visibility grid."""
    xs = sorted({start[0], end[0]} | {n[k] + d for n in nodes for k, d in [('left', -12), ('right', 12)]})
    ys = sorted({start[1], end[1]} | {n[k] + d for n in nodes for k, d in [('top', -12), ('bottom', 12)]})
    queue, costs, previous = [(0, start)], {start: 0}, {}
    while queue:
        cost, point = heapq.heappop(queue)
        if cost != costs[point]:
            continue
        if point == end:
            result = [end]
            while result[-1] != start:
                result.append(previous[result[-1]])
            return list(reversed(result))
        ix, iy = xs.index(point[0]), ys.index(point[1])
        neighbors = [(xs[j], point[1]) for j in (ix-1, ix+1) if 0 <= j < len(xs)]
        neighbors += [(point[0], ys[j]) for j in (iy-1, iy+1) if 0 <= j < len(ys)]
        for nxt in neighbors:
            if any(segment_hits_node(point, nxt, n) for n in nodes):
                continue
            new_cost = cost + abs(point[0]-nxt[0]) + abs(point[1]-nxt[1])
            if new_cost < costs.get(nxt, float('inf')):
                costs[nxt], previous[nxt] = new_cost, point
                heapq.heappush(queue, (new_cost, nxt))
    raise DiagramError('No collision-free orthogonal path between node ports')


def compute_layout(spec: dict):
    validate_spec(spec)
    col_extra, row_extra = {}, {}
    pos = {n['id']: n for n in spec['nodes']}
    last = None
    for attempt in range(6):
        try:
            result = _compute_layout(spec, col_extra, row_extra, strict=attempt < 3)
            return result
        except LabelPlacementError as ex:
            last = ex
            if not ex.edges:
                raise
            for e in ex.edges:
                u, v = pos[e['from']], pos[e['to']]
                for c in sorted({n['col'] for n in spec['nodes']}):
                    if min(u['col'], v['col']) < c <= max(u['col'], v['col']):
                        col_extra[c] = col_extra.get(c, 0) + 32
                for r in sorted({n['row'] for n in spec['nodes']}):
                    if min(u['row'], v['row']) < r <= max(u['row'], v['row']):
                        row_extra[r] = row_extra.get(r, 0) + 24
    raise last


def _compute_layout(spec: dict, col_extra, row_extra, strict=False):
    nodes ={n["id"]: dict(n) for n in spec["nodes"]}
    groups = {g["id"]: dict(g) for g in spec.get("groups", [])}
    edges = [dict(e) for e in spec.get("edges", [])]

    parent_of = {}
    for gid, g in groups.items():
        for child_id in g.get("children", []):
            parent_of[child_id] = gid

    def group_ancestors(gid):
        chain, cur = [], gid
        while cur:
            chain.append(cur)
            cur = parent_of.get(cur)
        return chain

    # Collect all transitive nodes belonging to each group
    group_all_nodes = {}

    def collect_nodes(gid):
        if gid in group_all_nodes:
            return group_all_nodes[gid]
        g = groups[gid]
        nset = {nid for nid in g.get("nodes", []) if nid in nodes}
        for cid in g.get("children", []):
            nset |= collect_nodes(cid)
        group_all_nodes[gid] = nset
        return nset

    for gid in groups:
        collect_nodes(gid)

    def can_overlap(g1, g2):
        # Ancestor-descendant groups naturally overlap
        if g1 in group_ancestors(g2) or g2 in group_ancestors(g1):
            return True
        # Cross-cutting groups that intentionally share nodes (or set allow_overlap) are allowed to intersect!
        if groups[g1].get("allow_overlap") or groups[g2].get("allow_overlap"):
            return True
        if group_all_nodes[g1] & group_all_nodes[g2]:
            return True
        return False

    rows = sorted({n["row"] for n in nodes.values()})
    cols = sorted({n["col"] for n in nodes.values()})

    group_rows = {gid: {nodes[nid]["row"] for nid in nset} for gid, nset in group_all_nodes.items() if nset}
    group_cols = {gid: {nodes[nid]["col"] for nid in nset} for gid, nset in group_all_nodes.items() if nset}

    group_min_row = {gid: min(rset) for gid, rset in group_rows.items() if rset}
    group_max_row = {gid: max(rset) for gid, rset in group_rows.items() if rset}
    group_min_col = {gid: min(cset) for gid, cset in group_cols.items() if cset}
    group_max_col = {gid: max(cset) for gid, cset in group_cols.items() if cset}

    def node_width(n):
        kind = n.get("kind", "card" if spec.get("mode") == "flow" else "tile")
        return 176 if kind == "card" else (NODE_WIDE_W if n.get("wide") else NODE_W)

    col_half_width = {c: max(node_width(n) // 2 for n in nodes.values() if n["col"] == c) for c in cols}

    # 1. Dynamic Column X coordinates
    col_x = {}
    for idx, c in enumerate(cols):
        if idx == 0:
            starting = [gid for gid, mc in group_min_col.items() if mc == c]
            max_anc = max((len(group_ancestors(gid)) for gid in starting), default=0)
            col_x[c] = LEFT_MARGIN + (max(0, max_anc - 1) * NEST_PAD_X)
        else:
            c_prev = cols[idx - 1]
            closing_right = [gid for gid, mc in group_max_col.items() if mc == c_prev]
            max_right_depth = 0
            for gid in closing_right:
                anc = [a for a in group_ancestors(gid) if group_max_col.get(a) == c_prev]
                max_right_depth = max(max_right_depth, len(anc))
            right_extent = col_half_width[c_prev] + (GROUP_INNER_PAD_X + max(0, max_right_depth - 1) * NEST_PAD_X if max_right_depth > 0 else 0)

            opening_left = [gid for gid, mc in group_min_col.items() if mc == c]
            max_left_depth = 0
            for gid in opening_left:
                anc = [a for a in group_ancestors(gid) if group_min_col.get(a) == c]
                max_left_depth = max(max_left_depth, len(anc))
            left_extent = col_half_width[c] + (GROUP_INNER_PAD_X + max(0, max_left_depth - 1) * NEST_PAD_X if max_left_depth > 0 else 0)

            labels = [str(e.get("label", "")) for e in edges
                      if {nodes[e["from"]]["col"], nodes[e["to"]]["col"]} == {c_prev, c}]
            clear_gap = max([MIN_NODE_GAP_X] + [int(text_display_units(label) * 7) + 28 for label in labels if label])
            node_pitch = col_half_width[c_prev] + col_half_width[c] + clear_gap + col_extra.get(c, 0)

            if max_right_depth > 0 or max_left_depth > 0:
                pitch = max(BASE_COL_PITCH, node_pitch, right_extent + left_extent + SIBLING_GROUP_GAP)
            else:
                pitch = max(BASE_COL_PITCH, node_pitch)
            col_x[c] = col_x[c_prev] + pitch

    # 2. Dynamic Row Y coordinates
    row_y = {}
    for idx, r in enumerate(rows):
        if idx == 0:
            starting = [gid for gid, mr in group_min_row.items() if mr == r]
            max_anc = max((len(group_ancestors(gid)) for gid in starting), default=0)
            row_y[r] = TOP_MARGIN + (LEAF_PAD_TOP + (max_anc - 1) * NEST_PAD_TOP if max_anc > 0 else 0)
        else:
            r_prev = rows[idx - 1]
            ending = [gid for gid, mr in group_max_row.items() if mr == r_prev]
            max_end_depth = 0
            for gid in ending:
                anc = [a for a in group_ancestors(gid) if group_max_row.get(a) == r_prev]
                max_end_depth = max(max_end_depth, len(anc))
            bottom_extent = LEAF_PAD_BOTTOM + max(0, max_end_depth - 1) * NEST_PAD_BOTTOM if max_end_depth > 0 else NODE_BOX_H + 16

            starting = [gid for gid, mr in group_min_row.items() if mr == r]
            max_start_depth = 0
            for gid in starting:
                anc = [a for a in group_ancestors(gid) if group_min_row.get(a) == r]
                max_start_depth = max(max_start_depth, len(anc))
            top_extent = LEAF_PAD_TOP + max(0, max_start_depth - 1) * NEST_PAD_TOP if max_start_depth > 0 else 16

            elbow_edges = [
                e for e in edges
                if nodes[e["from"]]["col"] != nodes[e["to"]]["col"]
                and min(nodes[e["from"]]["row"], nodes[e["to"]]["row"]) <= r_prev
                and max(nodes[e["from"]]["row"], nodes[e["to"]]["row"]) >= r
                and (
                    (nodes[e["to"]]["row"] == r and nodes[e["from"]]["row"] < r)
                    or (nodes[e["from"]]["row"] == r and nodes[e["to"]]["row"] < r)
                )
            ]
            corridor_h = max(48, 32 + 24 * max(1, len(elbow_edges))) + row_extra.get(r, 0)
            row_y[r] = row_y[r_prev] + bottom_extent + corridor_h + top_extent

    def build_boxes():
        for nid, n in nodes.items():
            n["cx"] = col_x[n["col"]]
            n["topY"] = row_y[n["row"]]
            n["kind"] = n.get("kind", "card" if spec.get("mode") == "flow" else "tile")
            w = node_width(n)
            n["height"] = 84 if n["kind"] == "card" else NODE_BOX_H
            n["half"] = w // 2 if n["kind"] == "card" else TILE_HALF
            n["mid"] = n["height"] // 2 if n["kind"] == "card" else TILE_HALF
            n["width"] = w
            n["left"] = n["cx"] - w // 2
            n["right"] = n["left"] + w
            n["top"] = n["topY"]
            n["bottom"] = n["topY"] + n["height"]

        # Mixed tile/card rows share one center line, so horizontal edges never kink.
        for r in rows:
            row_nodes = [n for n in nodes.values() if n["row"] == r]
            center = max(n["mid"] for n in row_nodes)
            for n in row_nodes:
                shift = center - n["mid"]
                n["topY"] += shift
                n["top"] += shift
                n["bottom"] += shift

        gboxes = {}

        def compute_group_box(gid):
            if gid in gboxes:
                return gboxes[gid]
            g = groups[gid]
            member_nodes = [nodes[nid] for nid in g.get("nodes", []) if nid in nodes]
            child_boxes = [compute_group_box(cid) for cid in g.get("children", []) if cid in groups]

            # Cross-cutting overlay groups gets slightly inset/offset padding so borders don't collinearly hide each other
            pad_offset = g.get("pad_offset", 0)
            lefts, rights, tops, bottoms = [], [], [], []
            for mn in member_nodes:
                inner_pad = max(14, GROUP_INNER_PAD_X + pad_offset)
                lefts.append(mn["left"] - inner_pad)
                rights.append(mn["right"] + inner_pad)
                tops.append(mn["topY"] - max(24, LEAF_PAD_TOP + pad_offset))
                bottoms.append(mn["bottom"] + max(14, LEAF_PAD_BOTTOM - NODE_BOX_H + pad_offset))
            for cb in child_boxes:
                lefts.append(cb["left"] - NEST_PAD_X)
                rights.append(cb["right"] + NEST_PAD_X)
                tops.append(cb["top"] - NEST_PAD_TOP)
                bottoms.append(cb["bottom"] + NEST_PAD_BOTTOM)

            box = {
                "id": gid,
                "left": min(lefts),
                "top": min(tops),
                "right": max(rights),
                "bottom": max(bottoms),
                "width": max(rights) - min(lefts),
                "height": max(bottoms) - min(tops),
                "depth": len(group_ancestors(gid)),
            }
            gboxes[gid] = box
            return box

        for gid in groups:
            compute_group_box(gid)
        return gboxes

    group_boxes = build_boxes()

    # 3. Iterative AABB collision resolution for disjoint groups (skipping intentionally overlapping groups)
    for _ in range(10):
        pushed = False
        gids = list(groups.keys())
        for i in range(len(gids)):
            for j in range(i + 1, len(gids)):
                g1, g2 = gids[i], gids[j]
                if can_overlap(g1, g2):
                    continue
                b1, b2 = group_boxes[g1], group_boxes[g2]
                v_overlap = not (b1["bottom"] + SIBLING_GROUP_GAP <= b2["top"] or b2["bottom"] + SIBLING_GROUP_GAP <= b1["top"])
                h_overlap = not (b1["right"] + SIBLING_GROUP_GAP <= b2["left"] or b2["right"] + SIBLING_GROUP_GAP <= b1["left"])
                if v_overlap and h_overlap:
                    if group_max_col[g1] < group_min_col[g2]:
                        delta = (b1["right"] + SIBLING_GROUP_GAP) - b2["left"]
                        if delta > 0:
                            for c in cols:
                                if c >= group_min_col[g2]:
                                    col_x[c] += delta
                            pushed = True
                    elif group_max_col[g2] < group_min_col[g1]:
                        delta = (b2["right"] + SIBLING_GROUP_GAP) - b1["left"]
                        if delta > 0:
                            for c in cols:
                                if c >= group_min_col[g1]:
                                    col_x[c] += delta
                            pushed = True
                    elif group_max_row[g1] < group_min_row[g2]:
                        delta = (b1["bottom"] + SIBLING_GROUP_GAP) - b2["top"]
                        if delta > 0:
                            for r in rows:
                                if r >= group_min_row[g2]:
                                    row_y[r] += delta
                            pushed = True
                    elif group_max_row[g2] < group_min_row[g1]:
                        delta = (b2["bottom"] + SIBLING_GROUP_GAP) - b1["top"]
                        if delta > 0:
                            for r in rows:
                                if r >= group_min_row[g1]:
                                    row_y[r] += delta
                            pushed = True
        if not pushed:
            break
        group_boxes = build_boxes()


    min_x = min([b["left"] for b in group_boxes.values()] + [n["left"] for n in nodes.values()])
    min_y = min([b["top"] for b in group_boxes.values()] + [n["topY"] for n in nodes.values()])
    dx = max(0, CANVAS_MARGIN_X - min_x)
    dy = max(0, 24 - min_y)
    if dx or dy:
        for c in cols:
            col_x[c] += dx
        for r in rows:
            row_y[r] += dy
        group_boxes = build_boxes()

    corridors = {}
    for idx in range(1, len(rows)):
        r_prev, r_curr = rows[idx - 1], rows[idx]
        y_prev = row_y[r_prev]
        y_curr = row_y[r_curr]
        ending_bottoms = [
            group_boxes[gid]["bottom"]
            for gid, mr in group_max_row.items()
            if mr == r_prev and not groups[gid].get("allow_overlap")
        ]
        c_top = max(ending_bottoms + [y_prev + NODE_BOX_H + 8])
        starting_tops = [
            group_boxes[gid]["top"]
            for gid, mr in group_min_row.items()
            if mr == r_curr and not groups[gid].get("allow_overlap")
        ]
        c_bottom = min(starting_tops + [y_curr - 8])
        if c_bottom <= c_top + 16:
            c_top = y_prev + NODE_BOX_H + 12
            c_bottom = y_curr - 12
        corridors[(r_prev, r_curr)] = (c_top, c_bottom)

    routed_edges = []
    corridor_usage = {}
    channel_usage = {}

    def is_channel(ed):
        a, b = nodes[ed['from']], nodes[ed['to']]
        return a['col'] == b['col'] and abs(a['row'] - b['row']) > 1 and any(
            n['col'] == a['col'] and min(a['row'], b['row']) < n['row'] < max(a['row'], b['row']) for n in nodes.values())

    # Same source port + different line style => split the shared stem so dashes stay visible.
    port_styles = {}
    for ed in edges:
        a, b = nodes[ed['from']], nodes[ed['to']]
        if a['row'] != b['row'] and not is_channel(ed):
            port_styles.setdefault((a['id'], b['row'] > a['row']), set()).add(ed.get('type', 'primary'))

    for e in edges:
        u = nodes[e["from"]]
        v = nodes[e["to"]]
        pair_offset = (10 if u['id'] < v['id'] else -10) if any(other['from'] == e['to'] and other['to'] == e['from'] for other in edges) else 0
        style = e.get("type", "primary")
        styles = sorted(port_styles.get((u['id'], v['row'] > u['row']), {style}))
        port = (styles.index(style) - (len(styles) - 1) / 2) * 14 if u['row'] != v['row'] else 0
        cls = "e" if style == "primary" else ("n dash" if style == "dashed" else "n")
        label_cls = "el a" if style == "primary" else "el"
        label = e.get("label", "")

        # Extra right clearance if a node has stacked replica cards
        u_rep_pad = 8 if int(u.get("replicas", 1)) > 1 else 0
        v_rep_pad = 8 if int(v.get("replicas", 1)) > 1 else 0

        if u["row"] == v["row"]:
            y = u["topY"] + u["mid"] + pair_offset
            if u["cx"] < v["cx"]:
                x1, x2 = u["cx"] + u["half"] + 6 + u_rep_pad, v["cx"] - v["half"] - 6
            else:
                x1, x2 = u["cx"] - u["half"] - 6, v["cx"] + v["half"] + 6 + v_rep_pad
            path_d = f"M{x1} {y} H{x2}"
            lx, ly, anchor = (x1 + x2) // 2, y - 8, "middle"
            if abs(u['col'] - v['col']) > 1 and any(
                n['row'] == u['row'] and min(u['col'], v['col']) < n['col'] < max(u['col'], v['col'])
                for n in nodes.values()
            ):
                candidates = [(a + b) // 2 for key, (a, b) in corridors.items() if u['row'] in key]
                candidates += [max(12, min(n['topY'] for n in nodes.values()) - 24),
                               max(n['bottom'] for n in nodes.values()) + 24]
                hy = min(candidates, key=lambda cy: abs(cy - y))
                below = hy > y
                y1 = u['bottom'] + 6 if below else u['topY'] - 12
                y2 = v['bottom'] + 6 if below else v['topY'] - 12
                path_d = f"M{u['cx']} {y1} V{hy} H{v['cx']} V{y2}"
                lx, ly = (u['cx'] + v['cx']) // 2, hy - 8

        elif u["col"] == v["col"]:
            x = u["cx"] + pair_offset + port
            if u["topY"] < v["topY"]:
                y1, y2 = u["bottom"] + 6, v["topY"] - 6
            else:
                y1, y2 = u["topY"] - 6, v["bottom"] + 6
            path_d = f"M{x} {y1} V{y2}"
            lx, ly, anchor = x + 10, (y1 + y2) // 2 + 4, "start"
            if pair_offset < 0:
                lx, anchor = x - 10, 'end'
            if abs(u['row'] - v['row']) > 1 and any(
                n['col'] == u['col'] and min(u['row'], v['row']) < n['row'] < max(u['row'], v['row'])
                for n in nodes.values()
            ):
                channel_x = max(n['right'] for n in nodes.values() if n['col'] == u['col']) + 16 + 14 * channel_usage.get(u['col'], 0)
                channel_usage[u['col']] = channel_usage.get(u['col'], 0) + 1
                side_u, side_v = u['cx'] + u['half'] + 6 + u_rep_pad, v['cx'] + v['half'] + 6 + v_rep_pad
                path_d = f"M{side_u} {u['topY'] + u['mid']} H{channel_x} V{v['topY'] + v['mid']} H{side_v}"
                lx = channel_x + 10

        else:
            r_high = max(u["row"], v["row"])
            r_idx = rows.index(r_high)
            corr_key = (rows[r_idx - 1], r_high)
            c_top, c_bottom = corridors[corr_key]

            x_min, x_max = min(u["cx"], v["cx"]), max(u["cx"], v["cx"])
            used_tracks = corridor_usage.setdefault(corr_key, [])
            track_idx = 0
            for prev_xmin, prev_xmax, prev_t in used_tracks:
                if not (x_max < prev_xmin - 10 or x_min > prev_xmax + 10):
                    if u["id"] != prev_t.get("from_id") or style != prev_t.get("style"):
                        track_idx = max(track_idx, prev_t["idx"] + 1)
            used_tracks.append((x_min, x_max, {"idx": track_idx, "from_id": u["id"], "style": style}))

            hy = (c_top + c_bottom) // 2 + (0 if pair_offset else track_idx * 14) + pair_offset
            hy = min(c_bottom - 12, max(c_top + 22, hy))

            if u["topY"] < v["topY"]:
                y1 = u["bottom"] + 6
                y2 = v["topY"] - 6
            else:
                y1 = u["topY"] - 6
                y2 = v["bottom"] + 6
            path_d = f"M{u['cx'] + pair_offset + port} {y1} V{hy} H{v['cx'] + pair_offset} V{y2}"

            lx = (u["cx"] + v["cx"]) // 2
            ly = hy - 8
            anchor = "middle"

        segments = edge_segments(path_d)
        if any(segment_hits_node(a, b, n) for a, b in segments for n in nodes.values()):
            points = route_around_nodes(segments[0][0], segments[-1][1], list(nodes.values()))
            path_d = f'M{points[0][0]} {points[0][1]}'
            for a, b in zip(points, points[1:]):
                path_d += f'H{b[0]}' if a[1] == b[1] else f'V{b[1]}'
            a, b = max(zip(points, points[1:]), key=lambda ab: abs(ab[0][0]-ab[1][0])+abs(ab[0][1]-ab[1][1]))
            lx, ly, anchor = (a[0]+b[0])/2, (a[1]+b[1])/2-8, 'middle'
        routed_edges.append({
            "from": u["id"], "to": v["id"], "cls": cls,
            "path": path_d,
            "label": label,
            "label_cls": label_cls,
            "lx": lx,
            "ly": ly,
            "anchor": anchor,
            "lw": max(44, int(text_display_units(label) * 7.0) + 16),
            "lh": 20,
        })

    place_group_labels(nodes, groups, group_boxes, routed_edges, group_ancestors)
    place_edge_labels(nodes, groups, group_boxes, routed_edges, strict)

    verify_no_collisions(nodes, groups, group_boxes, routed_edges)
    points = [p for e in routed_edges for segment in edge_segments(e['path']) for p in segment]
    canvas_w = max([b["right"] for b in group_boxes.values()] + [n["right"] for n in nodes.values()] + [p[0] for p in points] + [e['lx'] + e['lw'] + 12 for e in routed_edges if e['label']]) + CANVAS_MARGIN_X
    canvas_h = max([b["bottom"] for b in group_boxes.values()] + [n["bottom"] for n in nodes.values()] + [p[1] for p in points] + [e['ly'] + e['lh'] / 2 + 12 for e in routed_edges if e['label']]) + 36

    return nodes, groups, group_boxes, routed_edges, canvas_w, canvas_h


class LabelPlacementError(DiagramError):
    def __init__(self, message, edges=()):
        super().__init__(message)
        self.edges = list(edges)


def overlap(p, q, c=0):
    return p[0] < q[1] + c and q[0] < p[1] + c and p[2] < q[3] + c and q[2] < p[3] + c


def seg_box(a, b):
    return min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])


def group_label_metrics(g):
    style = g.get('style', 'ga')
    big = style in ('aws', 'aws vpc')
    icon = (38 if big else 20) if g.get('icon') else 0
    pad = 8 if big else 12
    width = sum(12.5 if unicodedata.east_asian_width(ch) in ('W', 'F') else 6.5 for ch in g.get('label', g['id'])) + icon + pad
    if big:
        return -1.5, -1.5, 30, width
    if style in ('aws private', 'aws public'):
        return 8, 10, 18, width
    return 10, 12, 18, width


def node_obstacles(n):
    if n['kind'] == 'card':
        return [(n['left'], n['right'], n['top'], n['bottom'])]
    rep = int(n.get('replicas', 1))
    badge = n.get('badge') or (f'×{rep}' if rep > 1 else '')
    extra = 8 if rep > 1 else 0
    right = n['cx'] + 30 + extra
    if badge:
        right = max(right, n['cx'] + 44)
        right = max(right, n['cx'] + 44 + 0)
    boxes = [(n['cx'] - 30, right, n['top'] - 8 if rep > 1 or badge else n['top'], n['top'] + 60)]
    boxes.append((n['left'], n['right'], n['top'] + 60, n['bottom']))
    return boxes


def group_borders(box):
    return [(box['left'], box['right'], box['top'], box['top']),
            (box['left'], box['right'], box['bottom'], box['bottom']),
            (box['left'], box['left'], box['top'], box['bottom']),
            (box['right'], box['right'], box['top'], box['bottom'])]


def label_conflicts(box, nodes, groups, boxes, edges, placed=(), group_label=False):
    """The obstacle predicate shared by candidate placement and final verification."""
    errors = []
    if not group_label and (box[0] < 8 or box[2] < 8):
        errors.append('label outside canvas margin')
    for edge in edges:
        if any(overlap(box, seg_box(a, b), 6 if group_label else 2)
               for a, b in edge_segments(edge['path'])):
            errors.append('label intersects edge')
    if any(overlap(box, ob, 4 if group_label else 3)
           for n in nodes.values() for ob in node_obstacles(n)):
        errors.append('label intersects node')
    if any(overlap(box, g['gl_box'], 6 if group_label else 3)
           for g in groups.values() if 'gl_box' in g):
        errors.append('label intersects group label')
    if not group_label and any(overlap(box, border, 7) for b in boxes.values() for border in group_borders(b)):
        errors.append('label intersects group border')
    if any(overlap(box, other, 4) for other in placed):
        errors.append('edge labels overlap')
    return errors


def place_group_labels(nodes, groups, boxes, edges, ancestors):
    placed, errors = [], []
    segs = [s for e in edges for s in edge_segments(e['path'])]
    for gid in sorted(groups, key=lambda g: -boxes[g]['width'] * boxes[g]['height']):
        g, b = groups[gid], boxes[gid]
        top, left_inset, h, w = group_label_metrics(g)
        y1, y2 = b['top'] + top, b['top'] + top + h
        lo, hi = b['left'] + left_inset, b['right'] - 12 - w
        hard, soft = [], []
        def block(box, c=6, into=None):
            if box[2] < y2 + c and box[3] > y1 - c:
                (hard if into is None else into).append((box[0] - c, box[1] + c))
        for s in segs:
            block(seg_box(*s))
        for n in nodes.values():
            for ob in node_obstacles(n):
                block(ob, 4)
        for other, ob in boxes.items():
            if other == gid or other in ancestors(gid):
                continue
            block((ob['left'], ob['left'], ob['top'], ob['bottom']), 4, soft)
            block((ob['right'], ob['right'], ob['top'], ob['bottom']), 4, soft)
            block((ob['left'], ob['right'], ob['top'], ob['top']), 4, soft)
            block((ob['left'], ob['right'], ob['bottom'], ob['bottom']), 4, soft)
        for pb in placed:
            block(pb, 6)
        def spans(blocked):
            free, cursor = [], lo
            for a, z in sorted(blocked):
                if a - w >= cursor and cursor <= hi:
                    free.append((cursor, min(a - w, hi)))
                cursor = max(cursor, z)
            if cursor <= hi:
                free.append((cursor, hi))
            return free
        free = spans(hard + soft) or spans(hard)
        if not free:
            cursor, widest = lo, 0
            for a, z in sorted(hard):
                widest = max(widest, min(a, hi + w) - cursor)
                cursor = max(cursor, z)
            widest = max(0, widest, hi + w - cursor)
            errors.append(f"group label does not fit: {g.get('label', gid)} (needs {w:.0f}px, widest free {widest:.0f}px)")
            continue
        if g.get('label_pos') == 'top-right':
            x = free[-1][1]
        else:
            x = free[0][0]
        candidate = (x, x + w, y1, y2)
        if label_conflicts(candidate, nodes, groups, boxes, edges, group_label=True):
            raise LabelPlacementError(f"group label does not fit: {g['label']}")
        g['gl_left'] = x - b['left']
        g['gl_box'] = (x, x + w, y1, y2)
        placed.append(g['gl_box'])
    if errors:
        raise LabelPlacementError('\n'.join(errors))


def edge_label_candidates(edge, shared):
    w = edge['lw']
    segs = edge_segments(edge['path'])
    out = []
    n = len(segs)
    for i, (a, b) in enumerate(segs):
        length = abs(a[0] - b[0]) + abs(a[1] - b[1])
        base = 100 * shared[i] + 6 * (n - 1 - i)
        for ti, t in enumerate((0.5, 0.35, 0.65, 0.2, 0.8)):
            px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if a[1] == b[1]:
                if length < 24:
                    continue
                over = 20 * (w > length)
                out.append((base + over + ti * 2, px, py - 8, 'middle'))
                out.append((base + over + ti * 2 + 1, px, py + 20, 'middle'))
            else:
                if length < 16:
                    continue
                out.append((base + ti * 2, a[0] + 10, py + 4, 'start'))
                out.append((base + ti * 2 + 1, a[0] - 10, py + 4, 'end'))
    return sorted(out, key=lambda c: c[0])


def place_edge_labels(nodes, groups, boxes, edges, strict=False):
    all_segs = [(i, s) for i, e in enumerate(edges) for s in edge_segments(e['path'])]
    def box_of(edge, c):
        return edge_label_box(dict(edge, lx=c[1], ly=c[2], anchor=c[3]))
    def static_ok(box):
        return not label_conflicts(box, nodes, groups, boxes, edges)
    work = []
    for i, e in enumerate(edges):
        if not e['label']:
            continue
        mine = edge_segments(e['path'])
        shared = []
        for s in mine:
            sb = seg_box(*s)
            sh = 0
            for j, o in all_segs:
                if j != i:
                    ob = seg_box(*o)
                    if sb[0] == sb[1] == ob[0] == ob[1] and max(sb[2], ob[2]) < min(sb[3], ob[3]):
                        sh = 1
                    if sb[2] == sb[3] == ob[2] == ob[3] and max(sb[0], ob[0]) < min(sb[1], ob[1]):
                        sh = 1
            shared.append(sh)
        cands = [c for c in edge_label_candidates(e, shared) if static_ok(box_of(e, c))]
        work.append((len(cands), i, e, cands))
    work.sort(key=lambda w: (w[0], w[1]))
    placed, errors = [], []
    for _, i, e, cands in work:
        for c in cands:
            box = box_of(e, c)
            if not label_conflicts(box, nodes, groups, boxes, edges, placed):
                e['lx'], e['ly'], e['anchor'] = c[1], c[2], c[3]
                placed.append(box)
                if strict and c[0] >= 100:
                    errors.append(e)
                break
        else:
            errors.append(e)
    if errors:
        raise LabelPlacementError('edge label has no free slot: ' + ', '.join(
            f'{e["from"]}→{e["to"]} "{e["label"]}"' for e in errors)
            + ' — shorten it or move nodes', errors)


def edge_segments(path):
    """Decode the compiler's absolute orthogonal M/H/V path subset."""
    tokens = re.findall(r'[MHV]|-?\d+(?:\.\d+)?', path)
    segments, cursor, i = [], None, 0
    while i < len(tokens):
        command = tokens[i]
        if command == 'M':
            cursor = (float(tokens[i + 1]), float(tokens[i + 2]))
            i += 3
        else:
            value = float(tokens[i + 1])
            end = (value, cursor[1]) if command == 'H' else (cursor[0], value)
            segments.append((cursor, end))
            cursor, i = end, i + 2
    return segments




def edge_label_box(edge):
    width = edge['lw']
    left = edge['lx'] - width / 2 if edge['anchor'] == 'middle' else edge['lx'] - width if edge['anchor'] == 'end' else edge['lx'] - 3
    return left, left + width, edge['ly'] - 14, edge['ly'] + 6


def collect_conflicts(nodes, groups, boxes, edges):
    """Fail before output on unresolved group or edge-label geometry collisions."""
    errors = []
    for edge in edges:
        if any(segment_hits_node(a, b, n) for a, b in edge_segments(edge['path']) for n in nodes.values()):
            errors.append('edge intersects node: ' + edge['path'])
    def descendants(gid):
        result = set(groups[gid].get('nodes', []))
        for child in groups[gid].get('children', []):
            result |= descendants(child)
        return result
    def nested(parent, child):
        return any(c == child or nested(c, child) for c in groups[parent].get('children', []))
    gids = list(groups)
    for i, gid in enumerate(gids):
        b = boxes[gid]
        for child in groups[gid].get('children', []):
            if boxes[child]['top'] - b['top'] < 36:
                errors.append(f'nested top clearance: {gid}/{child}')
        for other in gids[i + 1:]:
            if (nested(gid, other) or nested(other, gid) or groups[gid].get('allow_overlap')
                    or groups[other].get('allow_overlap') or descendants(gid) & descendants(other)):
                continue
            c = boxes[other]
            if max(b['left'], c['left']) < min(b['right'], c['right']) and max(b['top'], c['top']) < min(b['bottom'], c['bottom']):
                errors.append(f'group overlap: {gid}/{other}')
    placed = []
    for gid, group in groups.items():
        others = {k: v for k, v in groups.items() if k != gid}
        if 'gl_box' in group:
            errors.extend(f'{gid}: {e}' for e in label_conflicts(group['gl_box'], nodes, others, boxes, edges, group_label=True))
    for edge in edges:
        if edge['label']:
            box = edge_label_box(edge)
            errors.extend(f'{edge["label"]}: {e}' for e in label_conflicts(box, nodes, groups, boxes, edges, placed))
            placed.append(box)
    return errors


def verify_no_collisions(nodes, groups, boxes, edges):
    errors = collect_conflicts(nodes, groups, boxes, edges)
    if errors:
        raise DiagramError('Static collision verification failed:\n' + '\n'.join(errors))


TOKENS_LIGHT = {
    "color-paper": "#fafbfc",
    "color-paper-2": "#f2f4f6",
    "color-rule": "oklch(93% 0.007 255)",
    "color-rule-2": "oklch(83% 0.011 255)",
    "color-muted": "#62666d",
    "color-accent-ink": "#2054a7",
    "color-purple-ink": "#7934a5",
    "color-g1-nested": "oklch(96.5% 0.015 60 / .28)",
    "status-primary-stripe": "#2054a7",
    "status-primary-bg": "#d9e9ff",
    "status-primary-fg": "#003f8a",
    "status-warn-stripe": "#b67700",
    "status-warn-bg": "#fbe9c6",
    "status-warn-fg": "#6b3e03",
    "status-danger-stripe": "#b7191c",
    "status-danger-bg": "#ffdfde",
    "status-danger-fg": "#8a1616",
    "status-success-stripe": "#007e57",
    "status-success-bg": "#d4f4e5",
    "status-success-fg": "#005136",
    "color-neutral": "oklch(46% 0.015 255)",
    "color-ink-2": "oklch(34% 0.018 257)",
    "color-ink": "oklch(24% 0.020 258)",
    "color-accent": "oklch(58% 0.20 256)",
    "color-graphite": "oklch(24% 0.018 260)",
    "color-g1": "oklch(68% 0.15 55)",
    "color-g1-soft": "oklch(78% 0.12 55)",
    "color-g1-ink": "#8c4e22",
    "color-g1-tint": "oklch(96.5% 0.015 60 / .45)",
    "color-accent-soft": "oklch(58% 0.20 256 / .45)",
    "color-accent-tint": "oklch(97% 0.012 256 / .45)",
    "color-purple": "oklch(58% 0.19 305)",
    "color-purple-tint": "oklch(96% 0.02 305 / .38)",
    "font-display": "\"Geist\", \"Apple SD Gothic Neo\", \"Pretendard\", ui-sans-serif, system-ui, sans-serif",
    "font-body": "\"Apple SD Gothic Neo\", \"Pretendard\", ui-sans-serif, system-ui, sans-serif",
    "font-mono": "\"JetBrains Mono\", ui-monospace, \"SF Mono\", Menlo, monospace",
    "space-xs": "4px",
    "space-sm": "8px",
    "space-md": "16px",
    "space-lg": "24px",
    "space-xl": "40px",
    "space-2xl": "64px",
    "radius-card": "10px",
    "radius-tile": "12px",
    "color-veil": "oklch(98.5% 0.004 250 / .90)"
}
TOKENS_DARK = {
    "color-paper": "#111418",
    "color-paper-2": "#191d23",
    "color-rule": "oklch(24% 0.013 255)",
    "color-rule-2": "#475569",
    "color-muted": "#9ba2ae",
    "color-accent-ink": "#83b5ff",
    "color-purple-ink": "#cc9af3",
    "color-g1-nested": "oklch(26% 0.030 60 / .22)",
    "status-primary-stripe": "#83b5ff",
    "status-primary-bg": "#0e325f",
    "status-primary-fg": "#bedaff",
    "status-warn-stripe": "#eebc4a",
    "status-warn-bg": "#4d3202",
    "status-warn-fg": "#f5dc98",
    "status-danger-stripe": "#f14d4c",
    "status-danger-bg": "#5f1a19",
    "status-danger-fg": "#fdc8c7",
    "status-success-stripe": "#3fbe90",
    "status-success-bg": "#0b3c2b",
    "status-success-fg": "#b0eacf",
    "color-neutral": "oklch(72% 0.012 255)",
    "color-ink-2": "oklch(85% 0.010 255)",
    "color-ink": "oklch(94% 0.008 255)",
    "color-accent": "oklch(70% 0.16 256)",
    "color-graphite": "oklch(31% 0.020 260)",
    "color-g1": "oklch(70% 0.14 55)",
    "color-g1-soft": "oklch(58% 0.11 55)",
    "color-g1-ink": "oklch(78% 0.12 55)",
    "color-g1-tint": "oklch(26% 0.030 60 / .35)",
    "color-accent-soft": "oklch(70% 0.16 256 / .5)",
    "color-accent-tint": "oklch(28% 0.045 256 / .32)",
    "color-purple": "oklch(74% 0.16 305)",
    "color-purple-tint": "oklch(28% 0.045 305 / .30)",
    "color-veil": "oklch(18% 0.012 255 / .90)"
}

DARK_RULES = """
{root} .g-label img.lt, {root} .tile img.lt, {root} .card-meta img.lt {{display:none;}}
{root} .g-label img.dk, {root} .tile img.dk, {root} .card-meta img.dk {{display:block;}}
{root} .g-label img.plate {{background:#fff;border-radius:3px;padding:2px;width:18px;height:18px;}}
"""


def css_vars(tokens):
    return ';'.join(f'--{k}:{v}' for k, v in tokens.items()) + ';'


def theme_css():
    light = ':root{color-scheme:light;' + css_vars(TOKENS_LIGHT) + '}'
    def dark(root):
        return root + '{color-scheme:dark;' + css_vars(TOKENS_DARK) + '}' + DARK_RULES.format(root=root)
    return light + dark(':root[data-theme="dark"]') + '@media(prefers-color-scheme:dark){' + dark(':root:not([data-theme="light"])') + '}'


STATUS_GLYPH = {
    'warn': '<svg class="st" viewBox="0 0 10 10" role="img" aria-label="warning"><path d="M5 1 9.5 9h-9z" fill="currentColor"/></svg>',
    'danger': '<svg class="st" viewBox="0 0 10 10" role="img" aria-label="failure"><path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
    'success': '<svg class="st" viewBox="0 0 10 10" role="img" aria-label="success"><path d="M1.5 5.5 4 8l4.5-6" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
}


def render_html(spec, nodes, groups, group_boxes, routed_edges, canvas_w, canvas_h, icons_dir: pathlib.Path, fonts_dir: pathlib.Path):
    manifest = {}
    mpath = icons_dir / "manifest.json"
    if mpath.exists():
        manifest = json.loads(mpath.read_text(encoding="utf-8"))

    def icon_img(icon_key, is_group_label=False):
        if not icon_key:
            return ""
        entry = manifest.get(icon_key, {})
        if is_group_label and entry.get("dark_file"):
            return f'<img class="lt" src="%%ICON_{icon_key}%%" alt=""><img class="dk" src="%%ICON_{icon_key}.dark%%" alt="">'
        cls = ' class="plate"' if is_group_label and entry.get("white_fill") else ""
        return f'<img{cls} src="%%ICON_{icon_key}%%" alt="">'

    sorted_gids = sorted(groups.keys(), key=lambda g: -(group_boxes[g]["width"] * group_boxes[g]["height"]))
    group_divs = []
    for gid in sorted_gids:
        g = groups[gid]
        b = group_boxes[gid]
        style_cls = g.get('style', 'ga')
        g_icon = icon_img(g.get("icon"), is_group_label=True)
        label_html = html_lib.escape(g.get("label", gid))
        pos_cls = ""
        group_divs.append(
            f'    <div class="group {style_cls}" style="left:{b["left"]}px; top:{b["top"]}px; width:{b["width"]}px; height:{b["height"]}px;">\n'
            f'      <div class="g-label{pos_cls}" style="left:{g.get("gl_left", 12)}px">{g_icon}{label_html}</div>\n'
            f'    </div>'
        )

    edge_Els = []
    for e in routed_edges:
        edge_Els.append(f'      <path class="{e["cls"]}" d="{e["path"]}" marker-end="url(#ar)"/>')
        if e["label"]:
            left, right, top, bottom = edge_label_box(e)
            edge_Els.append(f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" rx="6" fill="var(--color-paper)"/>')
            anchor_attr = f' text-anchor="{e["anchor"]}"' if e["anchor"] != "start" else ""
            edge_Els.append(
                f'      <text class="{e["label_cls"]}" x="{e["lx"]}" y="{e["ly"]}"{anchor_attr}>{html_lib.escape(e["label"])}</text>'
            )

    node_divs = []
    for nid, n in nodes.items():
        icon_key = n.get("icon")
        entry = manifest.get(icon_key, {})
        replicas = int(n.get("replicas", 1))
        badge_text = n.get("badge") or (f"×{replicas}" if replicas > 1 else "")

        tile_cls = "tile"
        if n.get("tile"):
            tile_cls = f"tile {n['tile']}"
        elif entry.get("source") == "aws" and replicas == 1:
            tile_cls = "tile bare"
        elif entry.get("white_fill"):
            tile_cls = "tile dark"

        if replicas >= 3:
            tile_cls += " stack-3"
        elif replicas == 2:
            tile_cls += " stack-2"

        badge_html = f'<span class="badge">{html_lib.escape(badge_text)}</span>' if badge_text else ""
        w_style = f";width:{n['width']}px" if n["width"] != NODE_W else ""
        img_tag = icon_img(icon_key, is_group_label=False)
        if not icon_key and n["kind"] == "tile":
            img_tag = f'<span class="monogram">{html_lib.escape(n["name"][:2].upper())}</span>'
        if n["kind"] == "card":
            status = n.get("status", "primary")
            step = html_lib.escape(str(n.get("step", "")))
            detail = html_lib.escape(n.get("detail", ""))
            node_divs.append(
                f'<div class="node card {status}" style="left:{n["left"]}px;top:{n["topY"]}px;width:176px;height:84px">'
                f'<div class="card-meta">{img_tag}' + (f'<span class="card-step {status}">{STATUS_GLYPH.get(status, "")}{step}</span>' if step or status in STATUS_GLYPH else '') + '</div>'
                f'<div class="card-title" title="{html_lib.escape(n["name"], quote=True)}">{html_lib.escape(n["name"])}</div>'
                f'<div class="card-detail" title="{detail}">{detail}</div></div>'
            )
            continue
        node_divs.append(
            f'    <div class="node" style="left:{n["left"]}px;top:{n["topY"]}px{w_style}">\n'
            f'      <div class="{tile_cls}">{img_tag}{badge_html}</div>\n'
            f'      <div class="name"><span>{html_lib.escape(n["name"])}</span></div>'
            + (f'<div class="role"><span>{html_lib.escape(n["role"])}</span></div>\n' if n.get('role') else '') +
            f'    </div>'
        )

    sources_used = []
    used_keys = {item['icon'] for item in list(nodes.values()) + list(groups.values()) if item.get('icon')}
    for k in sorted(used_keys):
        v = manifest.get(k, {})
        s = v.get("source", "")
        label = {
            "aws": "AWS Architecture Icons",
            "gcp": "Google Cloud product icons",
            "azure": "Azure Public Service Icons",
            "lucide": "Lucide",
        }.get(s, s)
        if label and label not in sources_used:
            sources_used.append(label)
    sources_str = html_lib.escape(" / ".join(sources_used)) if sources_used else "none"

    legend_labels = spec.get('legend_labels', {})
    line_counts = {k: sum(e.get('type', 'primary') == k for e in spec.get('edges', [])) for k in ('primary', 'internal', 'dashed')}
    status_counts = {k: sum(n['kind'] == 'card' and n.get('status') == k for n in nodes.values()) for k in ('warn', 'danger', 'success')}
    line_items = [k for k, c in line_counts.items() if c >= 2 and k in legend_labels]
    if len(line_items) < 2:
        line_items = []
    status_items = [k for k, c in status_counts.items() if c >= 2 and k in legend_labels]
    legend_parts = []
    for kind in line_items:
        cls = {'primary': '', 'internal': 'n', 'dashed': 'n dash'}[kind]
        legend_parts.append(f'<span><span class="sw {cls}"></span>{html_lib.escape(legend_labels[kind])}</span>')
    for kind in status_items:
        legend_parts.append(f'<span><span class="sw-card {kind}">{STATUS_GLYPH[kind]}</span>{html_lib.escape(legend_labels[kind])}</span>')
    legend_html ='<div class="legend">' + ''.join(legend_parts) + '</div>' if legend_parts else ''

    title = html_lib.escape(spec.get("title", "Architecture Diagram"))
    kicker = html_lib.escape(spec.get("kicker", "diagram / compiled"))
    lede = html_lib.escape(spec.get("lede", ""))

    edge_summary = ''.join(f'<li>{html_lib.escape(nodes[e["from"]]["name"])} → {html_lib.escape(nodes[e["to"]]["name"])}: {html_lib.escape(e.get("label", ""))}</li>' for e in routed_edges)
    html = f"""<!DOCTYPE html>
<html lang="{html_lib.escape(spec.get('lang', 'en'), quote=True)}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script>try {{ const saved = localStorage.getItem('diagram-theme'); if (saved === 'dark' || saved === 'light') document.documentElement.dataset.theme = saved; }} catch(e) {{}}</script>
<style>
{theme_css()}
@font-face {{ font-family:"Geist"; font-style:normal; font-weight:100 900; font-display:swap;
  src:url(data:font/woff2;base64,%%FONT_DISPLAY%%) format("woff2"); }}
@font-face {{ font-family:"JetBrains Mono"; font-style:normal; font-weight:100 800; font-display:swap;
  src:url(data:font/woff2;base64,%%FONT_JBM%%) format("woff2"); }}
.kicker, .node .role, .el, .legend, .foot, .badge {{ letter-spacing: 0.04em; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ overflow-x: clip; }}
body {{ background: var(--color-paper); color: var(--color-ink); font-family: var(--font-body); padding: var(--space-xl) var(--space-lg) var(--space-2xl); }}
.page {{ width: fit-content; max-width: 100%; margin: 0 auto; }}
.head {{ display:grid; grid-template-columns: 1fr auto; gap: var(--space-lg); align-items:end;
  padding-bottom: var(--space-md); border-bottom: 1px solid var(--color-rule-2); margin-bottom: var(--space-lg); }}
.theme-toggle {{ grid-row:1; grid-column:2; align-self:center; border:1px solid var(--color-rule-2); border-radius:999px; padding:6px 12px; background:var(--color-paper-2); color:var(--color-ink); cursor:pointer; justify-self:end; }}
.kicker {{ grid-row:1; grid-column:1; }}
h1 {{ grid-row:2; grid-column:1 / -1; }}
.lede {{ grid-row:3; grid-column:1 / -1; }}
.kicker {{ font-family: var(--font-mono); font-size: 11px; color: var(--color-accent-ink); margin-bottom: var(--space-sm); }}
h1 {{ font-family: var(--font-display); font-weight: 700; font-size: clamp(22px, 4vw, 30px); letter-spacing: -0.005em; line-height: 1.2; }}
.lede {{ max-width: 420px; font-size: 12px; line-height: 1.7; color: var(--color-neutral); padding-bottom: 2px; }}
.scroller {{ overflow-x: auto; width:fit-content; max-width:100%; margin-inline:auto; border: 1px solid var(--color-rule-2); border-radius: var(--radius-card); }}
.canvas {{ position: relative; width: {canvas_w}px; height: {canvas_h}px; background: var(--color-paper);
  background-image:
    linear-gradient(var(--color-rule) 1px, transparent 1px),
    linear-gradient(90deg, var(--color-rule) 1px, transparent 1px);
  background-size: 24px 24px; background-position: -1px -1px; }}
.group {{ position:absolute; border-radius: var(--radius-tile); }}
.g-label {{ position:absolute; top:10px; left:12px; z-index:2; display:flex; align-items:center; gap:6px;
  font-family: var(--font-display); font-size: 12px; font-weight: 600;
  color: var(--color-neutral); white-space: nowrap;
  background: var(--color-veil); backdrop-filter: blur(1.5px); padding: 1px 6px; border-radius: 4px; }}

.g-label img {{ width: 14px; height: 14px; }}
.g-label img.dk, .tile img.dk {{ display:none; }}
.group.ga {{ border:1.5px solid var(--color-g1); background: var(--color-g1-tint); }}
.group.ga-nested {{ border:1.5px dashed var(--color-g1-soft); background: var(--color-g1-nested); }}
.group.gb {{ border:1.5px solid var(--color-accent-soft); background: var(--color-accent-tint); }}
.group.gp {{ border:1.5px dashed var(--color-purple); background: var(--color-purple-tint); }}
.group.ga > .g-label, .group.ga-nested > .g-label {{ color: var(--color-g1-ink); }}
.group.gb > .g-label {{ color: var(--color-accent-ink); }}
.group.gp > .g-label {{ color: var(--color-purple-ink); }}
.group.aws {{ border:1.5px solid var(--color-ink); border-radius:0; }}
.group.aws > .g-label {{ top:-1.5px; left:-1.5px; gap:8px; color: var(--color-ink); padding: 0 8px 0 0; border-radius: 0; }}
.group.aws:not(.private):not(.public) > .g-label img {{ width:30px; height:30px; }}
.group.aws.vpc {{ border-color:#8C4FFF; }}
.group.aws.private {{ border-color:#00A4A6; }}
.group.aws.public {{ border-color:#7AA116; }}
.group.aws.private > .g-label, .group.aws.public > .g-label {{ top:8px; left:10px; padding: 1px 6px; border-radius: 3px; }}

.node {{ position:absolute; z-index:2; width:132px; text-align:center; }}
.node.card {{ text-align:left; padding:8px 10px; border:1px solid var(--color-rule-2); border-left:4px solid var(--color-accent); border-radius:8px; background:var(--color-paper-2); overflow:hidden; }}
.card.primary {{ border-left-color:var(--color-rule-2); border-left-width:1px; padding-left:13px; }}
.card.warn {{ border-left-color:var(--status-warn-stripe); }}
.card.danger {{ border-left-color:var(--status-danger-stripe); }}
.card.success {{ border-left-color:var(--status-success-stripe); }}
.card-step {{ display:inline-flex; align-items:center; gap:4px; }}
.card-step.primary {{ background:var(--status-primary-bg); color:var(--status-primary-fg); border-color:transparent !important; }}
.card-step.warn {{ background:var(--status-warn-bg); color:var(--status-warn-fg); border-color:transparent !important; }}
.card-step.danger {{ background:var(--status-danger-bg); color:var(--status-danger-fg); border-color:transparent !important; }}
.card-step.success {{ background:var(--status-success-bg); color:var(--status-success-fg); border-color:transparent !important; }}
.st {{ width:9px; height:9px; flex:none; }}
.sw-card {{ display:inline-flex; align-items:center; justify-content:center; width:24px; height:14px; margin-right:6px; vertical-align:middle; border:1px solid var(--color-rule-2); border-radius:3px; background:var(--color-paper-2); }}
.sw-card.warn {{ border-left:4px solid var(--status-warn-stripe); color:var(--status-warn-fg); }}
.sw-card.danger {{ border-left:4px solid var(--status-danger-stripe); color:var(--status-danger-fg); }}
.sw-card.success {{ border-left:4px solid var(--status-success-stripe); color:var(--status-success-fg); }}
.card-meta {{ display:flex; align-items:center; gap:6px; height:18px; color:var(--color-muted); font:10px var(--font-mono); }}
.card-meta img {{ width:18px; height:18px; object-fit:contain; background:white; border-radius:3px; }}
.card-meta span {{ border:1px solid var(--color-rule-2); border-radius:999px; padding:1px 5px; }}
.card-meta img.dk {{ display:none; }}
.card-title {{ font:700 13px var(--font-display); margin-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.card-detail {{ font:9px var(--font-mono); color:var(--color-muted); margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.monogram {{ font:600 22px var(--font-mono); color:var(--color-ink); }}
.sr-only {{ position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap; }}
.tile {{ position:relative; width:60px; height:60px; margin:0 auto; border-radius: var(--radius-tile);
  background:#fff; border:1px solid var(--color-rule-2); display:grid; place-items:center;
  box-shadow: 0 1px 2px oklch(24% 0.02 258 / 0.05); }}
/* Stacked replica / shard cards behind the main tile */
.tile.stack-2::before, .tile.stack-3::before, .tile.stack-3::after {{
  content:""; position:absolute; inset:0; border-radius: var(--radius-tile);
  background:#fff; border:1px solid var(--color-rule-2); pointer-events:none;
}}
.tile.stack-2::before {{ transform: translate(5px, -5px); z-index:-1; box-shadow: 0 1px 2px oklch(24% 0.02 258 / 0.04); }}
.tile.stack-3::before {{ transform: translate(4px, -4px); z-index:-1; }}
.tile.stack-3::after  {{ transform: translate(8px, -8px); z-index:-2; background: var(--color-paper-2); }}

/* Replica / Shard count pill badge */
.badge {{
  position:absolute; top:-8px; right:-14px; z-index:3;
  font-family: var(--font-mono); font-size:9px; font-weight:600;
  color:var(--status-primary-fg); background: var(--status-primary-bg);
  padding: 1px 5px; border-radius: 999px;
  border: 1.5px solid var(--color-paper);
  white-space: nowrap; box-shadow: 0 1px 3px oklch(24% 0.02 258 / 0.18);
}}

.tile img {{ width:34px; height:34px; object-fit:contain; }}
.tile.dark {{ background: var(--color-graphite); border-color: var(--color-graphite); }}
.tile.bare {{ background:none; border:none; box-shadow:none; }}
.tile.bare img {{ width:60px; height:60px; }}
.node .name {{ font-family: var(--font-display); font-weight:600; font-size:13px; margin-top: var(--space-sm); }}
.node .role {{ font-family: var(--font-mono); font-size:9.5px; color: var(--color-muted); margin-top:2px; }}
.node .name span, .node .role span {{ background: var(--color-veil); backdrop-filter: blur(1.5px);
  padding: 0 var(--space-xs); border-radius: 3px; -webkit-box-decoration-break: clone; box-decoration-break: clone; }}
svg.edges {{ position:absolute; inset:0; z-index:1; width:{canvas_w}px; height:{canvas_h}px; pointer-events:none; }}
.e  {{ stroke: var(--color-accent); stroke-width:1.6; fill:none; }}
.n  {{ stroke: var(--color-neutral); stroke-width:1.4; fill:none; }}
.dash {{ stroke-dasharray:4 5; }}
.el {{ font-family: var(--font-mono); font-size:10.5px; fill: var(--color-neutral);
  paint-order: stroke; stroke: var(--color-paper); stroke-width:5px; stroke-linejoin:round; }}
.el.a {{ fill: var(--color-accent-ink); }}
.legend {{ display:flex; gap: var(--space-lg); align-items:center; margin-top: var(--space-md);
  font-family: var(--font-mono); font-size:10px; color: var(--color-muted); flex-wrap:wrap; }}
.legend .sw {{ display:inline-block; width:30px; vertical-align:middle; margin-right:6px; border-top:1.6px solid var(--color-accent); }}
.legend .sw.n {{ border-color: var(--color-neutral); border-top-width:1.4px; }}
.legend .sw.dash {{ border-top-style: dashed; }}
.foot {{ margin-top: var(--space-xl); padding-top: var(--space-md); border-top: 1px solid var(--color-rule-2);
  display:flex; justify-content:space-between; gap: var(--space-md); flex-wrap:wrap;
  font-family: var(--font-mono); font-size:10px; color: var(--color-muted); }}
</style>
</head>
<body>
<div class="page">
  <header class="head">
      <div class="kicker">{kicker}</div>
      <h1>{title}</h1>
    {f'<p class="lede">{lede}</p>' if lede else ""}
    <button class="theme-toggle" type="button">Dark theme</button>
  </header>
  <figure aria-label="{title}">
  <ul class="sr-only">{edge_summary}</ul>
  <div class="scroller">
  <div class="canvas">
{chr(10).join(group_divs)}
    <svg class="edges" viewBox="0 0 {canvas_w} {canvas_h}" aria-hidden="true">
      <defs>
        <marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
          <path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/>
        </marker>
      </defs>
{chr(10).join(edge_Els)}
    </svg>
{chr(10).join(node_divs)}
  </div>
  </div>
  </figure>
  {legend_html}
  <div class="foot">
    <span>engineering blueprint · declarative JSON · deterministic grid</span>
    {f"<span>icons: {sources_str} · diagram compiler</span>" if sources_used else ""}
  </div>
</div>
<script>
const root = document.documentElement;
const button = document.querySelector('.theme-toggle');
const media = window.matchMedia('(prefers-color-scheme: dark)');
const effectiveTheme = () => root.dataset.theme || (media.matches ? 'dark' : 'light');
function updateThemeLabel() {{
  const dark = effectiveTheme() === 'dark';
  button.textContent = dark ? 'Light Mode' : 'Dark Mode';
}}
button.addEventListener('click', function () {{
  const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
  root.dataset.theme = next;
  try {{ localStorage.setItem('diagram-theme', next); }} catch (e) {{}}
  updateThemeLabel();
}});
media.addEventListener('change', updateThemeLabel);
updateThemeLabel();
</script>
</body>
</html>
"""

    for tok, fn in (("%%FONT_DISPLAY%%", "Geist.woff2"), ("%%FONT_JBM%%", "JetBrainsMono.woff2")):
        if tok in html and (fonts_dir / fn).exists():
            html = html.replace(tok, b64_file(fonts_dir / fn))

    for key in used_keys:
        entry = manifest.get(key, {})
        for field, suffix in (('file', ''), ('dark_file', '.dark')):
            token = f'%%ICON_{key}{suffix}%%'
            if token in html and entry.get(field):
                asset = (icons_dir / entry[field]).resolve()
                if not asset.is_relative_to(icons_dir.resolve()):
                    raise DiagramError(f'icon {key}: asset path escapes cache')
                html = html.replace(token, data_uri(asset))

    unresolved = re.findall(r'%%(?:ICON|FONT)_[^%]+%%', html)
    if unresolved:
        raise DiagramError('Missing embedded assets: ' + ', '.join(sorted(set(unresolved))))
    return html


PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent
ARCHETYPES = (
    ("infra", "Infrastructure Boundary View", "stack", "01-cloud-vpc-msa.json",
     "Cloud → VPC → Subnets boundaries; nested groups.children; 60x60 official brand/cloud tiles."),
    ("layers", "Functional Layer and Split Storage View", "stack", "02-functional-layers.json",
     "Disjoint horizontal/vertical groups.nodes: Ingress, Sync API, Async Event Mesh, OLTP/Cache, OLAP/Lake."),
    ("sharded", "Scale-Out Replicas, Sharded DB and Cross-Cutting Domain Slice", "stack", "03-sharded-replicas.json",
     "nodes.replicas: N + badge for pod/broker decks; explicit DB shard nodes; groups.allow_overlap: true + pad_offset for vertical team/domain slices across horizontal tiers."),
    ("flow", "Engineering Execution and Fallback Pipeline", "flow", "04-engineering-flow.json",
     "176x84 execution cards with step, detail, status: primary|warn|danger|success and optional 18px logo; request/event/DLQ recovery."),
    ("hybrid", "Mixed Execution Flow + Storage/Infra Tiles", "flow", "05-hybrid.json",
     "mode flow; mix nodes.kind: card execution steps with kind: tile + replicas infrastructure/database targets."),
)


def template_reference():
    return [dict(template=name, title=title, mode=mode, example='examples/' + example,
                 when=description) for name, title, mode, example, description in ARCHETYPES]


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
            tmp = pathlib.Path(f.name)
            f.write(content)
        os.replace(tmp, path)
    finally:
        if tmp and tmp.exists():
            tmp.unlink()


def json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DiagramError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def reject_constant(value):
    raise DiagramError(f'non-finite JSON number: {value}')


def run():
    ap = argparse.ArgumentParser(prog="diagram", description="Build standalone engineering diagrams from JSON.")
    commands = ap.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="Compile JSON to standalone HTML and optional light/dark PNGs")
    build.add_argument("spec", type=pathlib.Path)
    build.add_argument("out", type=pathlib.Path)
    build.add_argument("--skill-dir", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent.parent)
    build.add_argument("--icons-dir", type=pathlib.Path, default=None)
    build.add_argument("--png", action="store_true", help="Also write OUT.png and OUT-dark.png (Playwright/Chromium required)")
    templates = commands.add_parser("templates", help="Show the five starter templates")
    templates.add_argument("--json", action="store_true", help="Emit compact template metadata")
    init = commands.add_parser("init", help="Copy a starter JSON to OUT.json, or stdout when omitted")
    init.add_argument("template", choices=[item[0] for item in ARCHETYPES])
    init.add_argument("out", nargs="?", type=pathlib.Path)
    args = ap.parse_args()
    if args.command == "templates":
        references = template_reference()
        if args.json:
            print(json.dumps(references, ensure_ascii=False, indent=2))
        else:
            for ref in references:
                print(f"{ref['template']}: {ref['title']} (mode={ref['mode']}) — {ref['when']}")
        return
    if args.command == "init":
        example = next(item[3] for item in ARCHETYPES if item[0] == args.template)
        content = (PACKAGE_ROOT / "examples" / example).read_text(encoding="utf-8")
        if args.out:
            atomic_write(args.out, content)
        else:
            sys.stdout.write(content)
        return

    spec = json.loads(args.spec.read_text(encoding="utf-8"), object_pairs_hook=json_pairs, parse_constant=reject_constant)
    icons_dir = args.icons_dir or (args.out.parent / "icons")
    validate_spec(spec)
    nodes, groups, group_boxes, routed_edges, cw, ch = compute_layout(spec)
    if args.png and importlib.util.find_spec("playwright") is None:
        raise DiagramError("PNG export needs Playwright: pip install playwright; python3 -m playwright install chromium")
    for warning in spec_warnings(spec):
        print(f'diagram: warning: {warning}', file=sys.stderr)
    ensure_icons(spec, icons_dir, args.skill_dir)
    fonts_dir = args.skill_dir / "assets" / "fonts"
    html = render_html(spec, nodes, groups, group_boxes, routed_edges, cw, ch, icons_dir, fonts_dir)
    print(f'[OK] Checked node, group and label geometry ({len(groups)} group labels, {len(routed_edges)} edge labels). Edge-edge crossings are not checked; inspect both themes.')
    atomic_write(args.out, html)
    print(f"compiled {args.out} ({len(html) // 1024} KB, canvas {cw}x{ch}, {len(nodes)} nodes, {len(groups)} groups, {len(routed_edges)} edges)")
    if args.png:
        subprocess.run([sys.executable, str(args.skill_dir / "scripts" / "render_png.py"),
                        str(args.out), str(args.out.with_suffix(".png"))], check=True)


def main():
    try:
        run()
    except (DiagramError, json.JSONDecodeError, OSError, subprocess.CalledProcessError) as error:
        print(f'diagram: error: {error}', file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
