from datetime import datetime, time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/roster", tags=["roster"])


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


@router.get("", response_model=List[schemas.WorkShiftRead])
def get_roster_by_date(
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
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
        .filter(models.WorkShift.work_date == date)
        .order_by(models.WorkShift.start_time)
        .all()
    )
    return shifts


@router.post(
    "",
    response_model=schemas.WorkShiftRead,
    status_code=status.HTTP_201_CREATED,
)
def create_work_shift(
    shift_in: schemas.WorkShiftCreate, db: Session = Depends(get_db)
) -> schemas.WorkShiftRead:
    """新增排班。

    当前版本仅做基础校验（时间合法、开始早于结束、员工存在），
    不做复杂排班冲突检测，后续可以基于 F2.2 规则扩展。
    """
    # 校验员工存在
    staff = db.query(models.Staff).filter(models.Staff.id == shift_in.staff_id).first()
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

    # 简单去重：避免完全相同的排班重复插入
    exists = (
        db.query(models.WorkShift)
        .filter(
            models.WorkShift.staff_id == shift_in.staff_id,
            models.WorkShift.work_date == shift_in.date,
            models.WorkShift.start_time == start_str,
            models.WorkShift.end_time == end_str,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="相同时间段排班已存在",
        )

    db_shift = models.WorkShift(
        staff_id=shift_in.staff_id,
        work_date=shift_in.date,
        start_time=start_str,
        end_time=end_str,
    )
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift


@router.post(
    "/copy",
    response_model=List[schemas.WorkShiftRead],
    summary="复制某日排班到另一日",
)
def copy_work_shifts(
    payload: schemas.RosterCopyRequest, db: Session = Depends(get_db)
) -> List[schemas.WorkShiftRead]:
    """复制指定日期的排班到目标日期。

    用于实现“复制排班到今天”等功能。
    """
    source_shifts = (
        db.query(models.WorkShift)
        .filter(models.WorkShift.work_date == payload.from_date)
        .all()
    )
    if not source_shifts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="源日期无排班可复制",
        )

    # 若目标日期已有排班且未允许覆盖，则提示前端确认
    target_q = db.query(models.WorkShift).filter(
        models.WorkShift.work_date == payload.to_date
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
        )
        db.add(cloned)
        new_shifts.append(cloned)

    db.commit()
    for s in new_shifts:
        db.refresh(s)
    return new_shifts
