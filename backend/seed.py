"""
Phase 2 seed — demo data (ready state for the SIH demo).

Run (from backend folder):
    alembic upgrade head
    python seed.py
    python seed.py --reset    # drop + recreate tables + seed
"""
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from argon2 import PasswordHasher
from sqlalchemy import select

from app.core.db import Base, SessionLocal, engine
from app.engine.ruleset import load_ruleset
from app.models import (
    AuditLog, Equipment, Evaluation, EvaluationEquipment, Instrument,
    InstrumentRange, Laboratory, Party, Ruleset, User,
)

ph = PasswordHasher()


def reset_db() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print(">> Tables drop + recreate ho gaye")


def seed() -> None:
    rs = load_ruleset()

    with SessionLocal() as db:
        # 1. Ruleset record (with the JSON document, sha256 integrity)
        db.add(Ruleset(id=rs["_id"], title=rs["title"],
                       sha256=rs["_sha256"], document=rs, is_active=True))

        # 2. Laboratory
        lab = Laboratory(
            name="Regional Reference Standards Laboratory (Demo)",
            address="Metrology Bhawan, New Delhi",
            accreditation_no="NABL-DEMO-0001",
        )
        db.add(lab)

        # 3. Users — one per role (Phase 4 login demo ready)
        users = {
            "admin": User(username="admin", full_name="System Administrator",
                          email="admin@lab.gov.in", role="ADMIN",
                          password_hash=ph.hash("Admin@123")),
            "engineer": User(username="engineer", full_name="Test Engineer",
                             email="engineer@lab.gov.in", role="ENGINEER",
                             password_hash=ph.hash("Engineer@123")),
            "reviewer": User(username="reviewer", full_name="Senior Metrologist",
                             email="reviewer@lab.gov.in", role="REVIEWER",
                             password_hash=ph.hash("Reviewer@123")),
            "viewer": User(username="viewer", full_name="Trainee Viewer",
                           email="viewer@lab.gov.in", role="VIEWER",
                           password_hash=ph.hash("Viewer@123")),
        }
        db.add_all(users.values())
        db.flush()   # assign ids (Python-side uuid default applies on flush)

        # 4. Manufacturer party
        acme = Party(kind="MANUFACTURER", name="Acme Scales Pvt. Ltd.",
                     address="Industrial Area Phase-2, Faridabad, Haryana",
                     gstin="06AACCA1234A1Z5", contact="+91-98100-00000",
                     email="quality@acmescales.example")
        db.add(acme)
        db.flush()

        # 5. Demo instrument — Class III platform scale
        #    Max 15 kg, Min 0.1 kg, e = d = 5 g  (n = 3000, Table 3 ✓)
        inst = Instrument(
            application_no="MA/2026/00001",
            type_designation="PS-15K-DEMO",
            manufacturer_id=acme.id,
            applicant_id=acme.id,
            category="Platform scale",
            accuracy_class="III",
            indication_type="SELF",
            display_kind="DIGITAL",
            range_kind="SINGLE",
            min_capacity=Decimal("0.1"),
            unit="kg",
            tare_plus=Decimal("0"),
            tare_minus=Decimal("-0.1"),
            max_safe_load=Decimal("20"),
            u_nom=Decimal("230"), u_min=Decimal("195.5"), u_max=Decimal("253"),
            frequency_hz=Decimal("50"),
            power_supply_category=["MAINS_AC"],
            zero_devices={"non_automatic": True, "semi_automatic": True,
                          "automatic": False, "initial": True,
                          "tracking": True, "zero_indicating": True},
            initial_zero_range_pct=Decimal("4"),
            tare_devices={"subtractive": True, "additive": False,
                          "semi_auto": True, "auto": False},
            temp_min_c=Decimal("-10"), temp_max_c=Decimal("40"),
            level_indicator=True,
            printer="NOT_PRESENT_CONNECTABLE",
            software_version="FW-1.2.3",
            submitted_identification_no="SN-DEMO-0001",
            created_by=users["admin"].id,
        )
        db.add(inst)
        db.flush()

        db.add(InstrumentRange(instrument_id=inst.id, idx=1,
                               e=Decimal("0.005"), d=Decimal("0.005"),
                               max_capacity=Decimal("15")))

        # 6. Evaluation (DRAFT) — test entries will be added here in Phase 5/7
        ev = Evaluation(
            report_no="LM/NAWI/2026/0001",
            instrument_id=inst.id,
            laboratory_id=lab.id,
            ruleset_id=rs["_id"],
            ruleset_sha256=rs["_sha256"],
            purpose="TYPE_APPROVAL",
            mpe_context="INITIAL",
            status="DRAFT",
            observer_id=users["engineer"].id,
            created_by=users["admin"].id,
            resolution_during_test=Decimal("0.001"),   # 1 g resolution during test
            auto_zero_status="IN_OPERATION",
        )
        db.add(ev)
        db.flush()

        # 7. Test equipment (traceability)
        weights = Equipment(kind="WEIGHT_SET", name="M1 Class Test Weight Set",
                            model="WT-M1-25kg", serial_no="M1-2026-001",
                            accuracy_class_or_uncertainty="M1",
                            cert_no="NABL-CERT-0001",
                            calibrated_on=date(2026, 1, 15),
                            valid_until=date(2027, 1, 14))
        thermo = Equipment(kind="THERMOMETER", name="Digital Thermometer",
                           serial_no="TH-2026-007",
                           accuracy_class_or_uncertainty="U=0.1 C",
                           cert_no="NABL-CERT-0002",
                           calibrated_on=date(2026, 2, 1),
                           valid_until=date(2027, 1, 31))
        db.add_all([weights, thermo])
        db.flush()
        db.add_all([
            EvaluationEquipment(evaluation_id=ev.id, equipment_id=weights.id),
            EvaluationEquipment(evaluation_id=ev.id, equipment_id=thermo.id),
        ])

        # 8. Audit entry
        db.add(AuditLog(user_id=users["admin"].id, action="SEED",
                        entity="evaluation", entity_id=str(ev.id),
                        after={"report_no": ev.report_no}))

        db.commit()

        print("\n================ SEED COMPLETE ================")
        print("Users     : admin/Admin@123 | engineer/Engineer@123 | "
              "reviewer/Reviewer@123 | viewer/Viewer@123")
        print(f"Laboratory: {lab.name} (id={lab.id})")
        print(f"Instrument: {inst.type_designation} Class III, Max 15 kg, e=5 g "
              f"(id={inst.id})")
        print(f"Evaluation: {ev.report_no} [{ev.status}] (id={ev.id})")
        print("Ruleset   : oiml-r76-2006 (sha256 stored)")
        print("===============================================\n")


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_db()
    seed()