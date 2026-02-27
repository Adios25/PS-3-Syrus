from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# --- Checklists ---
class ChecklistItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False

class ChecklistItemCreate(ChecklistItemBase):
    pass

class ChecklistItemUpdate(ChecklistItemBase):
    pass

class ChecklistItemInDB(ChecklistItemBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Users ---
class UserBase(BaseModel):
    email: str
    name: str
    role: str = "developer"
    experience_level: str = "junior"

class UserCreate(UserBase):
    pass

class UserInDB(UserBase):
    id: int
    created_at: datetime
    checklists: List[ChecklistItemInDB] = []

    class Config:
        from_attributes = True
