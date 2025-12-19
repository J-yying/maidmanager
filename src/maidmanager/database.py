import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = "sqlite:///./maid_system.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库表结构。"""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_owner_columns()
    _ensure_booked_minutes()
    _dedupe_work_shifts()
    _ensure_indexes()
    _refresh_commission_snapshot()
    _refresh_commission_snapshot()


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    for row in result:
        # PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
        if row[1] == column_name:
            return True
    return False


def _ensure_owner_columns() -> None:
    """为老库补充 owner 字段，用于账号隔离。"""
    tables = [
        "staff",
        "work_shifts",
        "orders",
        "expenses",
        "service_packages",
        "staff_package_commissions",
    ]
    with engine.begin() as conn:
        for table in tables:
            if not _column_exists(conn, table, "owner"):
                conn.execute(
                    text(
                        f"ALTER TABLE {table} "
                        "ADD COLUMN owner VARCHAR NOT NULL DEFAULT 'manager'"
                    )
                )


def _ensure_booked_minutes() -> None:
    """为订单增加 booked_minutes/extension_package_ids 字段，并回填。"""
    with engine.begin() as conn:
        if not _column_exists(conn, "orders", "booked_minutes"):
            conn.execute(
                text(
                    "ALTER TABLE orders "
                    "ADD COLUMN booked_minutes INTEGER NOT NULL DEFAULT 0"
                )
            )
        if not _column_exists(conn, "orders", "extension_package_ids"):
            conn.execute(
                text(
                    "ALTER TABLE orders "
                    "ADD COLUMN extension_package_ids VARCHAR"
                )
            )
        # 回填：若 booked_minutes 为空或 0，则用套餐时长；无套餐则置 0（不再使用 duration_minutes）
        conn.execute(
            text(
                """
                UPDATE orders
                SET booked_minutes = CASE
                    WHEN booked_minutes IS NULL OR booked_minutes = 0 THEN
                        COALESCE(
                            (SELECT duration_minutes FROM service_packages sp WHERE sp.id = orders.package_id),
                            0
                        )
                    ELSE booked_minutes
                END
                """
            )
        )


def _refresh_commission_snapshot() -> None:
    """旧数据提成快照重算：基础套餐 + 续钟套餐累加。"""
    from . import models  # noqa: WPS433

    session = SessionLocal()
    try:
        orders = (
            session.query(models.Order)
            .filter(models.Order.status != "cancelled")
            .all()
        )

        def calc_commission(pkg: models.ServicePackage, staff: models.Staff, owner: str) -> float:
            if pkg is None or staff is None:
                return 0.0
            if staff.commission_type == "percentage":
                base_amount = pkg.price or 0.0
                return base_amount * (staff.commission_value or 0.0)
            if staff.commission_type == "fixed":
                mapping = (
                    session.query(models.StaffPackageCommission)
                    .filter(
                        models.StaffPackageCommission.staff_id == staff.id,
                        models.StaffPackageCommission.package_id == pkg.id,
                        models.StaffPackageCommission.owner == owner,
                    )
                    .first()
                )
                if mapping:
                    return mapping.commission_amount or 0.0
                return pkg.default_commission or 0.0
            return 0.0

        for order in orders:
            staff = (
                session.query(models.Staff)
                .filter(
                    models.Staff.id == order.staff_id,
                    models.Staff.owner == order.owner,
                )
                .first()
            )
            if not staff:
                continue
            base_pkg = (
                session.query(models.ServicePackage)
                .filter(
                    models.ServicePackage.id == order.package_id,
                    models.ServicePackage.owner == order.owner,
                )
                .first()
                if order.package_id
                else None
            )
            commission_total = calc_commission(base_pkg, staff, order.owner)

            ext_ids: list[int] = []
            if order.extension_package_ids:
                try:
                    parsed = json.loads(order.extension_package_ids)
                    if isinstance(parsed, list):
                        ext_ids = [int(v) for v in parsed if isinstance(v, (int, str)) and str(v).isdigit()]
                except Exception:
                    ext_ids = []
            if ext_ids:
                ext_pkgs = (
                    session.query(models.ServicePackage)
                    .filter(
                        models.ServicePackage.id.in_(ext_ids),
                        models.ServicePackage.owner == order.owner,
                    )
                    .all()
                )
                ext_map = {p.id: p for p in ext_pkgs}
                for ext_id in ext_ids:
                    pkg = ext_map.get(ext_id)
                    if pkg:
                        commission_total += calc_commission(pkg, staff, order.owner)

            order.commission_amount = float(commission_total or 0.0)

        session.commit()
    finally:
        session.close()


def _refresh_commission_snapshot() -> None:
    """旧数据提成快照重算为基础套餐+续钟套餐提成累加。"""
    with engine.begin() as conn:
        # 填充缺失的续钟列表字段
        conn.execute(
            text(
                "UPDATE orders SET extension_package_ids = '[]' "
                "WHERE extension_package_ids IS NULL"
            )
        )


def _dedupe_work_shifts() -> None:
    """剔除同一天同一员工的重复排班（保留最早一条）。"""
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, staff_id, work_date, owner "
                "FROM work_shifts ORDER BY id"
            )
        ).fetchall()
        seen: set[tuple[int, str, str]] = set()
        dup_ids: list[int] = []
        for row in rows:
            key = (row.staff_id, row.work_date, row.owner)
            if key in seen:
                dup_ids.append(row.id)
            else:
                seen.add(key)
        if dup_ids:
            _delete_ids(conn, "work_shifts", dup_ids)


def _delete_ids(conn, table: str, ids: list[int]) -> None:
    if not ids:
        return
    placeholders = ", ".join(f":id{i}" for i in range(len(ids)))
    params = {f"id{i}": val for i, val in enumerate(ids)}
    conn.execute(text(f"DELETE FROM {table} WHERE id IN ({placeholders})"), params)


def _ensure_indexes() -> None:
    """创建必要的唯一索引。"""
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "idx_work_shifts_owner_day_staff "
                "ON work_shifts (owner, work_date, staff_id)"
            )
        )
