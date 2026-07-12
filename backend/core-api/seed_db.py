import asyncio
import uuid
from app.db import AsyncSessionLocal, engine
from app.models.department import Department
from app.models.employee import Employee
from app.models.asset_category import AssetCategory
from app.models.asset import Asset
from app.core.security import hash_password
from sqlalchemy import select, text
from app.db import Base

async def seed_data():
    # Setup tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Define the exact UUIDs used in tests
        DEPT_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
        EMPLOYEE_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
        MANAGER_ID = uuid.UUID("00000000-0000-0000-0000-000000000009")
        ASSET_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
        CATEGORY_ID = uuid.UUID("00000000-0000-0000-0000-000000000004")

        # 1. Department
        dept = await db.get(Department, DEPT_ID)
        if not dept:
            dept = Department(id=DEPT_ID, name="Engineering")
            db.add(dept)

        # 2. Employees
        emp = await db.get(Employee, EMPLOYEE_ID)
        if not emp:
            emp = Employee(
                id=EMPLOYEE_ID,
                name="Test Employee",
                email="employee@test.com",
                password_hash=hash_password("password123"),
                department_id=DEPT_ID,
                role="Employee"
            )
            db.add(emp)
            
        mgr = await db.get(Employee, MANAGER_ID)
        if not mgr:
            mgr = Employee(
                id=MANAGER_ID,
                name="Test Manager",
                email="manager@test.com",
                password_hash=hash_password("password123"),
                department_id=DEPT_ID,
                role="AssetManager"
            )
            db.add(mgr)

        # 3. Asset Category
        cat = await db.get(AssetCategory, CATEGORY_ID)
        if not cat:
            cat = AssetCategory(
                id=CATEGORY_ID, 
                name="Laptops"
            )
            db.add(cat)

        # 4. Asset
        asset = await db.get(Asset, ASSET_ID)
        if not asset:
            asset = Asset(
                id=ASSET_ID,
                name="Laptop #A-042",
                category_id=CATEGORY_ID,
                asset_tag="AF-0001",
                status="Available",
                is_bookable=True
            )
            db.add(asset)

        await db.commit()
        print("Database seeded successfully with test data!")

if __name__ == "__main__":
    asyncio.run(seed_data())
