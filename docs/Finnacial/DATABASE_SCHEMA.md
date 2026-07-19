# DATABASE_SCHEMA.md
# Enterprise ERP PostgreSQL Database Architecture
Version: 1.0  
Status: Production Database Blueprint  
Database Engine: PostgreSQL
---
# 1. Database Design Principles
The ERP database must support:
- Multi Company
- Multi Branch
- Multi Warehouse
- Multi Currency
- Multi Fiscal Year
- Audit Compliance
- Financial Integrity
- High Transaction Volume
Core principles:
1. Financial records are immutable.
2. Every business transaction must have audit information.
3. Every module owns its data.
4. Cross-module communication happens through services/events.
5. Database constraints enforce business integrity.
---
# 2. Database Architecture Overview

PostgreSQL ERP Database

public

|

+– organization

+– security

+– accounting

+– finance

+– sales

+– purchase

+– inventory

+– manufacturing

+– service

+– contracting

+– hr

+– payroll

+– asset

+– tax

+– reporting

+– audit

---
# 3. Common Audit Fields
Every business table must include:
```sql
id UUID PRIMARY KEY
created_at TIMESTAMP
updated_at TIMESTAMP
created_by UUID
updated_by UUID
is_active BOOLEAN
is_deleted BOOLEAN

Financial tables additionally require:

posted_at
posted_by
transaction_status
approval_status

⸻

4. Organization Schema

companies

Purpose:

Store legal entities.

Fields:

id
name
legal_name
national_id
tax_id
business_type
currency
fiscal_year_start
status

business_type:

MANUFACTURING
TRADING
SERVICE
CONTRACTING
HOLDING

⸻

branches

id
company_id
name
address
manager_id

⸻

warehouses

id
branch_id
name
code
warehouse_type

⸻

5. Security Schema

users

id
username
email
password_hash
status

roles

id
name
description

permissions

id
code
module
action

Example:

accounting.journal.create
invoice.approve
inventory.adjust

user_roles

user_id
role_id

⸻

6. Accounting Core Schema

Accounting is the central financial engine.

⸻

accounts

Chart of Accounts:

id
company_id
parent_id
code
name
account_type
level
is_control_account

account_type:

ASSET
LIABILITY
EQUITY
REVENUE
EXPENSE

⸻

account_dimensions

Supports:

* Cost Centers
* Projects
* Departments

id
type
name
code

⸻

journal_entries

Accounting document header:

id
company_id
document_number
document_date
source_module
description
status

source_module:

SALES
PURCHASE
INVENTORY
MANUFACTURING
PAYROLL
SERVICE

⸻

journal_lines

Double entry lines:

id
journal_id
account_id
debit
credit
cost_center_id
project_id
party_id

Validation:

SUM(DEBIT) = SUM(CREDIT)

⸻

7. Sales Schema

customers

id
company_id
name
tax_number
phone
address
credit_limit

⸻

sales_orders

id
customer_id
order_date
status
total_amount

⸻

sales_invoice

id
customer_id
invoice_number
invoice_date
subtotal
tax_amount
total_amount
status

⸻

sales_invoice_lines

invoice_id
product_id
quantity
unit_price
discount
tax

⸻

8. Purchase Schema

suppliers

id
company_id
name
tax_number
contact_info

⸻

purchase_orders

id
supplier_id
date
status

⸻

purchase_invoice

id
supplier_id
amount
tax
status

⸻

9. Inventory Schema

products

Master product table:

id
company_id
sku
name
product_type
unit
category_id

product_type:

RAW_MATERIAL
SEMI_FINISHED
FINISHED_GOOD
SERVICE

⸻

stock_transactions

Every movement:

id
product_id
warehouse_id
transaction_type
quantity
unit_cost
reference_type
reference_id

transaction_type:

PURCHASE_RECEIPT
SALE_ISSUE
PRODUCTION_CONSUMPTION
PRODUCTION_RECEIPT
TRANSFER
ADJUSTMENT

⸻

10. Manufacturing Schema

bill_of_materials

id
product_id
version
status

⸻

bom_lines

bom_id
material_id
quantity
waste_percentage

⸻

production_orders

id
product_id
planned_quantity
actual_quantity
start_date
end_date
status

⸻

production_material_consumption

production_order_id
material_id
quantity
cost

⸻

work_centers

id
name
capacity
hourly_cost

⸻

11. Service Schema

service_contracts

id
customer_id
start_date
end_date
sla_level
value

⸻

work_orders

id
contract_id
assigned_employee
status
estimated_time
actual_time

⸻

service_billing

id
work_order_id
amount
invoice_id

⸻

12. Contracting Schema

projects

id
customer_id
name
budget
start_date
end_date

⸻

contracts

id
project_id
contract_value
retention_percentage
status

⸻

project_costs

id
project_id
cost_type
amount

⸻

13. Tax Schema

tax_codes

id
code
name
rate
tax_type

⸻

tax_transactions

id
source_document
tax_code
tax_amount
status

⸻

electronic_invoices

id
invoice_id
tracking_code
submission_status
response

⸻

14. Payroll Schema

employees

id
company_id
person_id
employee_code

⸻

payroll_transactions

id
employee_id
period
gross_salary
tax
insurance
net_salary

⸻

15. Asset Management Schema

assets

id
name
category
purchase_date
cost
depreciation_method

⸻

depreciation_entries

asset_id
period
amount

⸻

16. Reporting Schema

Reports must be generated from:

* Transaction Tables
* Accounting Ledger
* Aggregation Tables

Recommended:

Operational Database
        |
Reporting Views
        |
BI Layer

⸻

17. PostgreSQL Optimization Rules

Indexes required:

* Foreign Keys
* Transaction Dates
* Document Numbers
* Company ID
* Status Fields

Large tables:

Recommended partitioning:

* journal_lines
* stock_transactions
* audit_logs

Partition key:

company_id + fiscal_year

⸻

18. Django ORM Mapping Rules

Each domain:

django_app
 |
models.py
 |
services.py
 |
repositories.py
 |
api.py

Business logic must NOT exist inside models.

⸻

19. Data Integrity Rules

Mandatory:

* No negative stock without permission.
* No unbalanced journal.
* No editing posted financial documents.
* Every approval must be logged.
* Every tax document must have traceability.

⸻

Document Status

Version: 1.0

Ready For:

* Django Backend Development
* API Design
* Migration Creation
* AI Coding Agent Implementation

