---
name: service-explorer
description: >-
  Explores, maps, and documents all pages of a web service using Orca's
  built-in browser (`orca` CLI) and persistent local credentials
  (`credentials.json`). Builds an initial site map from navigation menus,
  tracks coverage via a To-Do checklist (recording failure/skip reasons),
  infers each page's purpose, data views, inputs, CTAs, and cross-page data
  dependencies (how data created on one screen affects other screens) using
  hybrid DOM snapshot + visual screenshot analysis strictly without triggering
  state-mutating actions. Also supports an optional Archify visualization mode
  to render interactive HTML diagrams (`dataflow`, `architecture`, `tree`,
  `explainer`) from the collected service specs. Activate this skill whenever
  the user provides a URL or service name to explore, inspect, document, or
  visualize with Archify.
---

# Service Explorer Skill (FDE System & Web ERP Reconnaissance)

Explore and document a target web service or client ERP/MES/Admin system via the Orca built-in browser in **strict navigation-only mode**, saving an Initial Site Map, a Coverage To-Do Checklist, Per-Page Functional Specifications, Screenshots, a **Cross-Page Data Lineage & Impact Map**, and (when requested) **Archify Interactive HTML Diagrams**.

In the FDE pipeline, this skill bridges [`fde-client-recon`](../fde-client-recon/SKILL.md) (external OSINT) and [`fde-domain-simulator`](../fde-domain-simulator/SKILL.md) (Stage 1~4 × 5-Layer simulation): once demo/test credentials for a client's web ERP/MES/Admin are available, `service-explorer` extracts `[Direct]` evidence of official screens (Layer 1) and exact UI/table fields (`schema_keywords`, Layer 3 Tier 1).

Before creating output files, read [output_templates.md](./references/output_templates.md) and strictly follow its directory structure and Markdown templates.

## 0. Browser Initialization & Authentication

1. **Resolve, Open Browser & Reset Viewport Override**
   - Use `$ORCA_CLI_COMMAND` if set; otherwise use `orca`. Always pass `--json`.
   - Run `orca tab list --json`. Reuse an existing tab with `orca goto --url "<url>" --json` or create one with `orca tab create --url "<url>" --json`.
   - **Never set a virtual CDP viewport larger than the physical Orca panel (do NOT run `set viewport 1920 1080`)**: Because Orca's embedded browser (`WebContentsView`) has a fixed physical panel framebuffer (e.g., `1471x939`), overriding CDP viewport metrics to `1920x1080` causes 4-way framebuffer tiling and right-edge clipping. Always reset CDP viewport override via:
     ```bash
     orca exec --command "set viewport 0 0" --json
     ```
   - Run `orca wait --load networkidle --json`.
2. **Credential Lookup, Persistence & Auto-Login (`~/.agents/skills/service-explorer/credentials.json`)**
   - Note: `credentials.json` is strictly local (`chmod 600`) and excluded from Git via `.gitignore` (`**/credentials.json`). Never commit real credentials.
   - Expected JSON schema (see [credentials.example.json](./credentials.example.json)):
     ```json
     {
       "services": {
         "<service_name_or_host>": {
           "url": "https://...",
           "id": "...",
           "password": "...",
           "updatedAt": "ISO-8601"
         }
       }
     }
     ```
   - If the user provides a service name without a URL, resolve `url` from `~/.agents/skills/service-explorer/credentials.json` by matching the service key or hostname.
   - When a login screen or authentication gate appears (initially or mid-exploration due to session expiry):
     - **Case A — Valid credentials exist in `credentials.json`**:
       1. Run `orca snapshot --json` to locate `@eN` refs for ID input, Password input, and Login/Submit button.
       2. Execute `orca fill --element <id_ref> --value "<id>" --json` and `orca fill --element <pw_ref> --value "<password>" --json`.
       3. Execute `orca click --element <submit_ref> --json` and `orca wait --load networkidle --json`.
       4. Re-snapshot (`orca snapshot --json`) to verify login succeeded.
     - **Case B — File missing/corrupted, key missing, login rejected, or 2FA/OTP required**:
       1. Stop immediately and ask the user for credentials (or 2FA approval).
       2. When the user provides credentials, read existing `~/.agents/skills/service-explorer/credentials.json` (or initialize `{"services": {}}` if missing/corrupted), merge the new entry under `services["<service_name_or_host>"]`, write the file, and run `chmod 600 ~/.agents/skills/service-explorer/credentials.json`.
       3. Perform the login steps in Case A.

## 1. Output Directory Layout & Vault Index Registration (`~/docsspace/<project-slug>/`)

Persist all exploration artifacts incrementally under `~/docsspace/<project-slug>/explored-services/<service-slug>/` (inside the private Obsidian Vault `~/docsspace/`, never inside the public `fde-skills` repo). After creating or updating the exploration report, **always register/update the link in `~/docsspace/<project-slug>/00_SSOT_INDEX.md` and `~/docsspace/00_INDEX.md`**:

```text
~/docsspace/<project-slug>/
├── 00_SSOT_INDEX.md               # Project Master Index (must link 00-sitemap-and-todo.md & 99-cross-page-relations.md)
└── explored-services/<service-slug>/
    ├── 00-sitemap-and-todo.md     # Master index: Site Map + Coverage To-Do Checklist
    ├── 99-cross-page-relations.md # Service-wide Data Lineage & Producer->Consumer Impact Matrix
    ├── pages/
    │   └── <NN>-<page-slug>.md    # Per-page spec (purpose, views, inputs, CTAs, upstream/downstream links)
    ├── assets/
    │   └── screenshots/
    │       └── <NN>-<page-slug>.jpg # Visual capture paired 1:1 with each page spec
    └── visualizations/            # [Optional: Option --archify] Standalone interactive HTML via Archify
        ├── service-architecture.html
        └── cross-page-dataflow.html
```

## 2. Sequential Exploration Workflow (Steps 1–6)

### Step 1. Build the Initial Site Map from Navigation Menus
- Run `orca snapshot --json` and capture the entry page (following the zoom + screenshot sequence in Step 3) to visually identify global navigation bars (GNB), sidebars (LNB), icon menus, and drawers that may lack semantic HTML tags.
- If navigation containers are collapsed, click their read-only expander controls (`orca click --element <ref> --json`) and re-run `orca snapshot --json` to reveal child links.
- Extract all navigation hierarchies and write the **Initial Site Map** into `./explored-services/<service-slug>/00-sitemap-and-todo.md` following [output_templates.md](./references/output_templates.md).

### Step 2. Create the Coverage To-Do Checklist
- Convert every unique target page/view from the Site Map into the **To-Do Checklist** inside `00-sitemap-and-todo.md`:
  - `[ ]` Pending visit
  - `[x]` Visited and analyzed (linked to `./pages/<NN>-<page-slug>.md`)
  - `[!]` Unreachable or skipped — **must record the exact reason** (e.g., `403 Forbidden`, `404 Not Found`, `External domain`, `Duplicate template of <route>`, `Logout/Destructive link`).
- **Deduplication & Loop Termination Rules**:
  - **Same-origin only**: Do not visit external domains; mark them `[!] External domain`.
  - **Parameterized detail routes (`/items/:id`)**: Visit at most **1** representative detail page per template pattern; mark sibling rows/links `[!] Duplicate template`.
  - **Pagination & Infinite Lists**: Inspect only Page 1 (plus up to 2 downward scrolls via `orca scroll --direction down --amount 1000 --json`). Do not paginate through data tables.

### Step 3. Visit Target Page & Infer Functionality (Hybrid Visual + DOM Analysis)
- Navigate to the next `[ ]` item via `orca goto --url <url> --json` (or click the navigation menu/tab element for URL-less SPA views), then run `orca wait --load networkidle --json`.
- **Capture Both DOM & Visual Screen**:
  1. Run `orca snapshot --json` (and optionally `orca network --limit 50 --json` to observe read-only GET API resource names) to extract exact text labels, input placeholders, dropdown options, and link targets.
  2. Capture the full 1920px desktop layout without WebContentsView tiling or clipping (pass `--page <browserPageId>` when targeting a specific tab):
     - Apply CSS zoom before capture:
       `orca eval --expression "document.documentElement.style.zoom = String(Math.min(1, window.innerWidth / 1920))" --json`
     - Capture and save the image (`orca full-screenshot --format jpeg --json` or `orca screenshot --format jpeg --json`, decoding base64 `result.data` to `./explored-services/<service-slug>/assets/screenshots/<NN>-<page-slug>.jpg`).
     - Restore CSS zoom immediately after capture:
       `orca eval --expression "document.documentElement.style.zoom = \"\"" --json`
     - Inspect the saved image file using `read_file` to analyze visual layout, spatial grouping, charts/Canvas/SVG widgets, visual hierarchy of CTAs, and icon-only buttons.
- Create `./explored-services/<service-slug>/pages/<NN>-<page-slug>.md` using the Per-Page template in [output_templates.md](./references/output_templates.md), documenting:
  1. **Page Purpose & Role**: Core business or operational function and layout structure.
  2. **Data Views & Display Components**: Tables, KPI cards, charts, and view tabs.
  3. **Input Fields & Filters**: Search inputs, date pickers, dropdowns, text fields, checkboxes/radios.
  4. **Buttons & CTAs (Inferred Behavior)**: All visible buttons/icon-CTAs, their visual prominence, and their predicted behavior without clicking them.
  5. **Cross-Page Data Dependencies & Impact (Upstream & Downstream)**: Identify what domain entities this screen **produces/modifies** (via creation forms, settings, or status CTAs) and what entities it **consumes/references** (via dropdown options, foreign-key columns, or KPI counters).

### Step 4. Enforce Strict Navigation-Only Rule (Zero Side Effects)
- **Never click action buttons or CTAs** on the page (no Create, Save, Edit, Delete, Submit, Execute, Download/Export, Toggle, or Logout actions).
- **Never fill or submit non-authentication forms**.
- **Allowed interactions only**: URL navigation (`orca goto`, `orca back`), scrolling (`orca scroll`), waiting (`orca wait`), capturing (`orca snapshot`, `orca screenshot`, `orca full-screenshot`, `orca network`, `orca exec --command "set viewport 0 0"`, and temporary CSS `document.documentElement.style.zoom` adjustment via `orca eval`), clicking read-only navigation menus/in-page view tabs (`role="tab"`), and login form submission in Section 0.
- **Stale Reference Guard (`browser_stale_ref`)**: Any navigation, tab switch, or menu/tab click invalidates `@eN` refs. Always run `orca snapshot --json` before referencing any element.

### Step 5. Update To-Do & Repeat Steps 3–4 Until All Pages Are Visited
- Update `00-sitemap-and-todo.md` immediately after each page: mark the item `[x]` with a relative link to `./pages/<NN>-<page-slug>.md` (or `[!]` with the failure/skip reason).
- If the visual screenshot or DOM snapshot reveals previously unseen sub-navigation links or view tabs (subject to Step 2 deduplication rules), append them to the Site Map and To-Do Checklist in `00-sitemap-and-todo.md` as `[ ]`.
- Repeat **Step 3 through Step 5** until zero `[ ]` items remain.

### Step 6. Synthesize Cross-Page Data Lineage & Impact Map (`99-cross-page-relations.md`)
- Once all pages have been visited, cross-reference the **Produced Entities** and **Consumed Entities** across every generated `pages/<NN>-<page-slug>.md`:
  1. Trace **Producer → Consumer relationships**: When Screen A creates, edits, or changes the status of an entity (e.g., Product, Role, Category, Policy, User, Settlement Rule), identify every Screen B, C, D where that entity appears as a dropdown filter option, table column, reference field, access permission, or dashboard KPI metric.
  2. Generate `./explored-services/<service-slug>/99-cross-page-relations.md` containing:
     - **Data Propagation Flow Diagram** (ASCII diagram mapping how data flows between screens).
     - **Entity Producer → Consumer Impact Matrix** (Entity | Source Screen & CTA | Affected Target Screens | Exact UI/Business Impact).
  3. Update Section 5 (`Cross-Page Data Dependencies & Impact`) of each `pages/<NN>-<page-slug>.md` with bidirectional Markdown links between upstream producer pages and downstream consumer pages.

---

## 3. Optional Mode: Interactive HTML Visualization via Archify

When the user asks to **visualize the explored service** (e.g., *"이걸 기반으로 시각화 해줘"*, *"아키파이(Archify)로 시각화해서 저장해줘"*, or passes a visualization option):

1. **Load the Archify Skill**:
   - Read `~/.agents/skills/archify/SKILL.md` and its corresponding schema/example files in `~/.agents/skills/archify/schemas/` and `~/.agents/skills/archify/examples/`.
2. **Generate Interactive Standalone HTML Artifacts**:
   - Use the collected service specifications (`00-sitemap-and-todo.md`, `pages/*.md`, and `99-cross-page-relations.md`) as the source of truth to author validated Archify JSON candidates and render them via `node ~/.agents/skills/archify/bin/archify.mjs finalize <type> <candidate.json> <output.html> --quality showcase --json` into `./explored-services/<service-slug>/visualizations/`:
     - **Cross-Page Data Lineage (`dataflow` or `workflow`)**: `./explored-services/<service-slug>/visualizations/cross-page-dataflow.html` — maps how entities created on producer screens propagate into consumer screens (dropdowns, tables, KPIs, permissions).
     - **Service Site Map & Module Architecture (`architecture` or `tree`)**: `./explored-services/<service-slug>/visualizations/service-architecture.html` — maps the GNB/LNB hierarchy and module boundaries.
     - **One-Page Service Explainer (`explainer`, if requested)**: `./explored-services/<service-slug>/visualizations/service-explainer.html`.
3. **Link in Master Index**:
   - Add links to the generated `.html` files under the header of `./explored-services/<service-slug>/00-sitemap-and-todo.md` (and optionally open them in the Orca browser tab via `orca tab create --url "file:///..." --json` if the user wants to view them immediately).
