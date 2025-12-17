from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_account

router = APIRouter(prefix="/api/staff", tags=["staff"])


@router.post(
    "",
    response_model=schemas.StaffRead,
    status_code=status.HTTP_201_CREATED,
)
def create_staff(
    staff_in: schemas.StaffCreate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.StaffRead:
    """新增员工。

    同名员工暂不做强校验，由业务自行约束。
    """
    commission_type = staff_in.commission_type or "percentage"
    if commission_type not in {"percentage", "fixed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="commission_type 仅支持 percentage 或 fixed",
        )

    db_staff = models.Staff(
        name=staff_in.name,
        nickname=staff_in.nickname,
        phone=staff_in.phone,
        status=staff_in.status or "active",
        base_salary=staff_in.base_salary or 0.0,
        commission_type=commission_type,
        commission_value=staff_in.commission_value or 0.0,
        owner=current_account["username"],
    )
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff


@router.get("", response_model=List[schemas.StaffRead])
def list_staff(
    status_filter: Optional[str] = Query(
        None, alias="status", description="按状态过滤：active/resigned"
    ),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.StaffRead]:
    """员工列表，可按状态过滤。"""
    query = db.query(models.Staff).filter(
        models.Staff.owner == current_account["username"]
    )
    if status_filter:
        query = query.filter(models.Staff.status == status_filter)
    return query.order_by(models.Staff.id.desc()).all()


@router.put(
    "/{staff_id}",
    response_model=schemas.StaffRead,
    summary="更新员工信息",
)
def update_staff(
    staff_id: int,
    staff_in: schemas.StaffUpdate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.StaffRead:
    """更新员工信息（部分字段可选）。"""
    db_staff = (
        db.query(models.Staff)
        .filter(
            models.Staff.id == staff_id,
            models.Staff.owner == current_account["username"],
        )
        .first()
    )
    if not db_staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="员工不存在"
        )

    update_data = staff_in.dict(exclude_unset=True)

    if "commission_type" in update_data:
        commission_type = update_data["commission_type"] or "percentage"
        if commission_type not in {"percentage", "fixed"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="commission_type 仅支持 percentage 或 fixed",
            )
        update_data["commission_type"] = commission_type

    for field, value in update_data.items():
        setattr(db_staff, field, value)

    db.commit()
    db.refresh(db_staff)
    return db_staff
