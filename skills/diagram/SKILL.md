---
name: diagram
description: Create engineer-facing infrastructure, tech-stack, sharding/replica and execution/fallback blueprints as standalone HTML/PNG from JSON, or quick inline ASCII/Mermaid. Use for 아키텍처 다이어그램, 인프라 구성도, 기술 스택 구성도, 샤딩·복제 구성, 장애 복구 흐름. Use archify for business workflows, page journeys and explainers for non-developers.
---

# Diagram — Engineering Blueprint

## Choose the output

Honor explicit formats. Use prose when it communicates the answer faster.

| Request | Tool |
| --- | --- |
| Quick explanation in chat/Markdown, no format specified | Inline text or Mermaid; no files |
| Engineering infrastructure, stack, sharding or recovery with logos or shareable files | `diagram build` |
| Engineering sequence, ERD or state diagram | Mermaid; archify for standalone HTML or interaction |
| Business workflow, page journey or explanation for non-developers | Separately installed archify |

## Workflow

Run `./scripts/install.sh` from this repository to link `~/.local/bin/diagram`; add that directory to PATH.

1. Run `diagram templates` to choose the nearest template.
2. Run `diagram init <template> spec.json`.
3. Edit the JSON: put the conclusion in the title, concrete verbs/ports/failure rules on edges, and repeated encoding meanings in `legend_labels`.
4. Run `diagram build spec.json out.html --png`.
5. Open `out.png` and `out-dark.png`; inspect line crossings and truncated text.
6. Resolve errors/warnings by changing labels or grid positions, rebuild, and deliver JSON plus HTML and optional PNGs.

`diagram templates --json` emits compact metadata without pattern bodies. `diagram init <template>` emits the complete JSON to stdout when the output path is omitted.
`diagram build spec.json out.html --icons-dir /path/to/cache` reuses an icon cache. Python 3 standard library is sufficient for HTML; PNG export additionally requires Playwright and Chromium.

## Drawing principles

- Draw only what the decision needs.
- State mechanisms: `gRPC :50051`, `failed ×3`.
- Show the differences when comparing views.
- Explain encodings repeated at least twice with `legend_labels`.
- Use status only when it carries meaning; warning/failure/success cards also have SVG symbols.

## Templates

- `infra`, mode `stack`: deployment/network boundaries, nested cloud/VPC/subnets. [JSON](examples/01-cloud-vpc-msa.json)
- `layers`, mode `stack`: functional responsibilities and split storage. [JSON](examples/02-functional-layers.json)
- `sharded`, mode `stack`: replicas, explicit database shards, cross-cutting ownership. [JSON](examples/03-sharded-replicas.json)
- `flow`, mode `flow`: request/event execution, retries, DLQ and recovery. [JSON](examples/04-engineering-flow.json)
- `hybrid`, mode `flow`: execution cards and infrastructure/storage tiles. [JSON](examples/05-hybrid.json)

Template names are CLI inputs; they are not spec modes.

## JSON contract

Unknown fields and obsolete aliases fail before assets are fetched.

| Object | Required | Optional |
| --- | --- | --- |
| Root | `nodes` | `mode,title,kicker,lede,lang,icons,groups,edges,legend_labels` |
| Node common | `id,row,col,name` | `kind,icon` |
| Tile only | | `role,wide,replicas,badge,tile` |
| Card only | | `step,detail,status` |
| Group | `id,label` | `icon,nodes,children,style,allow_overlap,pad_offset,label_pos` |
| Edge | `from,to` | `label,type` |

- Root `mode`: `stack` (default tile) or `flow` (default card). Node `kind: tile|card` overrides it. Header fields are strings; `lang` is a BCP47 tag, default `en`.
- Nodes: unique nonempty string IDs/names, integer rows/columns, one node per grid cell. Maximum 200 nodes, 400 edges, 100 groups and 32 nested child levels.
- Tile: `wide` boolean; `replicas` positive integer, default 1; `badge` string; `tile: dark|bare`. Without an icon, a two-character monospace monogram is rendered. Name ≤36 and role ≤42 display units.
- Card: `step` string or finite number; `detail` string; `status: primary|warn|danger|success`, default primary. Name >20 or detail >26 display units warns of single-line truncation. No tile-field fallbacks.
- Groups: unique ID, nonempty label, unique string arrays `nodes` and/or `children` with at least one member. Existing references, acyclic hierarchy, one parent per child. Style: `ga` (default), `ga-nested,gb,gp,aws,aws vpc,aws private,aws public`. `allow_overlap` boolean; `pad_offset` finite number in [-24,80]; `label_pos: top-left|top-right`.
- Edges: existing distinct endpoints; duplicate same-direction edges fail—merge their labels. `type: primary|internal|dashed`, default primary; label ≤32 display units. Full-width characters count as 1.75 units. Over 25% unlabeled edges warns.
- `legend_labels`: string map with keys `primary,internal,dashed,warn,danger,success`. Unused encodings fail; single uses warn. Line items require at least two uses each and at least two qualifying declared line encodings. Status items require two card uses each. No meaning is inferred.
- `icons`: list of `key:slug`, `key:aws/Service`, `key:gcp/Product`, `key:azure/Service`, `key:lucide/name` or `key=URL`; alternatively map keys to slugs (optional `svgl:` prefix) or URLs. Keys match `[A-Za-z0-9_-]+`; every node/group icon must be declared. Preserve original logo colors. Cache checks source identity and file existence; assets/fonts embed in HTML.

## Build guarantees

The compiler checks node/group geometry, disjoint group overlap, nested top clearance, edge/node intersections, group labels against edges/nodes/other labels, and edge labels against all segments, node content, group labels/borders and other edge labels. Placement and verification share the obstacle predicate; unavailable slots fail instead of silently overlapping. Edge-label failures widen row/column corridors up to five times.

Edge-edge crossings and platform-specific font metrics need inspection in both themes. Text width estimates are not a browser guarantee. HTML writes are atomic, and invalid input leaves existing output intact. PNG dependency availability is checked before HTML is written. Light/dark token sets share component rules; OS theme applies unless a saved manual theme overrides it.

## Quick inline diagrams

Use a `text` block with Unicode borders `┌─┐│└┘`, junctions `├┤┬┴┼` and arrows `▼▲►◄`; keep lines within 80–88 display columns. CJK occupies two columns: prefer open-right trees or narrow, padded closed boxes. Label branches with conditions and show actions with their inputs/outputs.

Use Mermaid for rendered Markdown or when requested: `flowchart TD/LR`, `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`, `xychart-beta`. Quote labels containing spaces/punctuation; avoid HTML in labels.

## Handoff and attribution

Input: verified engineering topology or execution behavior. Deliver editable JSON and standalone HTML, plus requested PNGs. Public examples are synthetic; client files belong in the private project vault and its index.

Adapted from `caru-ini/stack-diagram`; retain [LICENSE](LICENSE) and font notices. Downloaded marks retain their owners' rights and source attribution.
