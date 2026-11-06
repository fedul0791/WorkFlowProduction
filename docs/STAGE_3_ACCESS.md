# Stage 3: employees, authentication and access control

## Initial setup

Start Docker Compose and run `docker compose exec backend python -m app.bootstrap`. This one-time interactive command creates the first company and Administrator account, or attaches the first Administrator to an existing Stage 2 company that has no accounts. It preserves existing structure data. Open registration is intentionally disabled. Administrators create subsequent accounts from the protected user-management API/UI.

## Authentication

Login and logout are `POST /api/v1/auth/login` and `POST /api/v1/auth/logout`; `GET /api/v1/auth/me` returns the current user, tenant, roles and permissions. The random session bearer is stored only as a SHA-256 digest in `user_sessions`; cookies are HttpOnly, SameSite=Strict, Secure outside development, and expire after 12 hours. A separate CSRF cookie must be echoed in `X-CSRF-Token` on state-changing requests. Passwords use salted scrypt hashes. There is no unauthenticated user-registration endpoint.

All routes except `/health`, login and OpenAPI infrastructure are authenticated. Stage 2 routes retain their paths, require `structure:read` or `structure:write`, and scope Company lookups to the authenticated user's tenant. Cross-tenant relationships use tenant-composite foreign keys.

## Roles and permissions

Per-tenant roles are seeded on bootstrap: Mitarbeiter (`employee`), Meister (`foreman`), Geschäftsführer (`director`) and Administrator (`administrator`). Users may have multiple roles; effective permissions are the union of role permissions. Permissions are persisted in `permissions` and `role_permissions`, checked by FastAPI dependencies on every protected endpoint, and can be updated by an administrator. Additional custom roles can be created by an administrator. The first Administrator is provisioned locally by CLI, never via an open web endpoint.

## Workforce model

Employees have full name, unique internal employee number, a home Site, active/archive state, and an optional linked User. Work at different sites and workstations is recorded separately in `employee_work_assignments`, with a validity period per assignment; each optional workstation is validated against the selected site. Existing `employees.site_id` remains the employee's home site for compatibility. Assignment history is read at `GET /api/v1/employees/{id}/work-assignments`, created at `POST` on that route, and its end date is maintained at `PATCH /api/v1/employee-work-assignments/{id}/period`.

Positions are associated with employees through time-bounded `employee_positions`. Qualifications are assigned through `employee_qualifications`, with status and optional expiry. Company settings control whether multiple current positions or qualifications are allowed. Equipment and operation authorizations have a validity interval and active/suspended/revoked status; expired authorizations are reported as expired.

Administrative writes record actor, tenant, entity, action, timestamp and before/after JSON in `audit_events`. Session revocation occurs when an account or linked employee is deactivated/archived.

## Local security boundary

Compose binds the frontend and API to loopback. Set `APP_ENV=production` only behind HTTPS so the Secure session cookies can be used. Production deployment should also supply TLS termination and operational login rate limiting; the local Compose development stack is not a production deployment.
