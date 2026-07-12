"""
app/models/__init__.py — Import all models so Alembic can discover them.
"""

from app.models.department import Department  # noqa: F401
from app.models.employee import Employee  # noqa: F401
from app.models.asset_category import AssetCategory  # noqa: F401
from app.models.asset import Asset  # noqa: F401
from app.models.allocation import Allocation  # noqa: F401
from app.models.transfer_request import TransferRequest  # noqa: F401
from app.models.booking import Booking  # noqa: F401
from app.models.maintenance_request import MaintenanceRequest  # noqa: F401
from app.models.audit_cycle import AuditCycle, AuditCycleAuditor  # noqa: F401
from app.models.audit_item import AuditItem  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.activity_log import ActivityLog  # noqa: F401
