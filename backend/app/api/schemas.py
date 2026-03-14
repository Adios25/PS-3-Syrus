from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List
import re

# --- Checklists ---
class ChecklistItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters long")
        if len(v) > 100:
            raise ValueError("Title must be at most 100 characters long")
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_\-\s]*$'
        if not re.match(pattern, v):
            raise ValueError(
                "Title must start with an alphanumeric character and contain "
                "only letters, numbers, underscores, hyphens, or spaces"
            )
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("Description must be at most 500 characters long")
        return v

class ChecklistItemCreate(ChecklistItemBase):
    pass

class ChecklistItemUpdate(ChecklistItemBase):
    pass

class ChecklistItemInDB(ChecklistItemBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

