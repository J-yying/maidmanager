from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/staff", tags=["staff"])


@router.get(
    "/{staff_id}/package_commissions",
    response_model=List[schemas.StaffPackageCommissionItem],
    summary="查询员工的套餐提成配置",
)
def list_staff_package_commissions(
    staff_id: int, db: Session = Depends(get_db)
) -> List[schemas.StaffPackageCommissionItem]:
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="员工不存在"
        )

    # 所有套餐
    packages = db.query(models.ServicePackage).order_by(models.ServicePackage.id).all()

    # 该员工的配置
    rows = (
        db.query(models.StaffPackageCommission)
        .filter(models.StaffPackageCommission.staff_id == staff_id)
        .all()
    )
    by_package = {row.package_id: row for row in rows}

    result: list[schemas.StaffPackageCommissionItem] = []
    for p in packages:
        row = by_package.get(p.id)
        result.append(
            schemas.StaffPackageCommissionItem(
                package_id=p.id,
                package_name=p.name,
                default_commission=p.default_commission or 0.0,
                staff_commission=row.commission_amount if row else None,
            )
        )
    return result


@router.put(
    "/{staff_id}/package_commissions",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="更新员工的套餐提成配置",
)
def update_staff_package_commissions(
    staff_id: int,
    items: List[schemas.StaffPackageCommissionUpdateItem],
    db: Session = Depends(get_db),
) -> None:
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="员工不存在"
        )

    for item in items:
        if item.commission_amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="提成金额不能为负数",
            )

    # 逐条 upsert
    for item in items:
        row = (
            db.query(models.StaffPackageCommission)
            .filter(
                models.StaffPackageCommission.staff_id == staff_id,
                models.StaffPackageCommission.package_id == item.package_id,
            )
            .first()
        )
        if row:
            row.commission_amount = item.commission_amount
        else:
            row = models.StaffPackageCommission(
                staff_id=staff_id,
                package_id=item.package_id,
                commission_amount=item.commission_amount,
            )
            db.add(row)

    db.commit()

