# Alembic Migration Discipline

## Historical limitation

Revisions `0001`, `0002`, `0003`, `0004` and `0006` call current SQLAlchemy metadata through `create_all`. This couples a fresh historical replay to today's ORM definitions. These revisions are preserved because rewriting deployed migration history is riskier than documenting it.

Revision `0007` is the transition point. Its conditional guards support both a database genuinely at `0006` and a fresh replay where historical metadata has already created current objects.

## Rule for all migrations after `0007`

Future revisions must be explicit and reviewable. Use only targeted Alembic operations such as:

- `op.create_table`
- `op.add_column` / `op.drop_column`
- `op.alter_column`
- `op.create_index` / `op.drop_index`
- `op.create_foreign_key`
- bounded data migrations with parameterized SQL

Do not import ORM model metadata and do not call `Base.metadata.create_all/drop_all` in a new revision. Every revision needs an intentional downgrade or an explicit explanation when downgrade is impossible.

## Validation

Before merge:

1. Upgrade an empty database to `head`.
2. Upgrade a schema at the previous head to the new revision.
3. Compare ORM metadata and database schema.
4. Run PostgreSQL-specific checks on PostgreSQL 16 for GIN, generated columns, JSON expressions, advisory locks and query plans.
5. Use SQLite only for portable migration/unit feedback; it is not proof of PostgreSQL behavior.

Phase 3.5 validated both fresh and simulated-existing paths through `0007` on SQLite. PostgreSQL execution remains blocked in this environment.
