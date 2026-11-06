# Enterprise structure (Stage 2)

## Data model

The company UUID is also its tenant UUID (`companies.id = companies.tenant_id`). Each child table stores `tenant_id`; composite foreign keys bind departments to sites, areas to departments, workstations to areas, and assignments to equipment/workstations belonging to the same tenant. Records are archived using `archived_at`; no DELETE endpoint is exposed.

Equipment is tenant-owned independently of its workstation assignments. `equipment_assignments` retains each validity period (`valid_from`, `valid_to`) and permits at most one open assignment per piece of equipment. Audit records are written in the same transaction as create, edit, move, archive, and assignment changes. `actor_id` remains null until identity/authentication exists.

## API

Base URL: `/api/v1`

- `GET/POST /companies`
- `GET /companies/{company_id}/structure`
- `PATCH /companies/{company_id}` and `POST /companies/{company_id}/archive`
- `POST /companies/{company_id}/nodes/{site|department|area|workstation}`
- `PATCH /companies/{company_id}/nodes/{kind}/{id}`
- `POST /companies/{company_id}/nodes/{kind}/{id}/move`
- `POST /companies/{company_id}/nodes/{kind}/{id}/archive`
- `POST /companies/{company_id}/equipment`
- `GET/PATCH /companies/{company_id}/equipment/{equipment_id}`
- `POST /companies/{company_id}/equipment/{equipment_id}/assignments`
- `POST /companies/{company_id}/equipment/{equipment_id}/assignments/close` (end current assignment)
- `POST /companies/{company_id}/equipment/{equipment_id}/archive`

A move requires a parent of the one allowed type and tenant. Archiving a parent with active children returns HTTP 409; archive descendants first. Equipment with an open assignment must be unassigned/reassigned before it can be archived.

## UI

The three localized pages are `/de/betrieb`, `/ru/betrieb`, and `/en/betrieb`. The UI calls the API; it has no browser-only structure store or seeded sample records. The tree displays active structure and currently assigned equipment. Equipment detail shows its assignment history. The interface currently has no user authentication/authorization; only use the local development binding until access control is added.
