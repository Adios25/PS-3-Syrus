from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..deps import get_db
from ..schemas import ChecklistItemCreate, ChecklistItemInDB, ChecklistItemUpdate
from ...db.models import ChecklistItem, User

router = APIRouter()

@router.post("/", response_model=ChecklistItemInDB)
async def create_item(
    user_id: int = Path(...),
    item: ChecklistItemCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    # Verify user exists
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    if not user_result.scalars().first():
        raise HTTPException(status_code=404, detail="User not found")

    db_item = ChecklistItem(
        title=item.title,
        description=item.description,
        is_completed=item.is_completed,
        owner_id=user_id,
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[ChecklistItemInDB])
async def read_items(user_id: int = Path(...), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ChecklistItem)
        .where(ChecklistItem.owner_id == user_id)
        .order_by(ChecklistItem.id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{item_id}", response_model=ChecklistItemInDB)
async def update_item(
    user_id: int = Path(...),
    item_id: int = Path(...),
    item_update: ChecklistItemUpdate = ...,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChecklistItem).where(
        ChecklistItem.id == item_id,
        ChecklistItem.owner_id == user_id,
    )
    result = await db.execute(stmt)
    db_item = result.scalars().first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    await db.commit()
    await db.refresh(db_item)
    return db_item

