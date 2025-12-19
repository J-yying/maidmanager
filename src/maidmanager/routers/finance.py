from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_account

router = APIRouter(prefix="/api/finance", tags=["财务"])


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

        pkg_rows = (
            db.query(
                models.Order.package_id,
                models.Order.package_name,
                func.count(models.Order.id).label("cnt"),
                func.coalesce(func.sum(models.Order.total_amount), 0.0).label("amount"),
                func.coalesce(func.sum(models.Order.commission_amount), 0.0).label(
                    "commission"
                ),
            )
            .filter(
                models.Order.staff_id == staff.id,
                models.Order.status == "completed",
                models.Order.order_date.like(like_pattern),
                models.Order.owner == current_account["username"],
            )
            .group_by(models.Order.package_id, models.Order.package_name)
            .all()
        )
        package_stats: list[schemas.SalaryPackageStat] = []
        for row in pkg_rows:
            package_stats.append(
                schemas.SalaryPackageStat(
                    package_id=row.package_id,
                    package_name=row.package_name or "未指定套餐",
                    order_count=row.cnt,
                    total_amount=float(row.amount or 0.0),
                    total_commission=float(row.commission or 0.0),
                )
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
                packages=package_stats,
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


@router.get(
    "/attendance",
    response_model=schemas.AttendanceResponse,
    summary="员工出勤统计（排班 + 已完成订单）",
)
def get_attendance(
    month: str = Query(..., description="月份 YYYY-MM"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.AttendanceResponse:
    """按月汇总员工排班天数/时长，以及已完成订单数/时长。"""
    if len(month) != 7 or month[4] != "-":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="月份格式需为 YYYY-MM"
        )
    like_pattern = f"{month}-%"

    # 排班汇总
    shift_duration_hours = (
        (func.julianday(models.WorkShift.work_date + " " + models.WorkShift.end_time)
         - func.julianday(models.WorkShift.work_date + " " + models.WorkShift.start_time))
        * 24
    )
    shift_rows = (
        db.query(
            models.WorkShift.staff_id.label("staff_id"),
            func.count(func.distinct(models.WorkShift.work_date)).label("shift_days"),
            func.coalesce(func.sum(shift_duration_hours), 0).label("shift_hours"),
        )
        .filter(
            models.WorkShift.owner == current_account["username"],
            models.WorkShift.work_date.like(like_pattern),
        )
        .group_by(models.WorkShift.staff_id)
        .all()
    )
    shift_map = {
        row.staff_id: {
            "shift_days": row.shift_days,
            "shift_hours": float(row.shift_hours or 0),
        }
        for row in shift_rows
    }

    # 订单汇总（排除已取消，仅统计已完成）
    active_status = ("completed",)
    order_rows = (
        db.query(
            models.Order.staff_id.label("staff_id"),
            func.count(models.Order.id).label("cnt"),
            func.coalesce(
                func.sum(
                    func.coalesce(models.Order.booked_minutes, models.Order.duration_minutes, 0)
                ),
                0,
            ).label("order_minutes"),
        )
        .filter(
            models.Order.owner == current_account["username"],
            models.Order.status.in_(active_status),
            models.Order.order_date.like(like_pattern),
        )
        .group_by(models.Order.staff_id)
        .all()
    )
    order_map = {
        row.staff_id: {
            "count": row.cnt,
            "hours": float(row.order_minutes or 0) / 60.0,
        }
        for row in order_rows
    }

    # 员工名称映射
    staff_rows = (
        db.query(models.Staff.id, models.Staff.name)
        .filter(models.Staff.owner == current_account["username"])
        .all()
    )
    items: list[schemas.StaffAttendanceItem] = []
    for staff_id, staff_name in staff_rows:
        shift_info = shift_map.get(staff_id, {"shift_days": 0, "shift_hours": 0.0})
        order_info = order_map.get(staff_id, {"count": 0, "hours": 0.0})
        items.append(
            schemas.StaffAttendanceItem(
                staff_id=staff_id,
                staff_name=staff_name,
                shift_days=shift_info["shift_days"],
                shift_hours=shift_info["shift_hours"],
                completed_order_count=order_info["count"],
                completed_order_hours=order_info["hours"],
            )
        )

    return schemas.AttendanceResponse(month=month, items=items)


@router.get(
    "/roster_overview",
    response_model=schemas.RosterOverviewResponse,
    summary="排班概览（按月）",
)
def get_roster_overview(
    month: str = Query(..., description="月份 YYYY-MM"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.RosterOverviewResponse:
    """按月汇总排班总时长/天数/日均时长，并给出最早/最晚排班时间。"""
    if len(month) != 7 or month[4] != "-":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="月份格式需为 YYYY-MM"
        )
    like_pattern = f"{month}-%"
    active_status = ("pending", "in_progress", "finished", "completed")

    # 总时长、天数、最早/最晚
    shift_duration_hours = (
        (func.julianday(models.WorkShift.work_date + " " + models.WorkShift.end_time)
         - func.julianday(models.WorkShift.work_date + " " + models.WorkShift.start_time))
        * 24
    )
    rows = (
        db.query(
            func.coalesce(func.sum(shift_duration_hours), 0).label("total_hours"),
            func.count(func.distinct(models.WorkShift.work_date)).label("shift_days"),
            func.min(models.WorkShift.start_time).label("earliest"),
            func.max(models.WorkShift.end_time).label("latest"),
        )
        .filter(
            models.WorkShift.owner == current_account["username"],
            models.WorkShift.work_date.like(like_pattern),
        )
        .first()
    )
    total_hours = float(rows.total_hours or 0) if rows else 0.0
    shift_days = int(rows.shift_days or 0) if rows else 0
    avg_daily = total_hours / shift_days if shift_days else 0.0
    earliest = rows.earliest if rows and rows.earliest else None
    latest = rows.latest if rows and rows.latest else None

    pkg_minutes_sum = (
        db.query(
            func.coalesce(func.sum(func.coalesce(models.Order.booked_minutes, 0)), 0)
        )
        .filter(
            models.Order.owner == current_account["username"],
            models.Order.status.in_(active_status),
            models.Order.order_date.like(like_pattern),
        )
        .scalar()
    )
    package_hours = float(pkg_minutes_sum or 0) / 60.0

    return schemas.RosterOverviewResponse(
        month=month,
        total_shift_hours=total_hours,
        total_package_hours=package_hours,
        shift_days=shift_days,
        avg_daily_shift_hours=avg_daily,
        earliest_start=earliest,
        latest_end=latest,
    )
