from datetime import datetime, time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_account

router = APIRouter(prefix="/api/roster", tags=["排班"])


def _normalize_time_str(raw: str) -> str:
    """将 HH:MM 或 HH:MM:ss 标准化为 HH:MM:ss 字符串。"""
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.strftime("%H:%M:%S")
        except ValueError:
            continue
    raise ValueError("时间格式必须为 HH:MM 或 HH:MM:ss")


def _parse_time(raw: str) -> time:
    normalized = _normalize_time_str(raw)
    return datetime.strptime(normalized, "%H:%M:%S").time()


@router.get(
    "",
    response_model=List[schemas.WorkShiftRead],
    summary="获取指定日期排班",
)
def get_roster_by_date(
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.WorkShiftRead]:
    """获取某日排班列表。"""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date 必须是 YYYY-MM-DD 格式",
        ) from exc

    shifts = (
        db.query(models.WorkShift)
        .filter(
            models.WorkShift.work_date == date,
            models.WorkShift.owner == current_account["username"],
        )
        .order_by(models.WorkShift.start_time)
        .all()
    )
    return shifts


@router.post(
    "",
    response_model=schemas.WorkShiftRead,
    status_code=status.HTTP_201_CREATED,
    summary="新增排班",
)
def create_work_shift(
    shift_in: schemas.WorkShiftCreate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.WorkShiftRead:
    """新增排班。

    当前版本仅做基础校验（时间合法、开始早于结束、员工存在），
    不做复杂排班冲突检测，后续可以基于 F2.2 规则扩展。
    """
    # 校验员工存在
    staff = (
        db.query(models.Staff)
        .filter(
            models.Staff.id == shift_in.staff_id,
            models.Staff.owner == current_account["username"],
        )
        .first()
    )
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的 staff_id 不存在",
        )

    # 时间合法性与顺序校验
    try:
        start_time_obj = _parse_time(shift_in.start)
        end_time_obj = _parse_time(shift_in.end)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if start_time_obj >= end_time_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始时间必须早于结束时间",
        )

    # 标准化时间字符串用于存储
    start_str = start_time_obj.strftime("%H:%M:%S")
    end_str = end_time_obj.strftime("%H:%M:%S")

    # 限制：同一员工同一天仅允许 1 条排班
    exists_same_day = (
        db.query(models.WorkShift)
        .filter(
            models.WorkShift.staff_id == shift_in.staff_id,
            models.WorkShift.work_date == shift_in.date,
            models.WorkShift.owner == current_account["username"],
        )
        .first()
    )
    if exists_same_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该员工当天已存在排班，不能重复添加",
        )

    db_shift = models.WorkShift(
        staff_id=shift_in.staff_id,
        work_date=shift_in.date,
        start_time=start_str,
        end_time=end_str,
        owner=current_account["username"],
    )
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift


@router.post(
    "/copy",
    response_model=List[schemas.WorkShiftRead],
    summary="复制排班到指定日期",
)
def copy_work_shifts(
    payload: schemas.RosterCopyRequest,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.WorkShiftRead]:
    """复制指定日期的排班到目标日期。

    用于实现“复制排班到今天”等功能。
    """
    source_shifts = (
        db.query(models.WorkShift)
        .filter(
            models.WorkShift.work_date == payload.from_date,
            models.WorkShift.owner == current_account["username"],
        )
        .all()
    )
    if not source_shifts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="源日期无排班可复制",
        )

    # 若目标日期已有排班且未允许覆盖，则提示前端确认
    target_q = db.query(models.WorkShift).filter(
        models.WorkShift.work_date == payload.to_date,
        models.WorkShift.owner == current_account["username"],
    )
    target_count = target_q.count()
    if target_count > 0 and not payload.override:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目标日期已有排班，如需覆盖请设置 override=true",
        )

    if target_count > 0 and payload.override:
        target_q.delete(synchronize_session=False)

    new_shifts: list[models.WorkShift] = []
    for shift in source_shifts:
        cloned = models.WorkShift(
            staff_id=shift.staff_id,
            work_date=payload.to_date,
            start_time=shift.start_time,
            end_time=shift.end_time,
            owner=current_account["username"],
        )
        db.add(cloned)
        new_shifts.append(cloned)

    db.commit()
    for s in new_shifts:
        db.refresh(s)
    return new_shifts


@router.delete(
    "/{shift_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除排班（需无预约/订单）",
)
def delete_work_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> None:
    """删除排班：若当日该员工存在未取消的预约/订单（含进行中、已完成等），不允许删除。"""
    db_shift = (
        db.query(models.WorkShift)
        .filter(
            models.WorkShift.id == shift_id,
            models.WorkShift.owner == current_account["username"],
        )
        .first()
    )
    if not db_shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="排班不存在"
        )

    # 检查当日同员工的非取消订单
    conflict_order = (
        db.query(models.Order)
        .filter(
            models.Order.staff_id == db_shift.staff_id,
            models.Order.order_date == db_shift.work_date,
            models.Order.owner == current_account["username"],
            models.Order.status != "cancelled",
        )
        .first()
    )
    if conflict_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="存在该员工当日的预约/订单，需先取消后再删除排班",
        )

    db.delete(db_shift)
    db.commit()


@router.put(
    "/{shift_id}",
    response_model=schemas.WorkShiftRead,
    summary="编辑排班（修改开始/结束时间）",
)
def update_work_shift(
    shift_id: int,
    payload: schemas.WorkShiftUpdate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.WorkShiftRead:
    """编辑排班：仅允许修改开始/结束时间，不可改员工与日期。"""
    db_shift = (
        db.query(models.WorkShift)
        .filter(
            models.WorkShift.id == shift_id,
            models.WorkShift.owner == current_account["username"],
        )
        .first()
    )
    if not db_shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="排班不存在"
        )

    # 如未提供则沿用原值
    new_start = payload.start or db_shift.start_time
    new_end = payload.end or db_shift.end_time

    try:
        start_time_obj = _parse_time(new_start)
        end_time_obj = _parse_time(new_end)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if start_time_obj >= end_time_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始时间必须早于结束时间",
        )

    # 员工与日期保持不变，仅更新时间
    db_shift.start_time = start_time_obj.strftime("%H:%M:%S")
    db_shift.end_time = end_time_obj.strftime("%H:%M:%S")
    db.commit()
    db.refresh(db_shift)
    return db_shift
