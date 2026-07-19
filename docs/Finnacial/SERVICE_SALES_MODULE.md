# SERVICE_SALES_MODULE.md
# Enterprise Service Sales Management Module Specification
Version: 1.0  
Status: READY FOR IMPLEMENTATION
---
# 1. Purpose
The Service Sales Module manages the selling of services as commercial products inside ERP.
This module is designed for companies where the primary business output is a service rather than a physical product.
Supported businesses:
- Travel Agencies
- Airlines Ticket Sellers
- Tour Operators
- Hotels
- Consulting Companies
- Training Companies
- SaaS Businesses
- Subscription Businesses
- Professional Services
The module is responsible for:
- Service Catalog
- Service Pricing
- Booking
- Reservation
- Availability Management
- Customer Billing
- Commission Management
- Supplier Settlement
- Revenue Recognition
---
# 2. Difference From Service Management
This module is NOT for after-sales service.
Example:
SERVICE SALES:

Customer

|

Buy Flight Ticket

|

Receive Service

SERVICE MANAGEMENT:

Customer

|

Buy Product

|

Warranty

|

Repair Request

---
# 3. Architecture

Service Catalog

    |

Pricing Engine

    |

Availability Engine

    |

Booking Engine

    |

Reservation

    |

Invoice

    |

Accounting

    |

Revenue Recognition

---
# 4. Service Product Model
Every service is treated as a sellable product.
Entity:

Service ID

Service Name

Category

Provider

Duration

Price Model

Tax Category

Accounting Account

Status

Service Types:

Flight Ticket

Hotel

Tour Package

Consulting

Subscription

Training

Insurance

---
# 5. Service Catalog
The catalog manages available services.
Features:
- Service categories
- Service attributes
- Availability rules
- Pricing rules
- Supplier connection
Example:

Category:

International Flight

Service:

Tehran → Istanbul Ticket

Provider:

Airline

---
# 6. Flight Ticket Sales
Flow:

Customer Request

    |

Search Flight

    |

Select Flight

    |

Passenger Information

    |

Reservation

    |

Payment

    |

Ticket Issue

    |

Invoice

Entities:

Flight

Route

Passenger

Ticket

PNR

Airline

Fare

---
# 7. Tour Package Management
Tour package contains multiple services.
Example:

Tour Package

Hotel

Flight

Transfer

Guide

Entities:

Tour Package

Tour Component

Destination

Duration

Supplier

Cost

Selling Price

---
# 8. Hotel Reservation
Supports:
- Room types
- Availability
- Check-in/out
- Supplier contracts
Entities:

Hotel

Room Type

Reservation

Guest

Rate Plan

---
# 9. Booking Engine
Booking lifecycle:

Draft

↓

Reserved

↓

Confirmed

↓

Paid

↓

Completed

↓

Cancelled

Booking contains:

Customer

Service

Date

Quantity

Price

Supplier

Status

---
# 10. Supplier Settlement
Supports:
- Airlines
- Hotels
- Tour Operators
- Service Providers
Flow:

Customer Payment

    |

ERP Revenue

    |

Supplier Payable

    |

Settlement

---
# 11. Commission Engine
Supports:
- Agent commission
- Salesperson commission
- Partner commission
Formula:

Selling Price

Supplier Cost

=

Gross Margin

Commission Based On Margin

---
# 12. Cancellation & Refund
Supports:
- Full cancellation
- Partial refund
- Penalty
- Supplier refund
Flow:

Cancellation Request

    |

Rule Evaluation

    |

Refund Calculation

    |

Accounting Adjustment

---
# 13. Revenue Recognition
Supports:
- Immediate recognition
- Deferred revenue
Example:
Annual Subscription:

Customer Payment

    |

Deferred Revenue

    |

Monthly Recognition

---
# 14. Accounting Integration
Sales:

Debit:

Customer Receivable

Credit:

Service Revenue

Credit:

VAT Payable

Supplier Cost:

Debit:

Cost Of Service

Credit:

Supplier Payable

---
# 15. Database Entities
Required tables:

services

service_categories

service_providers

bookings

booking_items

reservations

passengers

tickets

tour_packages

hotel_reservations

supplier_contracts

supplier_settlements

commission_rules

commission_transactions

refund_transactions

revenue_schedule

---
# 16. Django Structure

apps/

service_sales/

catalog/
booking/
reservation/
pricing/
suppliers/
commission/
revenue/
reports/
api/
---
# 17. Reports
Required reports:
Sales:
- Service Sales Report
- Booking Report
- Customer Revenue
Financial:
- Supplier Payable
- Commission Report
- Revenue Recognition Report
Operational:
- Booking Status
- Cancellation Report
---
# 18. AI Agent Rules
AI Agent must:
Always:
- Use Service Sales Services
- Validate booking rules
- Create accounting through Posting Engine
- Maintain booking history
Never:
- Modify confirmed bookings directly
- Bypass refund rules
- Change financial records manually
---
# Completion Criteria
✓ Service catalog works
✓ Booking works
✓ Reservation works
✓ Supplier settlement works
✓ Commission works
✓ Accounting integration works
✓ Reports available
✓ AI implementation requires no assumptions
---
# Document Status
Version: 1.0
READY FOR IMPLEMENTATION

پیام بعدی: SERVICE_MANAGEMENT_MODULE.md (گارانتی، تعمیرات، SLA و خدمات پس از فروش)