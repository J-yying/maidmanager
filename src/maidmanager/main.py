from fastapi import FastAPI

from .database import init_db
from .routers import (
    auth,
    expenses,
    finance,
    orders,
    packages,
    roster,
    staff,
    staff_commissions,
)

app = FastAPI(
    title="MaidManager API",
    description="女仆店内部管理系统后端（MVP 版本）。",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    # 启动时自动创建 SQLite 表结构
    init_db()


app.include_router(auth.router)
app.include_router(staff.router)
app.include_router(staff_commissions.router)
app.include_router(roster.router)
app.include_router(orders.router)
app.include_router(finance.router)
app.include_router(expenses.router)
app.include_router(packages.router)
