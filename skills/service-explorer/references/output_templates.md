# Service Explorer Output Structure & Templates

Store all exploration outputs in `~/docsspace/<project-slug>/explored-services/<service-slug>/` (inside the private Obsidian Vault `~/docsspace/`) and always register the entry in `~/docsspace/<project-slug>/00_SSOT_INDEX.md` and `~/docsspace/00_INDEX.md`.

## 1. Directory & File Structure

```text
explored-services/
└── <service-slug>/                      # e.g., admin-portal, billing-console
    ├── 00-sitemap-and-todo.md           # Master index: Site Map + Coverage To-Do Checklist + Summary
    ├── 99-cross-page-relations.md       # Service-wide Data Lineage, Entity Producer/Consumer Matrix & Flow
    ├── pages/                           # Per-page functional specifications
    │   ├── 01-dashboard.md
    │   ├── 02-user-management-list.md
    │   └── 03-role-permissions.md
    └── assets/
        └── screenshots/                 # Captured screenshots named identically to page specs
            ├── 01-dashboard.jpg
            ├── 02-user-management-list.jpg
            └── 03-role-permissions.jpg
    └── visualizations/                  # [Optional: Archify Mode] Standalone interactive HTML diagrams
        ├── service-architecture.html    # Site hierarchy / module architecture (archify architecture/tree)
        └── cross-page-dataflow.html     # Producer -> Consumer data impact flow (archify dataflow/workflow)
```

---

## 2. Master Index Template (`00-sitemap-and-todo.md`)

Create this file during **Step 1 & Step 2**, update To-Do statuses incrementally during **Step 5**, and link `99-cross-page-relations.md` in **Step 6**.

```markdown
# [Service Name] Service Exploration Report

- **Base URL**: `https://...`
- **Explored At**: `YYYY-MM-DD HH:mm`
- **Coverage Summary**: Total `N` views (`X` analyzed, `Y` skipped/unreachable)
- **Cross-Page Data & Impact Map**: [99-cross-page-relations.md](./99-cross-page-relations.md)

---

## 1. Site Map (Navigation Hierarchy)

```text
[Service Root] (https://...)
├── 1. Dashboard (/dashboard)
├── 2. User Management
│   ├── 2.1 User List (/users)
│   └── 2.2 Role & Permissions (/users/roles)
└── 3. Settings (/settings)
```

---

## 2. Exploration To-Do & Coverage Checklist

- [x] **1. Dashboard** (`/dashboard`) → [Spec](./pages/01-dashboard.md)
- [x] **2.1 User List** (`/users`) → [Spec](./pages/02-user-management-list.md)
- [x] **2.2 Role & Permissions** (`/users/roles`) → [Spec](./pages/03-role-permissions.md)
- [!] **2.1.1 User Detail Row #2+** (`/users/:id`) — **Reason**: `Duplicate template of /users/1`
```

---

## 3. Per-Page Functional Spec Template (`pages/<NN>-<slug>.md`)

Create one file per visited page during **Step 3**, and finalize Section 5 (`Cross-Page Data Dependencies & Impact`) after cross-referencing all pages in **Step 6**.

```markdown
# [NN]. [Page / Menu Title]

- **URL / Route**: `https://...` (or `SPA View: GNB > Menu > Tab`)
- **Navigation Path**: `GNB > Parent Menu > Current Page`
- **Screenshot**: ![Screenshot](../assets/screenshots/<NN>-<slug>.jpg)

---

## 1. Page Purpose & Role (Inferred)
- **Primary Function**: Concise explanation of what business/operational problem this screen solves and who uses it.
- **Layout Structure**: Brief visual breakdown (e.g., Top KPI summary cards + Middle search filter bar + Bottom paginated data table).

---

## 2. Data Views & Display Components
| Section / Component | Type (Table / Card / Chart / Tab) | Displayed Fields / Columns / Metrics |
| :--- | :--- | :--- |
| Summary Header | KPI Cards (4) | Total Users, Active Today, Pending Approval, Suspended |
| Main List | Data Table | `ID`, `Name`, `Email`, `Role`, `Status`, `Created At`, `Actions` |

---

## 3. Input Fields & Filters
| Field / Filter Label | Input Type | Options / Placeholder / Validation Clues | Inferred Usage |
| :--- | :--- | :--- | :--- |
| Search | Text Input | Placeholder: `"Search by name or email"` | Filters main table by keyword |
| Role | Dropdown (`<select>`) | `All`, `Admin`, `Editor`, `Viewer` | Filters rows by user role |

---

## 4. Buttons & CTAs (Inferred Behavior — Not Clicked)
| Button / CTA Label | Visual Style / Location | Inferred Action & Side Effect |
| :--- | :--- | :--- |
| `+ Invite User` | Primary (Top-right blue button) | Opens a modal or form to create/invite a new User entity |
| `Export CSV` | Secondary (Above table, right) | Downloads currently filtered table rows as a `.csv` file |
| `Deactivate` | Danger (Table row button) | Changes User `Status` to `Suspended/Deactivated` |

---

## 5. Cross-Page Data Dependencies & Impact (Upstream & Downstream)
- **Upstream Inputs (Where data displayed/selectable on this page originates)**:
  - `Role` dropdown options & table column ← Produced/configured in **[03. Role & Permissions](./03-role-permissions.md)** (`/users/roles`).
- **Downstream Impact (Where data created/modified on this page affects other screens)**:
  - Creating/inviting a user via `+ Invite User` or changing `Status` via `Deactivate` →
    1. Updates `Total Users` / `Active Today` / `Suspended` KPI counters in **[01. Dashboard](./01-dashboard.md)** (`/dashboard`).
    2. Populates selectable assignee/owner lists in downstream operational screens.
```

---

## 4. Cross-Page Data Lineage & Impact Report Template (`99-cross-page-relations.md`)

Generate this file in **Step 6** once all To-Do pages have been inspected. Synthesize how data created or configured in one screen propagates across the entire service.

```markdown
# [Service Name] Cross-Page Data Lineage & Impact Map

## 1. Data Propagation Flow Diagram

```text
[03. Role & Permissions (/users/roles)]
  │  (Creates/updates Role definitions & access scopes)
  ▼
[02. User List (/users)]
  │  • Consumes `Role` in filter dropdown & user assignment
  │  • Produces `User` records & `Status` (Active / Suspended)
  ├─────────────────────────────────────────┐
  ▼                                         ▼
[01. Dashboard (/dashboard)]        [04. Audit / Activity Logs]
  • Aggregates `Total/Active Users`   • Records user creation & status changes
```

---

## 2. Entity Producer → Consumer Impact Matrix

| Domain Entity / Data | Producer / Source Screen (Create / Update) | Trigger / Field on Source | Affected Consumer Screen(s) | Exact Impact Mechanism (How it affects the target screen) |
| :--- | :--- | :--- | :--- | :--- |
| **Role** | [03. Role & Permissions](./pages/03-role-permissions.md) | `+ Create Role`, Permission checkboxes | [02. User List](./pages/02-user-management-list.md) | Populates `Role` filter dropdown options and determines GNB/LNB menu visibility for assigned users |
| **User Account & Status** | [02. User List](./pages/02-user-management-list.md) | `+ Invite User`, `Deactivate` CTA | [01. Dashboard](./pages/01-dashboard.md) | Increments/decrements `Total Users`, `Pending Approval`, and `Suspended` KPI summary cards |
```
