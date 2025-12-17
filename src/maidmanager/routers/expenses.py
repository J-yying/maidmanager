from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_account

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.post(
    "",
    response_model=schemas.ExpenseRead,
    status_code=status.HTTP_201_CREATED,
    summary="新增支出记录",
)
def create_expense(
    expense_in: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.ExpenseRead:
    """新增一条支出记录（如房租、水电等）。"""
    if expense_in.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="amount 必须大于 0"
        )

    db_expense = models.Expense(
        title=expense_in.title,
        amount=expense_in.amount,
        expense_date=expense_in.expense_date,
        category=expense_in.category,
        note=expense_in.note,
        owner=current_account["username"],
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.get(
    "",
    response_model=List[schemas.ExpenseRead],
    summary="支出列表",
)
def list_expenses(
    month: Optional[str] = Query(
        None, description="按月份过滤，格式 YYYY-MM（可选）"
    ),
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> List[schemas.ExpenseRead]:
    """查询支出列表，可按月份过滤。"""
    query = db.query(models.Expense).filter(
        models.Expense.owner == current_account["username"]
    )
    if month:
        if len(month) != 7 or "-" not in month:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="month 必须是 YYYY-MM 格式",
            )
        like_pattern = f"{month}-%"
        query = query.filter(models.Expense.expense_date.like(like_pattern))

    return query.order_by(
        models.Expense.expense_date.desc(), models.Expense.id.desc()
    ).all()


@router.put(
    "/{expense_id}",
    response_model=schemas.ExpenseRead,
    summary="更新支出记录",
)
def update_expense(
    expense_id: int,
    expense_in: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> schemas.ExpenseRead:
    """修改一条支出记录。"""
    db_expense = (
        db.query(models.Expense)
        .filter(
            models.Expense.id == expense_id,
            models.Expense.owner == current_account["username"],
        )
        .first()
    )
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="支出记录不存在"
        )

    update_data = expense_in.dict(exclude_unset=True)
    if "amount" in update_data and update_data["amount"] is not None:
        if update_data["amount"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="amount 必须大于 0",
            )

    for field, value in update_data.items():
        setattr(db_expense, field, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除支出记录",
)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_account: dict = Depends(get_current_account),
) -> None:
    db_expense = (
        db.query(models.Expense)
        .filter(
            models.Expense.id == expense_id,
            models.Expense.owner == current_account["username"],
        )
        .first()
    )
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="支出记录不存在"
        )
    db.delete(db_expense)
    db.commit()
