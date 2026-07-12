import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models.booking import Booking
from app.models.allocation import Allocation
from app.models.maintenance_request import MaintenanceRequest
from app.models.employee import Employee
from app.services.notifications import create_notification
from app.models.activity_log import ActivityLog

logger = logging.getLogger(__name__)

async def process_booking_reminders():
    logger.info("Running process_booking_reminders...")
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        thirty_mins_from_now = now + timedelta(minutes=30)

        stmt = select(Booking).where(
            Booking.status == "Upcoming",
            Booking.reminder_sent_at.is_(None),
            Booking.start_time > now,
            Booking.start_time <= thirty_mins_from_now
        )
        result = await db.execute(stmt)
        bookings = result.scalars().all()

        for booking in bookings:
            await create_notification(
                db=db,
                user_id=booking.employee_id,
                type_="BookingReminder",
                message=f"Reminder: Your booking starts at {booking.start_time.strftime('%Y-%m-%d %H:%M')}.",
                entity_type="Booking",
                entity_id=str(booking.id),
            )
            booking.reminder_sent_at = now
            db.add(ActivityLog(
                user_id=booking.employee_id,
                action="booking_reminder_sent",
                entity_type="Booking",
                entity_id=str(booking.id)
            ))
        
        await db.commit()


async def process_overdue_allocations():
    logger.info("Running process_overdue_allocations...")
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        today = now.date()

        stmt = select(Allocation).where(
            Allocation.status == "Active",
            Allocation.expected_return_date < today,
            Allocation.actual_return_date.is_(None),
            Allocation.overdue_alert_sent_at.is_(None)
        )
        result = await db.execute(stmt)
        allocations = result.scalars().all()

        for alloc in allocations:
            if alloc.employee_id:
                await create_notification(
                    db=db,
                    user_id=alloc.employee_id,
                    type_="OverdueReturnAlert",
                    message=f"Alert: Your allocated asset is overdue for return since {alloc.expected_return_date}.",
                    entity_type="Allocation",
                    entity_id=str(alloc.id),
                )
            alloc.overdue_alert_sent_at = now
            if alloc.employee_id:
                db.add(ActivityLog(
                    user_id=alloc.employee_id,
                    action="overdue_return_alert_sent",
                    entity_type="Allocation",
                    entity_id=str(alloc.id)
                ))

        await db.commit()


async def process_overdue_maintenance():
    logger.info("Running process_overdue_maintenance...")
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        stmt = select(MaintenanceRequest).where(
            MaintenanceRequest.status.in_(["Pending", "Approved", "TechnicianAssigned", "InProgress"]),
            MaintenanceRequest.updated_at < seven_days_ago,
            MaintenanceRequest.overdue_alert_sent_at.is_(None)
        )
        result = await db.execute(stmt)
        requests = result.scalars().all()

        if requests:
            # Find AssetManagers and Admins to notify
            mgr_stmt = select(Employee).where(
                Employee.role.in_(["AssetManager", "Admin"]),
                Employee.is_deleted.is_(False)
            )
            mgr_result = await db.execute(mgr_stmt)
            managers = mgr_result.scalars().all()

            for req in requests:
                for mgr in managers:
                    await create_notification(
                        db=db,
                        user_id=mgr.id,
                        type_="OverdueMaintenance",
                        message=f"Overdue Maintenance Alert: Request for asset {req.asset_id} has been open for > 7 days.",
                        entity_type="MaintenanceRequest",
                        entity_id=str(req.id),
                    )
                req.overdue_alert_sent_at = now
                if managers:
                    db.add(ActivityLog(
                        user_id=managers[0].id,
                        action="overdue_maintenance_alert_sent",
                        entity_type="MaintenanceRequest",
                        entity_id=str(req.id)
                    ))

        await db.commit()
