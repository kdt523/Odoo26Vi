"""
app/routers/org.py — Organisation setup router.

Endpoints:
  Departments:
    GET    /departments            — List all departments
    POST   /departments            — Create department (Admin)
    GET    /departments/{id}       — Get department detail
    PUT    /departments/{id}       — Update department (Admin)
    DELETE /departments/{id}       — Soft-delete department (Admin)

  Asset Categories:
    GET    /categories             — List all categories
    POST   /categories             — Create category (Admin/AssetManager)
    GET    /categories/{id}        — Get category detail
    PUT    /categories/{id}        — Update category (Admin/AssetManager)
    DELETE /categories/{id}        — Delete category (Admin)

  Employee Directory:
    GET    /employees              — List employees (Admin)
    POST   /employees              — Create employee (Admin)
    GET    /employees/{id}         — Get employee detail
    PUT    /employees/{id}         — Update employee (Admin)
    POST   /employees/{id}/promote — Promote role (Admin-only)
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin, require_asset_manager, require_authenticated
from app.db import get_db
from app.schemas.org import (
    AssetCategoryCreate,
    AssetCategoryOut,
    AssetCategoryUpdate,
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeOut,
    EmployeeUpdate,
    RolePromotionRequest,
)

router = APIRouter(prefix="/org", tags=["org"])


# ── Departments ────────────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentOut])
async def list_departments(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    # TODO: query all departments
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/departments", response_model=DepartmentOut, status_code=201,
             dependencies=[Depends(require_admin)])
async def create_department(body: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    # TODO: insert Department ORM object
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/departments/{department_id}", response_model=DepartmentOut)
async def get_department(department_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                         _=Depends(require_authenticated)):
    # TODO: fetch by id → 404 if missing
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/departments/{department_id}", response_model=DepartmentOut,
            dependencies=[Depends(require_admin)])
async def update_department(department_id: uuid.UUID, body: DepartmentUpdate,
                             db: AsyncSession = Depends(get_db)):
    # TODO: fetch → apply patch → commit
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/departments/{department_id}", status_code=204,
               dependencies=[Depends(require_admin)])
async def delete_department(department_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # TODO: soft-delete (set status=Inactive) or hard-delete with FK guard
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


# ── Asset Categories ───────────────────────────────────────────────────────

@router.get("/categories", response_model=List[AssetCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    # TODO: query all asset categories
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/categories", response_model=AssetCategoryOut, status_code=201,
             dependencies=[Depends(require_asset_manager)])
async def create_category(body: AssetCategoryCreate, db: AsyncSession = Depends(get_db)):
    # TODO: insert AssetCategory
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/categories/{category_id}", response_model=AssetCategoryOut)
async def get_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                       _=Depends(require_authenticated)):
    # TODO: fetch by id → 404
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/categories/{category_id}", response_model=AssetCategoryOut,
            dependencies=[Depends(require_asset_manager)])
async def update_category(category_id: uuid.UUID, body: AssetCategoryUpdate,
                           db: AsyncSession = Depends(get_db)):
    # TODO: fetch → patch → commit
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/categories/{category_id}", status_code=204,
               dependencies=[Depends(require_admin)])
async def delete_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # TODO: delete or soft-delete; guard if assets reference this category
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


# ── Employee Directory ─────────────────────────────────────────────────────

@router.get("/employees", response_model=List[EmployeeOut],
            dependencies=[Depends(require_admin)])
async def list_employees(db: AsyncSession = Depends(get_db)):
    # TODO: paginated employee list
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/employees", response_model=EmployeeOut, status_code=201,
             dependencies=[Depends(require_admin)])
async def create_employee(body: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    # TODO: admin-created employee (role can be set by admin)
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/employees/{employee_id}", response_model=EmployeeOut,
            dependencies=[Depends(require_admin)])
async def get_employee(employee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # TODO: fetch by id → 404
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/employees/{employee_id}", response_model=EmployeeOut,
            dependencies=[Depends(require_admin)])
async def update_employee(employee_id: uuid.UUID, body: EmployeeUpdate,
                           db: AsyncSession = Depends(get_db)):
    # TODO: fetch → patch → commit
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/employees/{employee_id}/promote", response_model=EmployeeOut,
             dependencies=[Depends(require_admin)])
async def promote_employee(employee_id: uuid.UUID, body: RolePromotionRequest,
                            db: AsyncSession = Depends(get_db)):
    """
    Admin-only: change an employee's role.
    This is the ONLY way to assign DepartmentHead / AssetManager / Admin roles.
    """
    # TODO: fetch employee → set employee.role = body.role → commit
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
