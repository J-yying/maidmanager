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
    _dedupe_work_shifts()
    _ensure_indexes()


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
