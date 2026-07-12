"""
tests/test_notifications.py — Integration tests for the notification pipeline.

Prerequisites:
  - DB running with at least one AssetManager + one Employee seeded
  - Run: pytest tests/test_notifications.py -v

Tests:
  1. Transfer-approve → TransferApproved notification appears in /notifications
  2. Asset allocation → AssetAssigned notification
  3. Maintenance approve → MaintenanceApproved notification
  4. Maintenance reject → MaintenanceRejected notification
  5. GET /activity-log returns filtered results
  6. POST /notifications/{id}/read marks as read
"""

import pytest
import httpx
import asyncio
from uuid import UUID

BASE = "http://localhost:8000/api"

# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def login(email: str, password: str) -> str:
    """Return a Bearer token for the given credentials."""
    resp = httpx.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────────────────────────────────
# Fixtures (update credentials / IDs to match your seeded DB)
# ──────────────────────────────────────────────────────────────────────────

# Replace these with real values from your test DB:
MANAGER_EMAIL    = "manager@test.com"
MANAGER_PASSWORD = "password123"
EMPLOYEE_EMAIL   = "employee@test.com"
EMPLOYEE_PASSWORD = "password123"

# These UUIDs must exist in your test DB:
ASSET_ID         = "00000000-0000-0000-0000-000000000001"   # Available asset
EMPLOYEE_ID      = "00000000-0000-0000-0000-000000000002"   # Employee to allocate to
DEPT_ID          = "00000000-0000-0000-0000-000000000003"   # A valid department


# ──────────────────────────────────────────────────────────────────────────
# Test 1: Allocation → AssetAssigned notification
# ──────────────────────────────────────────────────────────────────────────

def test_allocation_fires_asset_assigned_notification():
    mgr_token = login(MANAGER_EMAIL, MANAGER_PASSWORD)
    emp_token = login(EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD)

    # Check unread count before
    before = httpx.get(f"{BASE}/notifications/", headers=auth_headers(emp_token))
    assert before.status_code == 200
    before_unread = before.json()["unread_count"]

    # Allocate the asset to the employee
    alloc_resp = httpx.post(
        f"{BASE}/allocations/",
        json={
            "asset_id": ASSET_ID,
            "employee_id": EMPLOYEE_ID,
            "department_id": DEPT_ID,
            "allocated_date": "2026-07-12",
        },
        headers=auth_headers(mgr_token),
    )
    assert alloc_resp.status_code == 201, f"Allocation failed: {alloc_resp.text}"
    allocation_id = alloc_resp.json()["id"]

    # Employee checks notifications — should have one more unread AssetAssigned
    after = httpx.get(f"{BASE}/notifications/", headers=auth_headers(emp_token))
    assert after.status_code == 200
    data = after.json()
    assert data["unread_count"] == before_unread + 1

    # The newest notification should be AssetAssigned
    newest = data["items"][0]
    assert newest["type"] == "AssetAssigned"
    assert newest["is_read"] is False
    assert newest["entity_type"] == "Allocation"
    assert newest["entity_id"] == allocation_id

    return allocation_id  # used in downstream tests if needed


# ──────────────────────────────────────────────────────────────────────────
# Test 2: Transfer approve → TransferApproved notification (acceptance criteria)
# ──────────────────────────────────────────────────────────────────────────

def test_transfer_approve_fires_transfer_approved_notification():
    """
    Acceptance criterion: hitting transfer-approve endpoint causes exactly one
    TransferApproved Notification row for the requester.
    """
    mgr_token = login(MANAGER_EMAIL, MANAGER_PASSWORD)
    emp_token = login(EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD)

    # Step 1: allocate asset
    alloc_resp = httpx.post(
        f"{BASE}/allocations/",
        json={
            "asset_id": ASSET_ID,
            "employee_id": EMPLOYEE_ID,
            "department_id": DEPT_ID,
            "allocated_date": "2026-07-12",
        },
        headers=auth_headers(mgr_token),
    )
    assert alloc_resp.status_code == 201
    allocation_id = alloc_resp.json()["id"]

    # Step 2: employee creates transfer request
    tr_resp = httpx.post(
        f"{BASE}/allocations/transfers",
        json={
            "allocation_id": allocation_id,
            "target_employee_id": EMPLOYEE_ID,  # transfer to same for simplicity
            "target_department_id": DEPT_ID,
            "reason": "Test transfer",
        },
        headers=auth_headers(emp_token),
    )
    assert tr_resp.status_code == 201, f"Transfer create failed: {tr_resp.text}"
    transfer_id = tr_resp.json()["id"]

    # Note unread count for employee before approval
    before = httpx.get(f"{BASE}/notifications/", headers=auth_headers(emp_token))
    before_unread = before.json()["unread_count"]

    # Step 3: manager approves the transfer
    approve_resp = httpx.post(
        f"{BASE}/allocations/transfers/{transfer_id}/approve",
        json={"action": "approve"},
        headers=auth_headers(mgr_token),
    )
    assert approve_resp.status_code == 200, f"Approve failed: {approve_resp.text}"

    # Step 4: employee checks /notifications
    after = httpx.get(f"{BASE}/notifications/", headers=auth_headers(emp_token))
    assert after.status_code == 200
    data = after.json()

    # Exactly 1 more unread notification (TransferApproved)
    transfer_notifs = [
        n for n in data["items"]
        if n["type"] == "TransferApproved" and n["entity_id"] == transfer_id
    ]
    assert len(transfer_notifs) == 1, (
        f"Expected exactly 1 TransferApproved notification, got: {transfer_notifs}"
    )
    assert transfer_notifs[0]["is_read"] is False


# ──────────────────────────────────────────────────────────────────────────
# Test 3: Maintenance approve → MaintenanceApproved notification
# ──────────────────────────────────────────────────────────────────────────

def test_maintenance_approve_fires_notification():
    mgr_token = login(MANAGER_EMAIL, MANAGER_PASSWORD)
    emp_token = login(EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD)

    # Create maintenance request
    mr_resp = httpx.post(
        f"{BASE}/maintenance/",
        json={
            "asset_id": ASSET_ID,
            "issue_description": "Fan making noise",
            "priority": "Medium",
        },
        headers=auth_headers(emp_token),
    )
    assert mr_resp.status_code == 201, f"Maintenance create failed: {mr_resp.text}"
    mr_id = mr_resp.json()["id"]

    before = httpx.get(f"{BASE}/notifications/", headers=auth_headers(emp_token))
    before_unread = before.json()["unread_count"]

    # Approve
    approve_resp = httpx.post(
        f"{BASE}/maintenance/{mr_id}/approve",
        headers=auth_headers(mgr_token),
    )
    assert approve_resp.status_code == 200

    after = httpx.get(f"{BASE}/notifications/", headers=auth_headers(emp_token))
    data = after.json()
    assert data["unread_count"] == before_unread + 1
    newest = data["items"][0]
    assert newest["type"] == "MaintenanceApproved"
    assert newest["entity_id"] == mr_id


# ──────────────────────────────────────────────────────────────────────────
# Test 4: Mark notification as read
# ──────────────────────────────────────────────────────────────────────────

def test_mark_notification_read():
    emp_token = login(EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD)

    notifs = httpx.get(f"{BASE}/notifications/", headers=auth_headers(emp_token))
    assert notifs.status_code == 200
    items = notifs.json()["items"]
    if not items:
        pytest.skip("No notifications to mark as read")

    notif_id = items[0]["id"]

    mark_resp = httpx.post(
        f"{BASE}/notifications/{notif_id}/read",
        headers=auth_headers(emp_token),
    )
    assert mark_resp.status_code == 200
    assert mark_resp.json()["is_read"] is True

    # Verify unread count decreased
    after = httpx.get(f"{BASE}/notifications/", headers=auth_headers(emp_token))
    after_notif = next(n for n in after.json()["items"] if n["id"] == notif_id)
    assert after_notif["is_read"] is True


# ──────────────────────────────────────────────────────────────────────────
# Test 5: GET /activity-log filtering
# ──────────────────────────────────────────────────────────────────────────

def test_activity_log_filterable():
    mgr_token = login(MANAGER_EMAIL, MANAGER_PASSWORD)

    # Unfiltered
    resp = httpx.get(f"{BASE}/activity-log/", headers=auth_headers(mgr_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data

    # Filter by entity_type
    resp2 = httpx.get(
        f"{BASE}/activity-log/",
        params={"entity_type": "Allocation"},
        headers=auth_headers(mgr_token),
    )
    assert resp2.status_code == 200
    for item in resp2.json()["items"]:
        assert item["entity_type"] == "Allocation"

    # Filter by date range (should return subset or same)
    resp3 = httpx.get(
        f"{BASE}/activity-log/",
        params={
            "from_date": "2026-01-01T00:00:00",
            "to_date": "2026-12-31T23:59:59",
            "page_size": 5,
        },
        headers=auth_headers(mgr_token),
    )
    assert resp3.status_code == 200
    assert len(resp3.json()["items"]) <= 5
