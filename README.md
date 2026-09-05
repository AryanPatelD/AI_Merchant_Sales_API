# AI Merchant Sales API

## AI-Native Commerce Infrastructure for Autonomous Buyers

**AI Merchant Sales API** is an AI-native commerce backend that enables merchants to become directly **discoverable, understandable, and transactable by autonomous AI agents**.

Traditional e-commerce platforms are designed primarily for humans. An AI agent usually has to navigate webpages, interpret HTML, scrape product information, and simulate button clicks before it can complete a purchase.

This project takes a different approach.

Instead of forcing AI agents to interact with a human-oriented interface, the merchant exposes a structured set of machine-readable commerce APIs that allow an AI buyer to programmatically:

**discover the merchant → search products → verify inventory → generate a quote → create an order → initiate payment → verify payment → track the order**

The goal is to demonstrate how merchants can participate in an emerging **agent-to-agent commerce ecosystem** through a reusable, secure, and model-agnostic API layer.

---

## Problem Statement

Most merchant websites are optimized for human interaction.

An AI buyer trying to purchase something must often:

- scrape webpage content,
- interpret changing HTML structures,
- understand UI elements,
- simulate clicks,
- extract prices manually,
- determine stock availability,
- and interact with checkout pages designed for humans.

This approach is fragile and difficult to standardize.

The **AI Merchant Sales API** removes this dependency on the frontend by exposing structured commerce capabilities directly through APIs.

Instead of:

```text
AI Agent
   ↓
Merchant Website
   ↓
HTML Scraping
   ↓
UI Interpretation
   ↓
Checkout Page
```

the system enables:

```text
AI Buyer
   ↓
AI Merchant Sales API
   ↓
Merchant Discovery
   ↓
Product Search
   ↓
Availability
   ↓
Quote
   ↓
Checkout
   ↓
Razorpay Payment
   ↓
Order Tracking
```

---

# Core Commerce Flow

```text
AI Buyer
   ↓
Merchant Discovery
   ↓
Product Search
   ↓
Inventory Availability
   ↓
Quote Generation
   ↓
Checkout
   ↓
Inventory Reservation
   ↓
Razorpay Payment
   ↓
Verified Razorpay Webhook
   ↓
Order Status
```

Each stage is exposed through structured APIs so that an AI agent can understand and execute the complete purchase workflow programmatically.

---

# Key Features

## 1. AI-Commerce Merchant Discovery

The API exposes a machine-readable discovery endpoint:

```http
GET /.well-known/ai-commerce
```

This allows an AI agent to identify the merchant and understand the commerce capabilities supported by the platform.

The manifest can describe information such as:

- merchant identity,
- supported currency,
- catalog capability,
- search capability,
- quote generation,
- checkout,
- payment,
- and order tracking.

This creates a simple discovery mechanism for AI-native commerce.

---

## 2. Structured Product Catalog

Products are exposed using stable **SKU identifiers** instead of relying on webpage elements or product URLs.

Example:

```text
sku_1042
sku_2051
sku_3098
```

Stable SKUs allow AI agents and backend systems to reliably reference products throughout the complete transaction lifecycle.

---

## 3. Product Search and Filtering

AI buyers can search the merchant catalog through structured API requests instead of scraping product pages.

The search layer can return information such as:

- product name,
- SKU,
- description,
- price,
- category,
- merchant,
- and inventory-related information.

---

## 4. Real-Time Inventory Availability

Before an AI buyer proceeds with a transaction, the system verifies the current inventory state.

This prevents an AI agent from purchasing products based on stale catalog information.

Availability checks act as an early validation step before quote generation and checkout.

---

## 5. Time-Bound and Reproducible Quotes

The platform generates structured quotes containing:

- selected products,
- quantities,
- unit price snapshots,
- subtotal,
- discounts,
- taxes,
- shipping charges,
- total payable amount,
- and quote expiration time.

Quotes are stored with price snapshots so that the same quote remains reproducible even if product pricing changes later.

Example lifecycle:

```text
ACTIVE
   ↓
CONSUMED
```

or

```text
ACTIVE
   ↓
EXPIRED
```

An expired quote cannot be used for checkout.

---

## 6. Transaction-Safe Checkout

Checkout performs inventory validation and order creation as a transactional operation.

A simplified workflow is:

```text
BEGIN TRANSACTION

Lock inventory

Recheck available stock

Reserve requested quantity

Create order

Create order items

Mark quote as consumed

COMMIT
```

If any critical operation fails, the transaction can be rolled back.

This prevents situations where an order is created without inventory being reserved or inventory is reduced without an order being successfully created.

---

## 7. Atomic Inventory Reservation

Inventory is validated again during checkout rather than trusting an earlier availability request.

This protects the platform from race conditions such as two buyers attempting to purchase the final available unit at approximately the same time.

The checkout transaction ensures that inventory reservation and order creation remain consistent.

---

## 8. Idempotency Protection

Commerce APIs can receive duplicate requests because of:

- network retries,
- client retries,
- AI-agent retries,
- timeout recovery,
- or repeated user actions.

The system supports **Idempotency Keys** for transactional operations.

Example:

```http
Idempotency-Key: checkout-123
```

If the same checkout request is submitted again with the same idempotency key, the API returns the previously created result rather than creating another order.

This protects against:

- duplicate orders,
- duplicate inventory reservations,
- and duplicate payment operations.

---

## 9. Razorpay Test Mode Integration

The project integrates **Razorpay Test Mode** for the payment lifecycle.

The application can:

```text
Create Order
   ↓
Create Razorpay Payment Order
   ↓
Customer Completes Test Payment
   ↓
Razorpay Sends Webhook
   ↓
Backend Verifies Webhook Signature
   ↓
Payment Marked as Verified
```

Test Mode is used so that the complete payment workflow can be demonstrated without processing real money.

---

## 10. Razorpay Webhook Verification

The backend does not trust a payment status simply because the frontend reports that payment was successful.

Instead, Razorpay sends a webhook event to the backend.

The backend verifies the webhook signature using the configured webhook secret before updating the payment state.

Conceptually:

```text
Razorpay Event
      ↓
Webhook Endpoint
      ↓
Signature Verification
      ↓
Valid?
   ↙       ↘
 Yes       No
 ↓          ↓
Process    Reject
Payment    Event
```

This creates a server-to-server verification mechanism for payment events.

---

## 11. Order Tracking

After payment processing, an AI buyer can retrieve the current state of an order programmatically.

For example:

```text
CREATED
   ↓
PAYMENT_PENDING
   ↓
PAID
   ↓
PROCESSING
   ↓
SHIPPED
   ↓
DELIVERED
```

This allows the AI agent to continue interacting with the merchant even after the initial purchase is complete.

---

## 12. API Authentication

Protected
