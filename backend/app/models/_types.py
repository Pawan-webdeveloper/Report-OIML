"""
Cross-database type helpers — support for Golden Design Rule #4.

Dev DB = SQLite, Prod DB = PostgreSQL. Doc §4 PG-specific types are portable here:

| Doc (PostgreSQL) | Here                                                   |
|------------------|--------------------------------------------------------|
| UUID             | sa.Uuid (SQLite: CHAR(32), PG: native UUID)            |
| JSONB            | sa.JSON → JSONB variant on PG                          |
| NUMERIC          | ExactNumeric (SQLite: EXACT text, PG: NUMERIC(18,6))   |
| TIMESTAMPTZ      | sa.DateTime(timezone=True)                             |
| TEXT[]           | JSON list (SQLite has no arrays)                       |

Why ExactNumeric: SQLite's native NUMERIC is float inside — high-precision
Decimals get corrupted by a float round-trip. So on SQLite we store an EXACT
STRING and convert back to Decimal. Bonus: if a float sneaks in, TypeError —
the bug is caught at insert time.
"""
from sqlalchemy import JSON, Numeric, String, TypeDecorator, Uuid
from sqlalchemy.dialects.postgresql import JSONB

from ..engine.units import dec

UUIDType = Uuid()                       # for PK/FK columns
JSONType = JSON().with_variant(JSONB(), "postgresql")


class ExactNumeric(TypeDecorator):
    """Decimal-safe numeric column. SQLite: exact string | PG: NUMERIC."""

    impl = String
    cache_ok = True

    def __init__(self, precision: int = 18, scale: int = 6):
        super().__init__()
        self.precision = precision
        self.scale = scale

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Numeric(self.precision, self.scale))
        return dialect.type_descriptor(String(40))   # exact decimal text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(dec(value))       # float aaya to yahin TypeError (guardrail!)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return dec(value)