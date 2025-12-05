from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.database import get_db
from app.models.models import Category
from pydantic import BaseModel
from typing import List

router = APIRouter()


class CategoryCreate(BaseModel):
    name: str

class CategoryOut(CategoryCreate):
    id: int
    class Config:
        orm_mode = True

@router.post("/api/categories", response_model=CategoryOut)
async def create_category(
    category: CategoryCreate, db: AsyncSession = Depends(get_db)
):
    db_category = Category(**category.dict())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.get("/api/categories", response_model=List[CategoryOut])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return categories

@router.put("/api/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db_category.name = category.name
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.delete("/api/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(db_category)
    await db.commit()
    return
