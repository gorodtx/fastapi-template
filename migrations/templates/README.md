# Roles Migration Template

1. Create a new alembic revision:
   - `uv run alembic revision -m "add <role> role"`
2. Copy `migrations/templates/roles_permissions_template.py` into the new revision.
3. Fill:
   - `revision`
   - `down_revision`
   - `NEW_ROLES`
   - optional `ROLE_DESCRIPTIONS`
   - optional `ROLE_USER_BINDINGS`
4. Apply:
   - `uv run alembic upgrade head`

The template is idempotent:
- re-running upgrade keeps role/permission state synchronized
- downgrade removes only roles declared in `NEW_ROLES`
