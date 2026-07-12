"""
app/routers/org.py — Organisation setup router.

Endpoints:
  Departments:
    GET    /departments            — List all departments
    POST   /departments            — Create department (Admin)
    GET    /departments/{id}       — Get department detail
    PUT    /departments/{id}       — Update department (Admin)
    DELETE /departments/{id}       — Soft-delete department (Admin)
    GET    /departments/{id}/tree  — Get department and children nested

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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin, require_asset_manager, require_authenticated
from app.db import get_db
from app.models.department import Department
from app.models.asset_category import AssetCategory
from app.models.employee import Employee
from app.models.activity_log import ActivityLog
from app.services.activity_log import log_activity
from app.models.asset import Asset
from app.models.allocation import Allocation
from app.schemas.org import (
    AssetCategoryCreate,
    AssetCategoryOut,
    AssetCategoryUpdate,
    DepartmentCreate,
    DepartmentOut,
    DepartmentTreeOut,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeOut,
    EmployeeUpdate,
    RolePromotionRequest,
)

router = APIRouter(prefix="/org", tags=["org"])

async def check_department_cycle(db: AsyncSession, dept_id: uuid.UUID, new_parent_id: uuid.UUID):
    current = new_parent_id
    while current:
        if current == dept_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Circular parent chain detected.")
        parent = await db.get(Department, current)
        if not parent:
            break
        current = parent.parent_department_id

def validate_flat_dict(d: dict):
    for k, v in d.items():
        if not isinstance(v, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="custom_fields must be a flat dictionary of strings.")

# ── Departments ────────────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentOut])
async def list_departments(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    stmt = select(Department)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/departments", response_model=DepartmentOut, status_code=201,
             dependencies=[Depends(require_admin)])
async def create_department(body: DepartmentCreate, db: AsyncSession = Depends(get_db),
                             current_user=Depends(require_admin)):
    if body.parent_department_id:
        parent = await db.get(Department, body.parent_department_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent department not found")
            
    if body.head_employee_id:
        head = await db.get(Employee, body.head_employee_id)
        if not head:
            raise HTTPException(status_code=400, detail="Head employee not found")

    dept = Department(
        name=body.name,
        parent_department_id=body.parent_department_id,
        head_employee_id=body.head_employee_id,
        status=body.status
    )
    db.add(dept)
    await db.flush()
    log_activity(db, current_user.id, "Department Created", "Department", str(dept.id))
    await db.commit()
    await db.refresh(dept)
    return dept


@router.get("/departments/{department_id}", response_model=DepartmentOut)
async def get_department(department_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                         _=Depends(require_authenticated)):
    dept = await db.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept


@router.get("/departments/{department_id}/tree", response_model=DepartmentTreeOut)
async def get_department_tree(department_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    stmt = select(Department)
    result = await db.execute(stmt)
    all_depts = result.scalars().all()
    
    dept_map = {d.id: DepartmentTreeOut.model_validate(d) for d in all_depts}
    if department_id not in dept_map:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        
    for d in all_depts:
        if d.parent_department_id and d.parent_department_id in dept_map:
            parent = dept_map[d.parent_department_id]
            if parent.children is None:
                parent.children = []
            parent.children.append(dept_map[d.id])
            
    return dept_map[department_id]


@router.put("/departments/{department_id}", response_model=DepartmentOut,
            dependencies=[Depends(require_admin)])
async def update_department(department_id: uuid.UUID, body: DepartmentUpdate,
                             db: AsyncSession = Depends(get_db),
                             current_user=Depends(require_admin)):
    dept = await db.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        
    if body.parent_department_id is not None:
        await check_department_cycle(db, department_id, body.parent_department_id)
        parent = await db.get(Department, body.parent_department_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent department not found")
        dept.parent_department_id = body.parent_department_id
        
    if body.head_employee_id is not None:
        head = await db.get(Employee, body.head_employee_id)
        if not head:
            raise HTTPException(status_code=400, detail="Head employee not found")
        dept.head_employee_id = body.head_employee_id
        
    if body.name is not None:
        dept.name = body.name
    if body.status is not None:
        dept.status = body.status
        
    log_activity(db, current_user.id, "department_updated", "Department", str(department_id),
                 details={"updated_fields": body.model_dump(exclude_unset=True)})
    await db.commit()
    await db.refresh(dept)
    return dept


@router.delete("/departments/{department_id}", dependencies=[Depends(require_admin)])
async def delete_department(department_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                             current_user=Depends(require_admin)):
    dept = await db.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        
    emp_stmt = select(Employee).where(Employee.department_id == department_id).limit(1)
    emp_res = await db.execute(emp_stmt)
    has_employees = emp_res.scalar_one_or_none() is not None
    
    alloc_stmt = select(Allocation).where(Allocation.department_id == department_id).limit(1)
    alloc_res = await db.execute(alloc_stmt)
    has_assets = alloc_res.scalar_one_or_none() is not None
    
    if has_employees or has_assets:
        dept.status = "Inactive"
        log_activity(db, current_user.id, "department_deactivated", "Department", str(department_id))
        await db.commit()
        return {"detail": "Department has active employees/assets and was deactivated instead of deleted.", "deactivated": True}
        
    log_activity(db, current_user.id, "department_deleted", "Department", str(department_id))
    await db.delete(dept)
    await db.commit()
    return {"detail": "Department deleted."}


# ── Asset Categories ───────────────────────────────────────────────────────

@router.get("/categories", response_model=List[AssetCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    stmt = select(AssetCategory).where(AssetCategory.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/categories", response_model=AssetCategoryOut, status_code=201,
             dependencies=[Depends(require_asset_manager)])
async def create_category(body: AssetCategoryCreate, db: AsyncSession = Depends(get_db),
                           current_user=Depends(require_asset_manager)):
    validate_flat_dict(body.custom_fields)
    
    cat = AssetCategory(
        name=body.name,
        custom_fields=body.custom_fields,
        is_active=True
    )
    db.add(cat)
    await db.flush()
    log_activity(db, current_user.id, "Asset Category Created", "AssetCategory", str(cat.id))
    await db.commit()
    await db.refresh(cat)
    return cat


@router.get("/categories/{category_id}", response_model=AssetCategoryOut)
async def get_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                       _=Depends(require_authenticated)):
    cat = await db.get(AssetCategory, category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return cat


@router.put("/categories/{category_id}", response_model=AssetCategoryOut,
            dependencies=[Depends(require_asset_manager)])
async def update_category(category_id: uuid.UUID, body: AssetCategoryUpdate,
                           db: AsyncSession = Depends(get_db),
                           current_user=Depends(require_asset_manager)):
    cat = await db.get(AssetCategory, category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        
    if body.custom_fields is not None:
        validate_flat_dict(body.custom_fields)
        cat.custom_fields = body.custom_fields
        
    if body.name is not None:
        cat.name = body.name
        
    log_activity(db, current_user.id, "category_updated", "AssetCategory", str(category_id),
                 details={"updated_fields": body.model_dump(exclude_unset=True)})
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", dependencies=[Depends(require_admin)])
async def delete_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                           current_user=Depends(require_admin)):
    cat = await db.get(AssetCategory, category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        
    asset_stmt = select(Asset).where(Asset.category_id == category_id).limit(1)
    asset_res = await db.execute(asset_stmt)
    has_assets = asset_res.scalar_one_or_none() is not None
    
    if has_assets:
        cat.is_active = False
        log_activity(db, current_user.id, "category_disabled", "AssetCategory", str(category_id))
        await db.commit()
        return {"detail": "Category is in use and was softly disabled instead of hard-deleted.", "disabled": True}
        
    log_activity(db, current_user.id, "category_deleted", "AssetCategory", str(category_id))
    await db.delete(cat)
    await db.commit()
    return {"detail": "Category deleted."}


# ── Employee Directory ─────────────────────────────────────────────────────

@router.get("/employees", response_model=List[EmployeeOut],
            dependencies=[Depends(require_admin)])
async def list_employees(
    name: str | None = None,
    email: str | None = None,
    department_id: uuid.UUID | None = None,
    role: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Employee)
    if name:
        stmt = stmt.where(Employee.name.ilike(f"%{name}%"))
    if email:
        stmt = stmt.where(Employee.email.ilike(f"%{email}%"))
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    if role:
        stmt = stmt.where(Employee.role == role)
    if status:
        stmt = stmt.where(Employee.status == status)
        
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/employees", response_model=EmployeeOut, status_code=201,
             dependencies=[Depends(require_admin)])
async def create_employee(body: EmployeeCreate, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    log_activity(db, current_user.id, "Employee Created", "Employee")
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
                           db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    stmt = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        
    if body.name is not None:
        employee.name = body.name
    if body.department_id is not None:
        employee.department_id = body.department_id
    if body.status is not None:
        employee.status = body.status
        
    log_activity(db, current_user.id, "Employee Updated", "Employee", str(employee_id))
    await db.commit()
    await db.refresh(employee)
    return employee


@router.post("/employees/{employee_id}/promote", response_model=EmployeeOut,
             dependencies=[Depends(require_admin)])
async def promote_employee(employee_id: uuid.UUID, body: RolePromotionRequest,
                            current_user=Depends(require_admin),
                            db: AsyncSession = Depends(get_db)):
    """
    Admin-only: change an employee's role.
    This is the ONLY way to assign DepartmentHead / AssetManager / Admin roles.
    """
    if body.role == "Admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot promote to Admin via this endpoint")
        
    stmt = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        
    old_role = employee.role
    employee.role = body.role
    
    # Log the promotion
    log_activity(
        db,
        current_user.id,
        "role_promoted",
        "Employee",
        str(employee.id),
        details={"old_role": old_role, "new_role": employee.role}
    )
    
    await db.commit()
    await db.refresh(employee)
    return employee
