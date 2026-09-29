"""
Phase 2 smoke tests — data layer (doc §4 → SQLite/PG portable models).

These prove that:
1. All 15 tables of doc §4 are created
2. A full graph insert (party→instrument→ranges→evaluation→test_record) works
3. ExactNumeric returns Decimal — high precision stays EXACT (no float leak)
4. CHECK constraints are enforced (bad role/verdict → IntegrityError)
5. UNIQUE (evaluation_id, kind, instance_no) is enforced
6. ORM cascade delete works
7. DB→Engine bridge: mpe('12 kg') == 7.5 g with ranges loaded from the DB
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.engine.classification import build_instrument
from app.engine.mpe import mpe
from app.engine.ruleset import load_ruleset
from app.engine.units import to_base
from app.models import (
    AuditLog, Evaluation, Instrument, InstrumentRange, Laboratory,
    Ruleset, TestRecord, User,
)

EXPECTED_TABLES = {
    "users", "laboratories", "parties", "instruments", "instrument_ranges",
    "evaluations", "equipment", "evaluation_equipment", "checklist_results",
    "test_records", "attachments", "reviews", "report_exports", "rulesets",
    "audit_log",
}


@pytest.fixture()
def db():
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    with Session(eng) as session:
        yield session


def _mk_instrument(db: Session) -> Instrument:
    inst = Instrument(
        type_designation="PS-15K", accuracy_class="III", indication_type="SELF",
        display_kind="DIGITAL", range_kind="SINGLE",
        min_capacity=Decimal("0.1"), unit="kg",
        temp_min_c=Decimal("-10"), temp_max_c=Decimal("40"),
        power_supply_category=["MAINS_AC"],
    )
    db.add(inst)
    db.flush()
    db.add(InstrumentRange(instrument_id=inst.id, idx=1,
                           e=Decimal("0.005"), d=Decimal("0.005"),
                           max_capacity=Decimal("15")))
    db.flush()
    return inst


class TestSchema:
    def test_all_doc_tables_created(self):
        assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES


class TestInsertGraph:
    def test_full_graph(self, db):
        rs = load_ruleset()
        lab = Laboratory(name="Demo Lab")
        user = User(username="eng1", full_name="E", email="e@x.in",
                    password_hash="x", role="ENGINEER")
        db.add_all([lab, user])
        db.flush()

        inst = _mk_instrument(db)
        ev = Evaluation(report_no="LM/NAWI/2026/0001",
                        instrument_id=inst.id, laboratory_id=lab.id,
                        ruleset_id=rs["_id"], ruleset_sha256=rs["_sha256"],
                        purpose="TYPE_APPROVAL", mpe_context="INITIAL",
                        status="IN_PROGRESS", observer_id=user.id,
                        created_by=user.id)
        db.add(ev)
        db.flush()

        db.add(TestRecord(
            evaluation_id=ev.id, kind="WEIGHING", form_no="1", instance_no=1,
            condition_label="Initial 20 C", test_date=date(2026, 10, 1),
            environment={"start": {"temp": 20.4, "rh": 51}},
            observations={
                "zero": {"L": "0.02", "I": "0.020", "dL": "1.0"},
                "points": [{"L": "12", "up": {"I": "12.005", "dL": "1.4"}}],
            },
            verdict="PASSED"))
        db.commit()

        got = db.scalar(select(TestRecord).where(TestRecord.kind == "WEIGHING"))
        assert got.evaluation_id == ev.id
        assert got.observations["zero"]["I"] == "0.020"
        assert got.evaluation.report_no == "LM/NAWI/2026/0001"


class TestExactNumeric:
    def test_returns_decimal_not_float(self, db):
        _mk_instrument(db)
        rng = db.scalar(select(InstrumentRange))
        assert isinstance(rng.e, Decimal)
        assert rng.e == Decimal("0.005")
        assert isinstance(rng.max_capacity, Decimal)
        assert rng.max_capacity == Decimal("15")

    def test_high_precision_exact(self, db):
        # float(0.1234567890123456789) → 0.12345678901234568 (18th digit gets corrupted)
        # ExactNumeric string storage returns it back EXACT
        inst = Instrument(type_designation="HP", accuracy_class="I",
                          indication_type="SELF", range_kind="SINGLE",
                          min_capacity="0.000001", unit="g")
        db.add(inst)
        db.flush()
        db.add(InstrumentRange(instrument_id=inst.id, idx=1,
                               e="0.1234567890123456789",
                               d="0.1234567890123456789",
                               max_capacity="12345678.90123456789"))
        db.flush()
        rng = db.scalar(select(InstrumentRange)
                        .where(InstrumentRange.instrument_id == inst.id))
        assert rng.e == Decimal("0.1234567890123456789")
        assert rng.max_capacity == Decimal("12345678.90123456789")


class TestConstraints:
    def test_bad_role_rejected(self, db):
        db.add(User(username="x", full_name="X", email="x@x.in",
                    password_hash="h", role="SUPERGOD"))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

    def test_bad_verdict_rejected(self, db):
        rs = load_ruleset()
        lab = Laboratory(name="L")
        db.add(lab)
        db.flush()
        inst = _mk_instrument(db)
        ev = Evaluation(report_no="R1", instrument_id=inst.id,
                        laboratory_id=lab.id, ruleset_id=rs["_id"],
                        ruleset_sha256=rs["_sha256"], purpose="TYPE_APPROVAL")
        db.add(ev)
        db.flush()
        db.add(TestRecord(evaluation_id=ev.id, kind="WEIGHING",
                          observations={}, verdict="MAYBE"))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

    def test_duplicate_test_page_rejected(self, db):
        rs = load_ruleset()
        lab = Laboratory(name="L")
        db.add(lab)
        db.flush()
        inst = _mk_instrument(db)
        ev = Evaluation(report_no="R2", instrument_id=inst.id,
                        laboratory_id=lab.id, ruleset_id=rs["_id"],
                        ruleset_sha256=rs["_sha256"], purpose="TYPE_APPROVAL")
        db.add(ev)
        db.flush()
        db.add(TestRecord(evaluation_id=ev.id, kind="WEIGHING",
                          instance_no=1, observations={}))
        db.flush()
        db.add(TestRecord(evaluation_id=ev.id, kind="WEIGHING",
                          instance_no=1, observations={}))   # same page!
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()


class TestCascade:
    def test_orm_cascade_deletes_test_records(self, db):
        rs = load_ruleset()
        lab = Laboratory(name="L")
        db.add(lab)
        db.flush()
        inst = _mk_instrument(db)
        ev = Evaluation(report_no="R3", instrument_id=inst.id,
                        laboratory_id=lab.id, ruleset_id=rs["_id"],
                        ruleset_sha256=rs["_sha256"], purpose="TYPE_APPROVAL")
        db.add(ev)
        db.flush()
        db.add(TestRecord(evaluation_id=ev.id, kind="WEIGHING", observations={}))
        db.add(TestRecord(evaluation_id=ev.id, kind="ECC_WEIGHTS", observations={}))
        db.commit()

        db.delete(ev)
        db.commit()
        assert db.scalar(select(func.count()).select_from(TestRecord)) == 0


class TestDbToEngineBridge:
    def test_mpe_from_db_loaded_instrument(self, db):
        _mk_instrument(db)
        inst_db = db.scalar(select(Instrument)
                            .where(Instrument.type_designation == "PS-15K"))
        r = inst_db.ranges[0]   # Decimal values in kg (declared unit)
        engine_inst = build_instrument(
            inst_db.accuracy_class, str(inst_db.min_capacity), inst_db.unit,
            [{"e": str(r.e), "d": str(r.d), "max": str(r.max_capacity)}],
        )
        # engine expects base unit (g): 12 kg → 12000 g → 2400 e → 1.5e = 7.5 g
        load_g = to_base("12", inst_db.unit)
        assert mpe(load_ruleset(), engine_inst, load_g) == Decimal("7.5")


class TestRulesetAndAudit:
    def test_ruleset_row(self, db):
        rs = load_ruleset()
        db.add(Ruleset(id=rs["_id"], title=rs["title"],
                       sha256=rs["_sha256"], document=rs))
        db.commit()
        row = db.get(Ruleset, "oiml-r76-2006")
        assert row.is_active is True
        assert row.document["mpe_bands"]["III"][0]["mult"] == "0.5"

    def test_audit_autoincrement(self, db):
        db.add_all([AuditLog(action="A"), AuditLog(action="B")])
        db.commit()
        rows = db.scalars(select(AuditLog)).all()
        assert [r.id for r in rows] == [1, 2]