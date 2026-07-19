# TAX_AND_LEGAL_RULES_IRAN.md
# Iran Tax Compliance & Legal Accounting Engine Specification
Version: 1.0  
Status: Production Ready Specification  
Target: Iranian ERP Tax Compliance Layer
---
# 1. Purpose
This document defines the complete architecture of the Iranian tax compliance engine for an ERP system.
The Tax Engine must support:
- Value Added Tax (VAT)
- Electronic Invoicing
- Samaneh Moadian Integration
- Corporate Income Tax
- Payroll Tax
- Withholding Tax
- Tax Reports
- Tax Audit Trail
- Industry Specific Tax Rules
The system must be configurable and rule-based.
Tax logic must never be hard-coded inside business modules.
---
# 2. Tax Engine Position in ERP Architecture

Business Module

(Sales / Purchase / Service / Manufacturing / Contracting)

            |
            v

Tax Classification Engine

            |
            v

Tax Rule Engine

            |
            v

Tax Calculation Engine

            |
            v

Accounting Posting Engine

            |
            v

Tax Reporting Engine

---
# 3. Supported Business Domains
The Tax Engine must support:
## Manufacturing Companies
Examples:
- Raw Material Purchase VAT
- Production Cost Tax Impact
- Finished Goods Sales VAT
- Scrap Transactions
## Trading Companies
Examples:
- Purchase VAT
- Sales VAT
- Import Related Taxes
- Distribution Transactions
## Service Companies
Examples:
- Service Invoice VAT
- Contract Service Tax
- Withholding Tax
## Contracting Companies
Examples:
- Progress Billing
- Retention Amount
- Advance Payment
- Contract Tax Rules
---
# 4. Tax Master Data
## 4.1 Tax Category
Defines tax behavior.
Example:

TAXABLE

EXEMPT

ZERO_RATE

SPECIAL_RULE

Database:

tax_categories

id

code

name

description

status

---
# 4.2 Tax Code
Defines applicable tax.
Example:

VAT_NORMAL

VAT_EXEMPT

WITHHOLDING_SERVICE

Database:

tax_codes

id

category_id

code

name

rate

effective_date

---
# 4.3 Tax Rule
Business logic container.
Example:

IF

Transaction = Sales Invoice

AND

Item Category = Taxable

THEN

Apply VAT Rule

Database:

tax_rules

id

name

condition

action

version

active

---
# 5. VAT Engine
## 5.1 VAT Components
System supports:

Output VAT

Input VAT

VAT Payable

VAT Receivable

VAT Adjustment

---
# 5.2 Sales Invoice VAT Flow
Process:

Sales Invoice Created

    |

Tax Classification

    |

VAT Calculation

    |

Accounting Posting

Accounting:

Debit:

Customer Receivable

Credit:

Sales Revenue

Credit:

VAT Payable

---
# 5.3 Purchase Invoice VAT Flow
Process:

Purchase Invoice

    |

Tax Validation

    |

VAT Calculation

    |

Posting

Accounting:

Debit:

Inventory / Expense

Debit:

Input VAT

Credit:

Supplier Payable

---
# 6. VAT Settlement Engine
At tax period closing:
Formula:

VAT Payable

=

Output VAT

Input VAT

System generates:
- VAT Settlement Report
- Accounting Adjustment
- Tax Filing Data
---
# 7. Electronic Invoice Architecture
The ERP must support electronic invoice lifecycle:

Invoice Creation

    |

Validation

    |

Electronic Format Generation

    |

Submission

    |

Government Response

    |

Tracking Storage

---
# 8. Electronic Invoice Data Model
## Invoice Header
Required:

Invoice Number

Invoice Date

Invoice Type

Seller Information

Buyer Information

Payment Method

Currency

Total Amount

---
## Seller Data

Tax ID

National ID

Economic Code

Branch

Address

---
## Buyer Data

Customer Type

National ID

Economic Code

Address

---
## Invoice Items

Product/Service Code

Description

Quantity

Unit

Price

Discount

Tax Rate

Tax Amount

---
# 9. Electronic Invoice Types
Supported:

NORMAL

CORRECTION

RETURN

CANCELLATION

SPECIAL

---
# 10. Samaneh Moadian Integration Layer
Architecture:

ERP

|

Tax Adapter

|

Electronic Invoice Service

|

External Tax Platform

Requirements:
- Authentication Management
- Submission Queue
- Retry Mechanism
- Error Handling
- Response Storage
- Tracking Number Management
---
# 11. Corporate Income Tax Engine
Purpose:
Calculate taxable income.
Formula:

Accounting Profit

Non Deductible Expenses

Allowed Deductions

=

Taxable Income

---
# 12. Tax Adjustment Management
Supports:
## Deductible Expenses
Examples:
- Operational Costs
- Approved Business Expenses
- Documented Expenses
## Non Deductible Expenses
Examples:
- Unsupported Expenses
- Personal Expenses
- Missing Documents
---
# 13. Payroll Tax Engine
Calculation flow:

Gross Salary

Benefits

Insurance

=

Tax Base

    |

Income Tax Calculation

Supports:
- Employee Tax Profiles
- Monthly Calculation
- Annual Adjustment
- Tax Reports
---
# 14. Withholding Tax Engine
Supported cases:
- Service Payments
- Contract Payments
- Professional Services
Flow:

Payment Request

    |

Withholding Rule

    |

Tax Deduction

    |

Tax Liability

---
# 15. Industry Tax Templates
## Manufacturing Template
Rules:
- Material Purchase VAT
- Production Cost Allocation
- Finished Goods Sale VAT
---
## Trading Template
Rules:
- Purchase VAT
- Sales VAT
- Inventory Related Tax
---
## Service Template
Rules:
- Service Revenue Tax
- Contractor Payments
- Withholding
---
## Contracting Template
Rules:
- Progress Invoice
- Retention
- Advance Payment
---
# 16. Tax Reports
Required reports:
## VAT Reports
- Sales VAT Report
- Purchase VAT Report
- VAT Settlement
## Income Tax Reports
- Taxable Income
- Tax Adjustment
- Tax Calculation
## Payroll Reports
- Employee Tax Summary
- Monthly Tax Report
## Audit Reports
- Tax Transaction History
- Document Traceability
---
# 17. Accounting Integration
Every tax event creates accounting entries.
Example:
## Output VAT

Debit:

Customer

Credit:

Sales Revenue

Credit:

VAT Payable

## Input VAT

Debit:

Input VAT

Credit:

Supplier Payable

---
# 18. Database Entities
Required tables:

tax_categories

tax_codes

tax_rates

tax_rules

tax_transactions

electronic_invoices

tax_reports

tax_adjustments

---
# 19. Django Application Architecture

apps/

tax/

models/
rules/
calculators/
integrations/
reports/
validators/
api/
---
# 20. AI Agent Implementation Rules
AI Agent must:
DO:
- Use Tax Rule Engine
- Keep tax history
- Validate documents
- Maintain audit trail
- Separate legal rules from business logic
DO NOT:
- Hard-code tax rates
- Modify finalized tax documents
- Bypass accounting posting
---
# 21. Completion Criteria
This module is considered complete when:
✓ All ERP modules can calculate tax  
✓ Tax rules are configurable  
✓ Electronic invoices are supported  
✓ Accounting integration exists  
✓ Reports are generated  
✓ Audit history is preserved  
✓ AI agents can implement without assumptions  
---
# Document Status
Version: 1.0
Status: READY FOR IMPLEMENTATION