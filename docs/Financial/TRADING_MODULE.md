# TRADING_MODULE.md
# Enterprise Trading & Commercial Management Module Specification
Version: 1.0  
Status: Production Ready Specification  
Target: ERP Trading Companies
---
# 1. Purpose
The Trading Module manages all commercial activities for companies involved in buying, selling, distribution, import and export operations.
The module supports:
- Wholesale Companies
- Retail Companies
- Distribution Companies
- Importers
- Exporters
- Commercial Organizations
The module integrates with:
- Accounting Core
- Inventory Management
- Tax Engine
- CRM
- Procurement
- Sales
- Reporting Engine
- Workflow Engine
---
# 2. Trading Module Architecture

Customer / Market Demand

    |

Sales Process

    |

Order Management

    |

Inventory Reservation

    |

Delivery

    |

Invoice

    |

Accounting Posting

Purchase Flow:

Supplier

    |

Purchase Request

    |

Purchase Order

    |

Goods Receipt

    |

Supplier Invoice

    |

Accounting Posting

---
# 3. Trading Business Types
The module supports:
## Wholesale
Features:
- Bulk sales
- Customer credit limits
- Price lists
- Sales representatives
- Commission
---
## Retail
Features:
- Fast sales
- POS integration
- Immediate payment
- Customer loyalty
---
## Distribution
Features:
- Multiple warehouses
- Route management
- Sales territories
- Delivery planning
---
## Import / Export
Features:
- Foreign suppliers
- Customs documents
- Currency transactions
- International payments
---
# 4. Master Data
## 4.1 Product Master
Products are shared with Inventory.
Required fields:

Product Code

SKU

Name

Category

Brand

Unit

Purchase Price

Sales Price

Tax Category

Inventory Type

Product Types:

Stock Product

Service Product

Bundle Product

Imported Product

Consignment Product

---
# 4.2 Customer Management
Customer entity:

Customer ID

Name

Type

National ID

Tax ID

Address

Contact Information

Credit Limit

Payment Terms

Price List

Sales Territory

Customer Types:

Retail Customer

Wholesale Customer

Corporate Customer

Government Customer

International Customer

---
# 4.3 Supplier Management
Supplier entity:

Supplier ID

Name

Tax Information

Contact

Payment Terms

Currency

Bank Information

---
# 5. Sales Management
## 5.1 Sales Lifecycle

Lead

|

Quotation

|

Sales Order

|

Delivery

|

Invoice

|

Payment

---
# 5.2 Sales Quotation
Purpose:
Create commercial offers.
Fields:

Quotation Number

Customer

Date

Valid Until

Items

Prices

Discounts

Taxes

Terms

Status

Statuses:

Draft

Sent

Approved

Rejected

Expired

Converted

---
# 5.3 Sales Order
Main sales document.
Fields:

Order Number

Customer

Order Date

Warehouse

Items

Quantity

Price

Discount

Tax

Delivery Date

Payment Terms

Status

---
# 5.4 Sales Approval Workflow
Supports:
- Amount Based Approval
- Customer Based Approval
- Discount Based Approval
Example:

Order > 1 Billion IRR

    |

Manager Approval

    |

Finance Approval

    |

Release

---
# 6. Pricing Engine
The pricing engine supports:
## Price Lists
Examples:

Retail Price

Wholesale Price

VIP Customer Price

Export Price

---
## Dynamic Pricing Rules
Rules:

IF

Customer Type = Wholesale

AND

Quantity > 100

THEN

Apply Discount

---
## Discount Types
Supports:

Percentage Discount

Fixed Discount

Quantity Discount

Campaign Discount

Customer Specific Discount

---
# 7. Commission Engine
Supports sales commission.
Commission rules:

Sales Person

Product Category

Customer Type

Sales Amount

=

Commission

Examples:

Electronics Sales:

2% Commission

New Customer:

Additional 1%

Commission calculation:

Sales Invoice

    |

Commission Rule Engine

    |

Commission Record

    |

Payroll / Payment

---
# 8. Delivery Management
Supports:
- Warehouse Delivery
- Customer Delivery
- Multiple Shipment
Delivery document:

Delivery Number

Customer

Warehouse

Items

Quantity

Driver

Status

Statuses:

Created

Prepared

Shipped

Delivered

Cancelled

---
# 9. Purchase Management
## Purchase Lifecycle

Purchase Request

    |

Purchase Order

    |

Goods Receipt

    |

Supplier Invoice

    |

Payment

---
# 10. Purchase Order
Fields:

Supplier

Items

Quantity

Price

Currency

Delivery Date

Payment Terms

Approval Status

---
# 11. Goods Receipt
When goods arrive:
Inventory:

Increase Stock

Accounting:

Debit:

Inventory

Credit:

Goods Received Not Invoiced

---
# 12. Import / Export Management
Supports:
## Import Flow

Foreign Supplier

    |

Purchase Contract

    |

Shipment

    |

Customs

    |

Warehouse Receipt

Documents:

Proforma Invoice

Commercial Invoice

Packing List

Customs Documents

Shipping Documents

---
## Export Flow

Customer Order

    |

Export Documentation

    |

Shipment

    |

Invoice

    |

Payment

---
# 13. Currency Management
Supports:
- Multiple currencies
- Exchange rates
- Currency gain/loss
Example:
Foreign purchase:

Purchase Currency:

USD

Accounting Currency:

IRR

---
# 14. Return Management
## Sales Return
Flow:

Customer Return Request

    |

Inspection

    |

Stock Return

    |

Credit Note

Accounting:

Debit:

Sales Return

Credit:

Customer Receivable

---
## Purchase Return
Flow:

Return To Supplier

    |

Stock Reduction

    |

Supplier Credit

---
# 15. Tax Integration
Sales:

Sales Invoice

    |

VAT Calculation

    |

Electronic Invoice

    |

Accounting Posting

Purchase:

Supplier Invoice

    |

Input VAT

    |

Tax Record

---
# 16. Accounting Integration
## Sales Invoice

Debit:

Customer Receivable

Credit:

Sales Revenue

Credit:

VAT Payable

---
## Purchase Invoice

Debit:

Inventory / Expense

Debit:

Input VAT

Credit:

Supplier Payable

---
# 17. Reports
Required reports:
## Sales Reports
- Sales Summary
- Sales By Customer
- Sales By Product
- Sales Representative Performance
---
## Purchase Reports
- Purchase Summary
- Supplier Analysis
- Purchase Price History
---
## Inventory Reports
- Stock Availability
- Stock Turnover
- Slow Moving Items
---
## Commercial Reports
- Profit Margin
- Discount Analysis
- Commission Report
- Import Cost Analysis
---
# 18. Database Entities
Required tables:

customers

suppliers

products

sales_quotes

sales_orders

sales_order_lines

deliveries

sales_invoices

purchase_requests

purchase_orders

purchase_order_lines

goods_receipts

pricing_rules

discount_rules

commission_rules

commission_transactions

import_documents

export_documents

---
# 19. Django Application Structure

apps/

trading/

customers/
suppliers/
sales/
purchase/
pricing/
commission/
import_export/
reports/
api/
---
# 20. AI Agent Implementation Rules
AI Agent must:
Always:
- Use Trading Services
- Validate approval workflows
- Integrate with Inventory Engine
- Create accounting entries through Posting Engine
- Use Tax Engine
- Maintain document history
Never:
- Modify posted invoices
- Bypass approval rules
- Directly update inventory
- Hard-code pricing rules
---
# 21. Completion Criteria
The module is complete when:
✓ Sales lifecycle works  
✓ Purchase lifecycle works  
✓ Import/export supported  
✓ Pricing engine works  
✓ Commission works  
✓ Tax integrated  
✓ Accounting integrated  
✓ Inventory integrated  
✓ Reports available  
✓ AI implementation requires no assumptions  
---
# Document Status
Version: 1.0
Status: READY FOR IMPLEMENTATION