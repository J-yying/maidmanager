from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_account

router = APIRouter(prefix="/api/finance", tags=["finance"])


def _validate_month(month: str) -> str:
    if len(month) != 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="month 必须是 YYYY-MM 格式",
        )
    year, dash, mon = month.partition("-")
    if dash != "-" or not year.isdigit() or not mon.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="month 必须是 YYYY-MM 格式",
        )
    return month


@router.get(
    "/salary_slip",
    response_model=schemas.SalarySlipResponse,
    summary="工资条列表",
)
def get_salary_slip(
    month: str = Query(..., description="月份 YYYY-MM"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.SalarySlipResponse:
    """按月生成所有员工的工资条汇总。"""
    month = _validate_month(month)
    like_pattern = f"{month}-%"

    staff_list: List[models.Staff] = (
        db.query(models.Staff)
        .filter(
            models.Staff.status == "active",
            models.Staff.owner == current_account["username"],
        )
        .order_by(models.Staff.id)
        .all()
    )

    items: List[schemas.SalaryItem] = []
    for staff in staff_list:
        commission_total = (
            db.query(func.coalesce(func.sum(models.Order.commission_amount), 0.0))
            .filter(
                models.Order.staff_id == staff.id,
                models.Order.status == "completed",
                models.Order.order_date.like(like_pattern),
                models.Order.owner == current_account["username"],
            )
            .scalar()
        )
        base_salary = staff.base_salary or 0.0
        total_salary = base_salary + float(commission_total or 0.0)
        items.append(
            schemas.SalaryItem(
                staff_id=staff.id,
                staff_name=staff.name,
                base_salary=base_salary,
                commission_total=float(commission_total or 0.0),
                total_salary=total_salary,
            )
        )

    return schemas.SalarySlipResponse(month=month, items=items)


@router.get(
    "/dashboard",
    response_model=schemas.FinanceDashboardResponse,
    summary="财务总览",
)
def get_finance_dashboard(
    month: str = Query(..., description="月份 YYYY-MM"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.FinanceDashboardResponse:
    """财务驾驶舱：营收、工资、支出与净利润。"""
    month = _validate_month(month)
    like_pattern = f"{month}-%"

    # 总营收
    total_revenue = (
        db.query(func.coalesce(func.sum(models.Order.total_amount), 0.0))
        .filter(
            models.Order.status == "completed",
            models.Order.order_date.like(like_pattern),
            models.Order.owner == current_account["username"],
        )
        .scalar()
    )

    # 总提成
    total_commission = (
        db.query(func.coalesce(func.sum(models.Order.commission_amount), 0.0))
        .filter(
            models.Order.status == "completed",
            models.Order.order_date.like(like_pattern),
            models.Order.owner == current_account["username"],
        )
        .scalar()
    )

    # 工资条（用于计算总底薪与应发工资）
    salary_slip = get_salary_slip(
        month=month, db=db, current_account=current_account
    )
    total_base_salary = float(
        sum(item.base_salary for item in salary_slip.items)
    )
    total_salary = float(sum(item.total_salary for item in salary_slip.items))

    # 其他支出
    total_expenses = (
        db.query(func.coalesce(func.sum(models.Expense.amount), 0.0))
        .filter(
            models.Expense.expense_date.like(like_pattern),
            models.Expense.owner == current_account["username"],
        )
        .scalar()
    )

    net_profit = float(total_revenue or 0.0) - float(total_salary or 0.0) - float(
        total_expenses or 0.0
    )

    return schemas.FinanceDashboardResponse(
        month=month,
        total_revenue=float(total_revenue or 0.0),
        total_commission=float(total_commission or 0.0),
        total_base_salary=total_base_salary,
        total_salary=total_salary,
        total_expenses=float(total_expenses or 0.0),
        net_profit=net_profit,
    )
