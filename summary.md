# AssetFlow — Project Summary

## Overview

AssetFlow is an Enterprise Asset & Resource Management System that digitizes the lifecycle of physical assets and shared resources for organizations.

Target organizations:
- Companies
- Schools
- Hospitals
- Factories
- Government agencies
- Any organization managing physical assets

The system focuses on:
- Asset lifecycle management
- Resource booking
- Asset allocation
- Maintenance workflow
- Audit workflow
- Notifications
- Analytics

No purchasing, invoicing or accounting modules.

---

# Goal

Build a responsive ERP application with:

- RBAC authentication
- Clean modular architecture
- Proper workflows
- Real-world validations
- Dashboard
- Reports

---

# User Roles

## Admin

Permissions

- Manage Departments
- Manage Asset Categories
- Manage Employee Directory
- Promote Employees to:
  - Department Head
  - Asset Manager
- Manage Audit Cycles
- View Organization Analytics

---

## Asset Manager

Permissions

- Register Assets
- Allocate Assets
- Approve Transfers
- Approve Maintenance
- Approve Asset Returns
- Resolve Audit Discrepancies

---

## Department Head

Permissions

- View Department Assets
- Approve Transfers
- Approve Allocations
- Book Shared Resources

---

## Employee

Permissions

- View Assigned Assets
- Book Shared Resources
- Raise Maintenance Requests
- Request Transfers
- Return Assets

---

# Core Modules

## 1 Authentication

Features

- Login
- Signup
- Forgot Password
- Session Validation

Rules

Signup always creates Employee role.

Only Admin can promote users.

Users cannot assign themselves elevated roles.

---

## 2 Dashboard

KPIs

- Assets Available
- Assets Allocated
- Maintenance Today
- Active Bookings
- Pending Transfers
- Upcoming Returns
- Overdue Returns

Quick Actions

- Register Asset
- Book Resource
- Raise Maintenance

---

## 3 Organization Setup

### Departments

Fields

- Name
- Parent Department
- Department Head
- Status

Operations

- Create
- Edit
- Deactivate

---

### Asset Categories

Examples

- Electronics
- Furniture
- Vehicles

Optional metadata

Example

Warranty Period

---

### Employee Directory

Fields

- Name
- Email
- Department
- Role
- Status

Admin promotes Employee → Department Head / Asset Manager.

---

## 4 Asset Registry

Fields

- Asset Tag (auto generated)
- Name
- Category
- Serial Number
- Acquisition Date
- Acquisition Cost
- Condition
- Location
- Documents
- Photos
- Shared / Bookable Flag

Search

- Asset Tag
- QR
- Category
- Status
- Department
- Location

Lifecycle States

- Available
- Allocated
- Reserved
- Under Maintenance
- Lost
- Retired
- Disposed

History

- Allocation History
- Maintenance History

---

## 5 Asset Allocation

Allocate asset to

- Employee
- Department

Optional

Expected Return Date

Conflict Rule

One asset cannot be allocated twice.

If already allocated

Show:

Current Holder

Offer:

Transfer Request

Transfer Workflow

Requested

↓

Approved

↓

Reallocated

Return Workflow

Returned

↓

Condition Check

↓

Available

Overdue Returns

Auto flagged

Shown on

Dashboard

Notifications

---

## 6 Resource Booking

Bookable Resources

- Meeting Rooms
- Equipment
- Vehicles

Calendar View

Booking Status

- Upcoming
- Ongoing
- Completed
- Cancelled

Overlap Rule

Bookings cannot overlap.

Example

9-10 booked

9:30-10:30 ❌

10-11 ✅

Support

- Cancel
- Reschedule
- Reminder Notification

---

## 7 Maintenance

Raise Request

Fields

- Asset
- Issue
- Priority
- Photo

Workflow

Pending

↓

Approved / Rejected

↓

Technician Assigned

↓

In Progress

↓

Resolved

Rules

Approval changes asset status

Available

↓

Under Maintenance

Resolution changes status

Under Maintenance

↓

Available

Maintenance history retained.

---

## 8 Asset Audit

Create Audit Cycle

Fields

- Scope
- Department
- Location
- Date Range

Assign Auditors

Auditor marks

- Verified
- Missing
- Damaged

System generates

Discrepancy Report

Closing audit updates asset status

Example

Missing

↓

Lost

Audit history retained.

---

## 9 Reports

Analytics

- Asset Utilization
- Idle Assets
- Maintenance Frequency
- Department Allocation
- Assets Near Retirement
- Booking Heatmap

Export

- Reports

---

## 10 Notifications

Examples

- Asset Assigned
- Transfer Approved
- Maintenance Approved
- Booking Reminder
- Booking Cancelled
- Overdue Return
- Audit Flagged

Maintain complete audit log

Who

What

When

---

# Business Rules

## Authentication

- Signup creates Employee only.
- Only Admin assigns elevated roles.

---

## Asset Rules

Asset lifecycle

Available

Allocated

Reserved

Under Maintenance

Lost

Retired

Disposed

Only Available assets can be allocated.

---

## Allocation Rules

One asset

One owner.

Duplicate allocation blocked.

Transfer required.

---

## Booking Rules

No overlapping bookings.

Calendar validation required.

---

## Maintenance Rules

Approval required before maintenance.

Approved

↓

Under Maintenance

Resolved

↓

Available

---

## Audit Rules

Audit cycles are scheduled.

Assets verified individually.

Missing assets generate discrepancy reports.

Confirmed missing assets become Lost.

---

## Return Rules

Returned assets require condition notes.

Return changes status to Available.

Overdue returns automatically flagged.

---

# Expected Database Tables

Users

Departments

Employees

Roles

AssetCategories

Assets

AssetHistory

Allocations

TransferRequests

Bookings

MaintenanceRequests

AuditCycles

AuditItems

Notifications

ActivityLogs

---

# Suggested Folder Structure

frontend/
backend/

backend/modules/

auth

users

departments

categories

assets

allocations

bookings

maintenance

audits

notifications

reports

dashboard

---

# APIs (Suggested)

Auth

POST /login

POST /signup

POST /forgot-password

Departments

CRUD

Categories

CRUD

Employees

CRUD

Assets

CRUD

Allocation

Allocate

Transfer

Return

Booking

Create

Update

Cancel

Maintenance

Create

Approve

Resolve

Audit

Create Cycle

Assign Auditor

Submit Audit

Close Audit

Dashboard

KPIs

Reports

Analytics

Notifications

List

Mark Read

---

# Success Criteria

Must Have

- RBAC
- Authentication
- Dashboard
- Asset CRUD
- Allocation
- Resource Booking
- Maintenance Workflow
- Audit Workflow
- Reports
- Notifications
- Activity Logs

Nice to Have

- QR Code Search
- Charts
- Mobile Responsive UI
- Better Dashboard
- Advanced Filters

---

# End-to-End Workflow

Admin

↓

Create Departments

↓

Create Categories

↓

Create Employees

↓

Promote Roles

↓

Asset Manager registers Asset

↓

Asset Available

↓

Allocate Asset

↓

Employee Uses Asset

↓

Book Shared Resources

↓

Raise Maintenance

↓

Approve Maintenance

↓

Asset Under Maintenance

↓

Resolve Maintenance

↓

Asset Available

↓

Run Audit Cycle

↓

Generate Discrepancy Report

↓

Notifications

↓

Dashboard Updates

↓

Reports

---

# Tech Priorities

1. Authentication + RBAC
2. Database schema
3. Asset CRUD
4. Allocation
5. Booking
6. Maintenance
7. Audit
8. Dashboard
9. Notifications
10. Reports

Everything revolves around Assets. Every module should reference the Asset entity as the central object.
