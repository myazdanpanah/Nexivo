# ACCOUNTING_MODULE.md
# Enterprise Accounting Core Module Specification
Version: 1.0  
Status: Production Accounting Blueprint  
Target: ERP Financial Core
---
# 1. Module Purpose
Accounting Core is the financial heart of the ERP.
All operational modules must communicate with this module.
Supported business models:
- Manufacturing
- Trading
- Service
- Contracting
- Holding Companies
The Accounting Module is responsible for:
- General Ledger
- Subsidiary Ledger
- Journal Management
- Financial Statements
- Cost Accounting
- Budgeting
- Closing
- Audit Compliance
---
# 2. Accounting Architecture

Business Transaction

    |

Transaction Engine

    |

Accounting Posting Engine

    |

Journal Entry

    |

General Ledger

    |

Financial Reports

---
# 3. Accounting Principles
System must enforce:
## Double Entry Accounting
Every transaction:

Total Debit = Total Credit

Example:
Purchase Invoice:

Debit:
Inventory / Expense

Debit:
Input VAT

Credit:
Supplier Payable

---
# 4. Chart of Accounts Architecture
The system supports:

Account Tree

Level 1:
Account Class

Level 2:
Account Group

Level 3:
General Account

Level 4:
Subsidiary Account

Level 5:
Detail Account

Example:

1 Assets

11 Current Assets

   1101 Cash
   110101 Main Bank Account
---
# 5. Account Types
Supported:

ASSET

LIABILITY

EQUITY

REVENUE

EXPENSE

---
# 6. Accounting Dimensions
Every journal can have:
## Cost Center
Example:
- Production
- Marketing
- Administration
## Profit Center
Example:
- Branch
- Business Unit
## Project
Example:
- Construction Project
- Customer Contract
## Department
Example:
- HR
- Sales
---
# 7. Journal Engine
Core entity:

Journal Header

Journal Lines

---
# 7.1 Journal Header
Fields:

Document Number

Date

Fiscal Year

Source Module

Description

Reference Number

Status

Approval Status

---
# 7.2 Journal Lines
Fields:

Account

Debit

Credit

Cost Center

Project

Party

Currency

Description

---
# 8. Posting Engine
All modules create accounting documents through posting rules.
Architecture:

Sales Module

    |

Posting Rule

    |

Accounting Entry

No module is allowed to directly insert journal records.
---
# 9. Sales Accounting
## Sales Invoice
Transaction:

Customer Invoice

Debit:

Accounts Receivable

Credit:

Sales Revenue

Credit:

VAT Payable

---
## Sales Return

Debit:

Sales Return

Debit:

VAT Adjustment

Credit:

Customer Receivable

---
# 10. Purchase Accounting
## Purchase Invoice

Debit:

Inventory / Expense

Debit:

Input VAT

Credit:

Supplier Payable

---
## Purchase Return

Debit:

Supplier Payable

Credit:

Inventory

Credit:

VAT Adjustment

---
# 11. Inventory Accounting
Inventory events:
## Stock Receipt

Debit:

Inventory

Credit:

Goods Received Account

## Stock Issue

Debit:

COGS

Credit:

Inventory

---
# 12. Manufacturing Accounting
Manufacturing flow:

Raw Material

    ↓

Production WIP

    ↓

Finished Goods

---
## Material Consumption

Debit:

Production WIP

Credit:

Raw Material Inventory

---
## Production Completion

Debit:

Finished Goods Inventory

Credit:

Production WIP

---
## Manufacturing Cost Allocation
Costs:
- Material
- Labor
- Machine
- Overhead
Entry:

Debit:

Production Cost

Credit:

Cost Allocation Accounts

---
# 13. Service Accounting
Service transaction:

Service Invoice

Debit:

Customer Receivable

Credit:

Service Revenue

Service Cost:

Debit:

Service Cost

Credit:

Expense / Resource Cost

---
# 14. Contract Accounting
Supports:
- Project Cost
- Progress Billing
- Retention
- Advance Payment
Example:
Progress Invoice:

Debit:

Customer Receivable

Credit:

Project Revenue

---
# 15. Treasury Module Integration
Supports:
- Cash
- Bank
- Payment
- Receipt
- Transfer
Payment:

Debit:

Supplier Payable

Credit:

Bank

Receipt:

Debit:

Bank

Credit:

Customer Receivable

---
# 16. Cost Accounting
Supports:
## Direct Cost
- Material
- Labor
## Indirect Cost
- Electricity
- Rent
- Maintenance
## Allocation Methods
- Percentage
- Activity Based Costing
- Machine Hours
- Labor Hours
---
# 17. Financial Closing
## Monthly Closing
Process:

Validate Transactions

    |

Post Journals

    |

Calculate Adjustments

    |

Close Period

---
## Year End Closing
Includes:
- Revenue Closing
- Expense Closing
- Profit Transfer
- Opening Balance Creation
---
# 18. Financial Reports
## Standard Reports
### Balance Sheet
Shows:
- Assets
- Liabilities
- Equity
---
### Income Statement
Shows:
- Revenue
- Expenses
- Profit
---
### Cash Flow
Shows:
- Operating Cash
- Investment Cash
- Financing Cash
---
### Ledger Reports
- General Ledger
- Subsidiary Ledger
- Trial Balance
---
# 19. Audit Requirements
Every accounting action must record:

Created By

Created Date

Approved By

Approved Date

Source Document

Modification History

---
# 20. AI Implementation Rules
AI coding agents must:
## Never:
- Create unbalanced journals
- Modify posted transactions
- Bypass posting engine
## Always:
- Use accounting services
- Validate debit/credit
- Maintain audit trail
- Keep source document reference
---
# 21. Django Application Structure
Recommended:

apps/

accounting/

models/
services/
posting/
reports/
validators/
api/
---
# Document Status
Version: 1.0
Status:
READY FOR IMPLEMENTATION
Used By:
- Django Backend
- API Specification
- Workflow Engine
- AI Coding Agent