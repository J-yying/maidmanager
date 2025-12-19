import json
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_account

router = APIRouter(prefix="/api", tags=["订单"])


def _parse_dt(raw: str) -> datetime:
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="时间格式必须为 YYYY-MM-DD HH:MM:ss",
        ) from exc


def _calc_commission_for_package(
    pkg: Optional[models.ServicePackage],
    staff: models.Staff,
    owner: str,
    db: Session,
) -> float:
    if pkg is None:
        return 0.0

    if staff.commission_type == "percentage":
        base_amount = pkg.price or 0.0
        return base_amount * (staff.commission_value or 0.0)

    if staff.commission_type == "fixed":
        mapping = (
            db.query(models.StaffPackageCommission)
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


@router.get(
    "/orders/day_view",
    response_model=List[schemas.StaffDaySchedule],
    summary="某日排班与订单总览",
)
def get_day_view(
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.StaffDaySchedule]:
    """按员工维度返回某日排班 + 订单，用于日历视图。"""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date 必须为 YYYY-MM-DD 格式",
        ) from exc

    staff_list = (
        db.query(models.Staff)
        .filter(
            models.Staff.status == "active",
            models.Staff.owner == current_account["username"],
        )
        .order_by(models.Staff.id)
        .all()
    )

    result: list[schemas.StaffDaySchedule] = []
    for staff in staff_list:
        shift_rows = (
            db.query(models.WorkShift)
            .filter(
                models.WorkShift.staff_id == staff.id,
                models.WorkShift.work_date == date,
                models.WorkShift.owner == current_account["username"],
            )
            .order_by(models.WorkShift.start_time)
            .all()
        )
        order_rows = (
            db.query(models.Order)
            .filter(
                models.Order.staff_id == staff.id,
                models.Order.order_date == date,
                models.Order.status != "cancelled",
                models.Order.owner == current_account["username"],
            )
            .order_by(models.Order.start_datetime)
            .all()
        )
        if not shift_rows and not order_rows:
            # 当日完全没有排班和订单的员工不返回，避免界面过于冗长
            continue

        shift_schemas = [
            schemas.WorkShiftRead(
                id=row.id,
                staff_id=row.staff_id,
                work_date=row.work_date,
                start_time=row.start_time,
                end_time=row.end_time,
                staff=None,
            )
            for row in shift_rows
        ]

        pending_rows = [row for row in order_rows if row.status == "pending"]
        actual_rows = [
            row for row in order_rows if row.status in {"in_progress", "finished", "completed"}
        ]

        pending_schemas = [
            schemas.OrderRead(
                id=row.id,
                staff_id=row.staff_id,
                staff_name=staff.name,
                customer_name=row.customer_name,
                order_date=row.order_date,
                start_datetime=row.start_datetime,
                end_datetime=row.end_datetime,
                duration_minutes=row.duration_minutes,
                total_amount=row.total_amount,
                package_id=getattr(row, "package_id", None),
                package_name=getattr(row, "package_name", None),
                extra_amount=getattr(row, "extra_amount", 0.0),
                payment_method=row.payment_method,
                commission_amount=row.commission_amount,
                status=row.status,
                note=row.note,
                created_at=row.created_at,
            )
            for row in pending_rows
        ]
        order_schemas = [
            schemas.OrderRead(
                id=row.id,
                staff_id=row.staff_id,
                staff_name=staff.name,
                customer_name=row.customer_name,
                order_date=row.order_date,
                start_datetime=row.start_datetime,
                end_datetime=row.end_datetime,
                duration_minutes=row.duration_minutes,
                total_amount=row.total_amount,
                package_id=getattr(row, "package_id", None),
                package_name=getattr(row, "package_name", None),
                extra_amount=getattr(row, "extra_amount", 0.0),
                payment_method=row.payment_method,
                commission_amount=row.commission_amount,
                status=row.status,
                note=row.note,
                created_at=row.created_at,
            )
            for row in actual_rows
        ]

        result.append(
            schemas.StaffDaySchedule(
                staff_id=staff.id,
                staff_name=staff.name,
                shifts=shift_schemas,
                pending_orders=pending_schemas,
                orders=order_schemas,
            )
        )
    return result


@router.get(
    "/orders/marks",
    response_model=List[str],
    summary="订单日历标记（含进行中/待结算/已完成）",
)
def get_order_marks(
    month: str = Query(..., description="月份 YYYY-MM"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[str]:
    """返回指定月份内存在订单（进行中/待结算/已完成）的日期列表。"""
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="month 必须为 YYYY-MM 格式",
        ) from exc

    like_pattern = f"{month}-%"
    active_status = ("in_progress", "finished", "completed")
    rows = (
        db.query(models.Order.order_date)
        .filter(
            models.Order.order_date.like(like_pattern),
            models.Order.status.in_(active_status),
            models.Order.owner == current_account["username"],
        )
        .group_by(models.Order.order_date)
        .all()
    )
    return [r[0] for r in rows]


@router.get(
    "/orders/active",
    response_model=List[schemas.OrderRead],
    summary="某日待处理订单列表",
)
def list_active_orders(
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.OrderRead]:
    """返回某日处于 pending/in_progress/finished 状态的订单列表。"""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date 必须为 YYYY-MM-DD 格式",
        ) from exc

    active_status = ("pending", "in_progress", "finished", "completed")
    rows = (
        db.query(models.Order, models.Staff.name.label("staff_name"))
        .join(models.Staff, models.Staff.id == models.Order.staff_id)
        .filter(
            models.Order.order_date == date,
            models.Order.status.in_(active_status),
            models.Order.owner == current_account["username"],
            models.Staff.owner == current_account["username"],
        )
        .order_by(models.Order.start_datetime)
        .all()
    )

    result: list[schemas.OrderRead] = []
    for order, staff_name in rows:
        result.append(
            schemas.OrderRead(
                id=order.id,
                staff_id=order.staff_id,
                staff_name=staff_name,
                customer_name=order.customer_name,
                order_date=order.order_date,
                start_datetime=order.start_datetime,
                end_datetime=order.end_datetime,
                duration_minutes=order.duration_minutes,
                booked_minutes=order.booked_minutes,
                total_amount=order.total_amount,
                package_id=order.package_id,
                package_name=order.package_name,
                extension_package_ids=order.extension_package_ids,
                extra_amount=order.extra_amount,
                payment_method=order.payment_method,
                commission_amount=order.commission_amount,
                status=order.status,
                note=order.note,
                created_at=order.created_at,
            )
        )
    return result


@router.get(
    "/available_staff",
    response_model=List[schemas.StaffRead],
    summary="查询指定时间段的可用员工",
)
def get_available_staff(
    target_time: str = Query(
        ..., description="目标开始时间 YYYY-MM-DD HH:MM:ss"
    ),
    duration: int = Query(..., description="时长（分钟）"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.StaffRead]:
    """根据现有订单计算指定时间段内可接单的员工列表。

    规则：只要该时间段内没有与其它订单重叠，即视为可用。
    排班仅用于前端展示，不做硬性限制。
    """
    start_dt = _parse_dt(target_time)

    if duration <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="duration 必须大于 0"
        )
    end_dt = start_dt + timedelta(minutes=duration)

    start_dt_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_dt_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 所有在职员工
    active_staff_ids = [
        row.id
        for row in db.query(models.Staff)
        .filter(
            models.Staff.status == "active",
            models.Staff.owner == current_account["username"],
        )
        .all()
    ]
    if not active_staff_ids:
        return []

    # 忙碌员工：在该时间段内已有订单（排除已取消）
    busy_staff_ids = [
        row.staff_id
        for row in db.query(models.Order)
        .filter(
            models.Order.staff_id.in_(active_staff_ids),
            models.Order.status != "cancelled",
            and_(
                models.Order.start_datetime < end_dt_str,
                models.Order.end_datetime > start_dt_str,
            ),
            models.Order.owner == current_account["username"],
        )
        .all()
    ]

    available_ids = set(active_staff_ids) - set(busy_staff_ids)
    if not available_ids:
        return []

    staff_list = (
        db.query(models.Staff)
        .filter(models.Staff.id.in_(available_ids))
        .order_by(models.Staff.id)
        .all()
    )
    return staff_list


@router.post(
    "/orders",
    response_model=schemas.OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建订单（含提成快照）",
)
def create_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.OrderRead:
    """创建订单并计算提成快照。

    同时做基础的撞单校验（同一员工同一时间段只允许一单）。
    """
    staff = (
        db.query(models.Staff)
        .filter(
            models.Staff.id == order_in.staff_id,
            models.Staff.owner == current_account["username"],
        )
        .first()
    )
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的 staff_id 不存在",
        )

    pkg = None
    if order_in.package_id is not None:
        pkg = (
            db.query(models.ServicePackage)
            .filter(
                models.ServicePackage.id == order_in.package_id,
                models.ServicePackage.owner == current_account["username"],
            )
            .first()
        )
    if pkg is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须选择一个有效的套餐",
        )

    start_dt = _parse_dt(order_in.start_datetime)

    end_dt = _parse_dt(order_in.end_datetime)
    if start_dt >= end_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始时间必须早于结束时间",
        )

    duration_minutes = int((end_dt - start_dt).total_seconds() // 60)
    order_date = start_dt.strftime("%Y-%m-%d")
    start_dt_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_dt_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 撞单校验：同一员工同一时间段不允许有重叠订单
    conflict = (
        db.query(models.Order)
        .filter(
            models.Order.staff_id == order_in.staff_id,
            models.Order.status != "cancelled",
            and_(
                models.Order.start_datetime < end_dt_str,
                models.Order.end_datetime > start_dt_str,
            ),
            models.Order.owner == current_account["username"],
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该时间段已存在订单，无法创建新订单",
        )

    # 计算提成快照
    commission_amount = _calc_commission_for_package(
        pkg, staff, current_account["username"], db
    )

    db_order = models.Order(
        staff_id=order_in.staff_id,
        customer_name=order_in.customer_name,
        order_date=order_date,
        start_datetime=start_dt_str,
        end_datetime=end_dt_str,
        duration_minutes=duration_minutes,
        booked_minutes=pkg.duration_minutes if pkg else 0,
        total_amount=order_in.total_amount,
        package_id=order_in.package_id,
        package_name=pkg.name if pkg else None,
        extra_amount=order_in.extra_amount or 0.0,
        payment_method=order_in.payment_method,
        commission_amount=commission_amount,
        status="pending",
        note=order_in.note,
        owner=current_account["username"],
        extension_package_ids=json.dumps([]),
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.get(
    "/orders",
    response_model=List[schemas.OrderRead],
    summary="历史订单列表",
)
def list_orders(
    from_date: Optional[str] = Query(
        None, description="起始日期 YYYY-MM-DD（可选）"
    ),
    to_date: Optional[str] = Query(
        None, description="结束日期 YYYY-MM-DD（可选）"
    ),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.OrderRead]:
    """历史订单列表（只包含已完成和已取消的订单），按创建时间倒序。"""

    def _parse_date(s: str) -> str:
        try:
            datetime.strptime(s, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期必须为 YYYY-MM-DD 格式",
            ) from exc
        return s

    if from_date:
        from_date = _parse_date(from_date)
    if to_date:
        to_date = _parse_date(to_date)

    query = (
        db.query(models.Order, models.Staff.name.label("staff_name"))
        .join(models.Staff, models.Staff.id == models.Order.staff_id)
        .filter(
            or_(models.Order.status == "completed", models.Order.status == "cancelled"),
            models.Order.owner == current_account["username"],
            models.Staff.owner == current_account["username"],
        )
    )

    if from_date:
        query = query.filter(models.Order.order_date >= from_date)
    if to_date:
        query = query.filter(models.Order.order_date <= to_date)

    orders = query.order_by(models.Order.created_at.desc()).all()

    result: list[schemas.OrderRead] = []
    for order, staff_name in orders:
        result.append(
            schemas.OrderRead(
                id=order.id,
                staff_id=order.staff_id,
                staff_name=staff_name,
                customer_name=order.customer_name,
                order_date=order.order_date,
                start_datetime=order.start_datetime,
                end_datetime=order.end_datetime,
                duration_minutes=order.duration_minutes,
                total_amount=order.total_amount,
                package_id=order.package_id,
                package_name=order.package_name,
                extension_package_ids=order.extension_package_ids,
                extra_amount=order.extra_amount,
                payment_method=order.payment_method,
                commission_amount=order.commission_amount,
                status=order.status,
                note=order.note,
                created_at=order.created_at,
            )
        )
    return result


@router.put(
    "/orders/{order_id}",
    response_model=schemas.OrderRead,
    summary="修改订单（重新计算提成）",
)
def update_order(
    order_id: int,
    order_in: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.OrderRead:
    """修改订单信息，并基于当前提成配置重新计算提成快照。

    注意：staff_id 不允许在此接口中修改，如需变更服务员工，应取消原订单后重新开单。
    """
    db_order = (
        db.query(models.Order)
        .filter(
            models.Order.id == order_id,
            models.Order.owner == current_account["username"],
        )
        .first()
    )
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在"
        )

    staff = (
        db.query(models.Staff)
        .filter(
            models.Staff.id == db_order.staff_id,
            models.Staff.owner == current_account["username"],
        )
        .first()
    )
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联员工不存在",
        )

    # 解析时间（若未提供则使用原值）
    start_str = order_in.start_datetime or db_order.start_datetime
    end_str = order_in.end_datetime or db_order.end_datetime
    start_dt = _parse_dt(start_str)
    end_dt = _parse_dt(end_str)
    if start_dt >= end_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始时间必须早于结束时间",
        )

    duration_minutes = int((end_dt - start_dt).total_seconds() // 60)
    order_date = start_dt.strftime("%Y-%m-%d")
    start_dt_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_dt_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 撞单校验：排除本订单本身
    conflict = (
        db.query(models.Order)
        .filter(
            models.Order.id != db_order.id,
            models.Order.staff_id == db_order.staff_id,
            models.Order.status != "cancelled",
            and_(
                models.Order.start_datetime < end_dt_str,
                models.Order.end_datetime > start_dt_str,
            ),
            models.Order.owner == current_account["username"],
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该时间段已存在其他订单，无法修改为新的时间范围",
        )

    # 金额与套餐信息：若未传则使用原值
    total_amount = (
        order_in.total_amount
        if order_in.total_amount is not None
        else db_order.total_amount
    )
    package_id = (
        order_in.package_id
        if order_in.package_id is not None
        else db_order.package_id
    )
    extra_amount = (
        order_in.extra_amount
        if order_in.extra_amount is not None
        else db_order.extra_amount
    )

    pkg = None
    if package_id is not None:
        pkg = (
            db.query(models.ServicePackage)
            .filter(
                models.ServicePackage.id == package_id,
                models.ServicePackage.owner == current_account["username"],
            )
            .first()
        )
        if not pkg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的套餐不存在",
            )
    elif db_order.package_id:
        pkg = (
            db.query(models.ServicePackage)
            .filter(
                models.ServicePackage.id == db_order.package_id,
                models.ServicePackage.owner == current_account["username"],
            )
            .first()
        )

    # 重新计算提成快照（使用当前配置，基础套餐 + 续钟套餐叠加）
    commission_amount = _calc_commission_for_package(
        pkg, staff, current_account["username"], db
    )

    # 应用变更
    db_order.customer_name = (
        order_in.customer_name
        if order_in.customer_name is not None
        else db_order.customer_name
    )
    db_order.order_date = order_date
    db_order.start_datetime = start_dt_str
    db_order.end_datetime = end_dt_str
    db_order.duration_minutes = duration_minutes
    db_order.total_amount = total_amount
    db_order.package_id = package_id
    db_order.package_name = pkg.name if pkg else None
    db_order.extra_amount = extra_amount
    db_order.payment_method = (
        order_in.payment_method
        if order_in.payment_method is not None
        else db_order.payment_method
    )
    db_order.note = (
        order_in.note if order_in.note is not None else db_order.note
    )

    # 续钟套餐时长累加：extend_minutes 用于增加 booked_minutes
    if order_in.extend_minutes:
        db_order.booked_minutes = (db_order.booked_minutes or 0) + order_in.extend_minutes
    elif pkg and order_in.package_id is not None:
        # 如果指定了新的套餐，则以新套餐时长作为 booked_minutes；无套餐则保持现值
        db_order.booked_minutes = pkg.duration_minutes or db_order.booked_minutes or 0

    # 续钟套餐 ID 列表：extend_package_id 追加；extension_package_ids 可直接覆盖
    ext_ids: list[int] = []
    if db_order.extension_package_ids:
        try:
            ext_ids = json.loads(db_order.extension_package_ids)
        except Exception:
            ext_ids = []
    if order_in.extension_package_ids is not None:
        ext_ids = order_in.extension_package_ids
    elif order_in.extend_package_id:
        ext_ids = ext_ids + [order_in.extend_package_id]
    db_order.extension_package_ids = json.dumps(ext_ids)

    # 若提供完整扩展包列表，则重算 booked_minutes = 基础套餐 + 续钟套餐总时长
    if pkg:
        total_minutes = pkg.duration_minutes or 0
        if ext_ids:
            ext_pkgs = (
                db.query(models.ServicePackage)
                .filter(models.ServicePackage.id.in_(ext_ids))
                .all()
            )
            ext_map = {p.id: p for p in ext_pkgs}
            for ext_id in ext_ids:
                if ext_id in ext_map:
                    total_minutes += ext_map[ext_id].duration_minutes or 0
        db_order.booked_minutes = total_minutes

    # 续钟套餐提成：在基础套餐提成基础上累加续钟套餐提成
    if pkg and ext_ids:
        ext_pkgs = (
            db.query(models.ServicePackage)
            .filter(models.ServicePackage.id.in_(ext_ids))
            .all()
        )
        for ext in ext_pkgs:
            commission_amount += _calc_commission_for_package(
                ext, staff, current_account["username"], db
            )

    if order_in.status is not None:
        db_order.status = order_in.status

    db.commit()
    db.refresh(db_order)

    return schemas.OrderRead(
        id=db_order.id,
        staff_id=db_order.staff_id,
        staff_name=staff.name,
        customer_name=db_order.customer_name,
        order_date=db_order.order_date,
        start_datetime=db_order.start_datetime,
        end_datetime=db_order.end_datetime,
        duration_minutes=db_order.duration_minutes,
        total_amount=db_order.total_amount,
        package_id=db_order.package_id,
        package_name=db_order.package_name,
        extra_amount=db_order.extra_amount,
        payment_method=db_order.payment_method,
        commission_amount=db_order.commission_amount,
        status=db_order.status,
        note=db_order.note,
        created_at=db_order.created_at,
    )
