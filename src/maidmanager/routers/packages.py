from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_account

router = APIRouter(prefix="/api/packages", tags=["套餐"])


@router.get(
    "",
    response_model=List[schemas.ServicePackageRead],
    summary="套餐列表",
)
def list_packages(
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.ServicePackageRead]:
    """查询所有套餐，按创建顺序返回。"""
    return (
        db.query(models.ServicePackage)
        .filter(models.ServicePackage.owner == current_account["username"])
        .order_by(models.ServicePackage.id)
        .all()
    )


@router.post(
    "",
    response_model=schemas.ServicePackageRead,
    status_code=status.HTTP_201_CREATED,
    summary="新增套餐",
)
def create_package(
    payload: schemas.ServicePackageCreate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.ServicePackageRead:
    if payload.duration_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="duration_minutes 必须大于 0",
        )
    if payload.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="price 必须大于 0",
        )

    db_pkg = models.ServicePackage(
        name=payload.name,
        duration_minutes=payload.duration_minutes,
        price=payload.price,
        description=payload.description,
        default_commission=payload.default_commission or 0.0,
        owner=current_account["username"],
    )
    db.add(db_pkg)
    db.commit()
    db.refresh(db_pkg)
    return db_pkg


@router.put(
    "/{package_id}",
    response_model=schemas.ServicePackageRead,
    summary="更新套餐",
)
def update_package(
    package_id: int,
    payload: schemas.ServicePackageUpdate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.ServicePackageRead:
    db_pkg = (
        db.query(models.ServicePackage)
        .filter(
            models.ServicePackage.id == package_id,
            models.ServicePackage.owner == current_account["username"],
        )
        .first()
    )
    if not db_pkg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="套餐不存在"
        )

    data = payload.dict(exclude_unset=True)
    if "duration_minutes" in data and data["duration_minutes"] is not None:
        if data["duration_minutes"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="duration_minutes 必须大于 0",
            )
    if "price" in data and data["price"] is not None:
        if data["price"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="price 必须大于 0",
            )

    for field, value in data.items():
        setattr(db_pkg, field, value)

    db.commit()
    db.refresh(db_pkg)
    return db_pkg


@router.delete(
    "/{package_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除套餐",
)
def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> None:
    """删除套餐。

    若已有订单使用该套餐，建议只在不影响历史数据时删除。
    当前简单实现为直接删除记录。
    """
    db_pkg = (
        db.query(models.ServicePackage)
        .filter(
            models.ServicePackage.id == package_id,
            models.ServicePackage.owner == current_account["username"],
        )
        .first()
    )
    if not db_pkg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="套餐不存在"
        )
    db.delete(db_pkg)
    db.commit()
