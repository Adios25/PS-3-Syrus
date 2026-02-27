from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..deps import get_db
from ..schemas import UserCreate, UserInDB
from ...db.models import User

router = APIRouter()

@router.post("/", response_model=UserInDB)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    stmt = select(User).where(User.email == user.email)
    result = await db.execute(stmt)
    db_user = result.scalars().first()
    
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    db_user = User(
        email=user.email,
        name=user.name,
        role=user.role,
        experience_level=user.experience_level
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=UserInDB)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    db_user = result.scalars().first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
