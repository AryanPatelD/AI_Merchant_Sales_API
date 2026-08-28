# AI Merchant Sales API

AI Merchant Sales API is an AI-native commerce backend designed to make merchants directly discoverable and transactable by autonomous AI buyers.

Instead of requiring an AI agent to scrape websites or interact with traditional user interfaces, the system exposes structured, machine-readable APIs for merchant discovery, product search, inventory availability, quote generation, checkout, Razorpay payment processing, and order tracking.

The platform follows a secure commerce workflow with expiring quotes, atomic inventory reservation, idempotent transactional operations, Razorpay webhook verification, API authentication, and audit logging.

### Core Flow

AI Buyer → Merchant Discovery → Product Search → Availability → Quote → Checkout → Razorpay Payment → Verified Webhook → Order Status

### Key Features

- AI-commerce discovery through `/.well-known/ai-commerce`
- Structured product catalog with stable SKU identifiers
- Product search and filtering
- Real-time inventory availability
- Time-bound and reproducible quotes
- Transaction-safe checkout and inventory reservation
- Razorpay Test Mode payment integration
- Razorpay webhook signature verification
- Idempotency protection against duplicate orders and payments
- Order status and fulfillment tracking
- API authentication, rate limiting, and audit logs

The goal is to demonstrate a reusable, secure, and model-agnostic commerce protocol that allows any capable AI agent to interact with a merchant programmatically.
