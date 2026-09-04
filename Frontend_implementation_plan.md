# AI Merchant Sales API — Judge-Facing Frontend Implementation Plan

## 1. Project Context

This project is an AI-native Merchant Sales API built for a hackathon.

The backend is already implemented and working.

The goal of the frontend is NOT to build a traditional e-commerce website.

The frontend exists primarily to help hackathon judges quickly understand and demonstrate the complete AI-commerce workflow.

The core workflow is:

AI Buyer
    ↓
Merchant Discovery
    ↓
Product Search
    ↓
Availability Check
    ↓
Quote Generation
    ↓
Checkout
    ↓
Razorpay Payment
    ↓
Verified Payment
    ↓
Order Status

The backend exposes APIs for:

- Merchant discovery
- Catalog
- Product search
- Availability
- Quote generation
- Checkout
- Razorpay payment
- Razorpay webhook processing
- Order status

The frontend should make this workflow visually understandable.

---

# 2. Technology Requirements

Use:

- React
- Vite
- JavaScript
- Normal CSS
- Native fetch()
- Existing backend APIs

Avoid adding unnecessary dependencies.

DO NOT add:

- Redux
- Next.js
- Tailwind unless already installed
- TypeScript conversion
- complex state libraries
- animation libraries
- authentication UI
- admin dashboard
- chatbot
- recommendation system
- vector search
- embeddings
- unnecessary backend modifications

The project has a very short deadline.

Simplicity, reliability and demo clarity are more important than advanced frontend architecture.

---

# 3. Important Development Rules

Before modifying code:

1. Inspect the existing project structure.
2. Inspect existing backend endpoints.
3. Inspect actual request and response schemas.
4. Do not invent API fields.
5. Do not change working backend behavior unless absolutely necessary.
6. Do not rewrite unrelated files.
7. Keep frontend API calls centralized.
8. Add loading states.
9. Add useful error states.
10. After each phase, stop and report what was changed.

Do NOT implement multiple phases at once.

Complete only the phase explicitly requested by the user.

After finishing a phase:

- list modified files
- describe what was implemented
- explain how to manually test it
- mention any issue discovered
- STOP

Wait for the next instruction.

---

# 4. Frontend Design Goal

The frontend should look like a modern AI-commerce demonstration console.

The judge should understand the project within approximately 20–30 seconds.

The page should communicate:

"Instead of an AI scraping a merchant website, an AI agent can directly discover and transact with a merchant using standardized machine-readable APIs."

The interface should visually represent:

Discover → Search → Availability → Quote → Checkout → Payment → Track

---

# 5. Main Layout

Use a single-page application.

Suggested overall structure:

--------------------------------------------------
AI Merchant Sales API

Making merchants directly transactable by AI agents

[Discover] → [Search] → [Availability]
→ [Quote] → [Checkout] → [Payment] → [Track]

--------------------------------------------------

Current Step

Main interactive content

--------------------------------------------------

Optional technical information:

Request
GET /search?q=wireless+mouse

Response
JSON response

--------------------------------------------------

Do not create separate pages unless there is a strong technical reason.

---

# 6. Suggested Frontend Structure

frontend/
│
├── src/
│   ├── components/
│   │   ├── Header.jsx
│   │   ├── CommerceStepper.jsx
│   │   ├── MerchantDiscovery.jsx
│   │   ├── ProductSearch.jsx
│   │   ├── Availability.jsx
│   │   ├── QuoteCard.jsx
│   │   ├── CheckoutForm.jsx
│   │   ├── PaymentSection.jsx
│   │   ├── OrderStatus.jsx
│   │   └── TrustPanel.jsx
│   │
│   ├── services/
│   │   └── api.js
│   │
│   ├── App.jsx
│   ├── App.css
│   └── main.jsx
│
├── .env.example
├── package.json
└── vite.config.js

This structure is a recommendation.

If an existing frontend structure already exists, preserve it instead of unnecessarily restructuring the whole project.

---

# 7. Environment Configuration

Use an environment variable for the backend base URL.

Example:

VITE_API_BASE_URL=http://127.0.0.1:8000

Never hard-code production URLs throughout components.

API calls should use:

import.meta.env.VITE_API_BASE_URL

Create or update:

frontend/.env.example

with:

VITE_API_BASE_URL=http://127.0.0.1:8000

Do not commit sensitive credentials.

---

# 8. API Integration Rule

Create:

src/services/api.js

Centralize API requests there.

For example:

discoverMerchant()

getCatalog()

searchProducts()

checkAvailability()

createQuote()

createCheckout()

createPayment()

getOrderStatus()

The exact parameters and payloads MUST be taken from the existing backend implementation.

Do not assume request schemas.

Inspect backend routes/Pydantic schemas before implementing each API call.

---

# ==================================================
# PHASE 1 — FRONTEND FOUNDATION
# ==================================================

## Goal

Create only the frontend shell.

Do NOT connect business APIs yet except optional health checking.

Implement:

- React/Vite setup
- global layout
- header
- project tagline
- commerce stepper
- main content area
- basic responsive styling
- environment configuration
- centralized API file skeleton

The top of the application should clearly display:

AI Merchant Sales API

Making merchants directly transactable by AI agents.

Show this workflow:

Discover
→ Search
→ Availability
→ Quote
→ Checkout
→ Payment
→ Track

Keep design modern but simple.

Do not spend excessive time on styling.

## Phase 1 Acceptance Criteria

- npm run dev works
- application loads successfully
- header is visible
- project explanation is visible
- commerce stepper is visible
- layout works on normal desktop screen
- API base URL comes from environment variable
- no backend business API integration yet
- no console errors

STOP after completing Phase 1.

---

# ==================================================
# PHASE 2 — MERCHANT DISCOVERY
# ==================================================

## Goal

Implement only Merchant Discovery.

Inspect the existing backend implementation for:

GET /.well-known/ai-commerce

Use the actual response schema.

Create a judge-friendly Merchant Discovery section.

Add a button:

Discover Merchant

When clicked:

1. show loading state
2. call the backend merchant discovery API
3. handle HTTP errors
4. display merchant information

Suggested presentation:

Merchant
TechStore

Currency
INR

Country
IN

API Version
1.0

Payment Gateway
Razorpay

Capabilities

✓ Catalog
✓ Search
✓ Availability
✓ Quote
✓ Checkout
✓ Payment
✓ Order Status

Do not hard-code merchant values.

Use the actual backend response.

Also optionally display:

GET /.well-known/ai-commerce

so judges understand that the AI discovers the merchant programmatically.

## Phase 2 Acceptance Criteria

- Discover Merchant button works
- real backend is called
- merchant data is not hardcoded
- loading state exists
- API failure displays friendly error
- capabilities are displayed dynamically
- page remains usable if request fails
- no unrelated modules modified

STOP after Phase 2.

---

# ==================================================
# PHASE 3 — PRODUCT SEARCH
# ==================================================

## Goal

Implement only Product Search.

Inspect the existing backend search route and schema first.

Use the actual query parameters supported by the backend.

Create:

"What does the AI buyer want?"

Search input example:

wireless mouse

Add only useful filters already supported by backend, such as:

- category
- brand
- min price
- max price

Do not create filters that the backend does not support.

On search:

1. show loading
2. call the real search API
3. render matching products
4. handle empty results
5. handle backend errors

Product cards should show useful fields such as:

- product name
- SKU
- brand
- category
- price
- currency

Each product should have:

Check Availability

Do not implement Availability API in this phase.

Store the selected product in React state so the next phase can use it.

If no results are found, display something similar to:

"No products matched the AI buyer's request."

Do NOT treat an empty result as a frontend error.

## Phase 3 Acceptance Criteria

- search calls real backend
- search results display correctly
- filters match backend-supported filters
- selected SKU is stored
- empty search result handled
- errors handled
- Check Availability button visually exists
- availability API not implemented yet

STOP after Phase 3.

---

# ==================================================
# PHASE 4 — AVAILABILITY
# ==================================================

## Goal

Implement only inventory availability checking.

Use the SKU selected during Product Search.

Inspect the existing backend availability endpoint.

Call the real endpoint.

Display:

IN STOCK / OUT OF STOCK

Available Quantity

Delivery ETA

Example:

✓ IN STOCK

Available
12 units

Estimated Delivery
2 days

If available, allow user to choose quantity.

Suggested:

Quantity

[-] 1 [+]

Add:

Generate Quote

Do NOT implement quote API yet.

If out of stock:

- clearly show OUT OF STOCK
- disable Generate Quote

Do not allow quantity greater than available stock from the frontend.

Backend validation must still remain authoritative.

## Phase 4 Acceptance Criteria

- selected SKU is used
- real availability endpoint called
- stock quantity shown
- ETA shown
- out-of-stock state handled
- quantity selector works
- invalid quantities prevented in UI
- Generate Quote exists
- quote API not implemented yet

STOP after Phase 4.

---

# ==================================================
# PHASE 5 — QUOTE ENGINE
# ==================================================

## Goal

Implement Quote Generation only.

Inspect the existing POST /quote request and response schemas.

Use selected:

- SKU
- quantity

Call the real backend.

Display the quote in a judge-friendly card.

Show whatever fields exist in backend, such as:

Quote ID

Product

Quantity

Subtotal

Discount

Tax

Shipping

Total

Currency

Expiry / Validity

Example:

--------------------------------

QUOTE CREATED

Wireless Mouse M1

Subtotal       ₹799.00
Discount         ₹0.00
Tax            ₹143.82
Shipping          ₹0.00

TOTAL           ₹942.82

Quote expires in approximately 5 minutes.

[Proceed to Checkout]

--------------------------------

Do not recalculate pricing in React.

Use values returned by the backend.

The backend is the source of truth.

Store quote_id for checkout.

If quote creation fails because of:

- unavailable inventory
- invalid quantity
- product issue

show the backend error clearly.

## Phase 5 Acceptance Criteria

- real /quote endpoint called
- correct SKU and quantity sent
- quote values come from backend
- frontend does not calculate total itself
- quote_id stored
- expiry displayed
- error handling works
- Proceed to Checkout available
- checkout not implemented yet

STOP after Phase 5.

---

# ==================================================
# PHASE 6 — CHECKOUT
# ==================================================

## Goal

Implement only Checkout and Order Creation.

Inspect backend checkout schema before implementing.

Create a compact buyer form.

Use only fields required by the backend.

Suggested sections:

Buyer Details

Name
Email
Phone

Shipping Address

Address Line 1
Address Line 2
City
State
Postal Code
Country

Use the existing quote_id.

Call:

POST /checkout

Display:

ORDER CREATED

Order ID
xxxxxxxx

Status
PENDING_PAYMENT

Total
₹xxx.xx

Then provide:

Pay with Razorpay

Store order_id for payment and tracking.

Do not implement payment yet.

Prevent accidental multiple frontend submissions by disabling the button while request is running.

Do NOT attempt to replace backend idempotency protection.

## Phase 6 Acceptance Criteria

- buyer form validates required fields
- real checkout endpoint called
- quote_id reused
- loading state prevents repeated clicks
- order_id stored
- order status displayed
- backend validation errors shown
- Pay button visible
- payment not implemented yet

STOP after Phase 6.

---

# ==================================================
# PHASE 7 — RAZORPAY PAYMENT
# ==================================================

## Goal

Integrate the existing payment workflow.

DO NOT create a custom payment gateway implementation.

Inspect the backend:

POST /payment

and existing Razorpay integration.

Understand:

- what backend returns
- how Razorpay checkout is currently initialized
- whether a Razorpay key ID needs to be exposed to the frontend
- how payment success is reconciled
- how webhook processing works

Never expose:

- Razorpay key secret
- Razorpay webhook secret
- database credentials

Only expose values that are safe for browser usage.

When the user clicks:

Pay with Razorpay

1. create/initiate backend payment
2. launch Razorpay test checkout if required
3. display payment processing state
4. after client checkout completes, do NOT automatically claim that payment is verified unless backend confirms it
5. refresh/fetch order or payment status from backend

Clearly distinguish:

Payment initiated

from:

Payment verified

The project treats verified backend/webhook state as authoritative.

Suggested UI:

PAYMENT INITIATED

Waiting for verified payment confirmation...

Then after confirmed backend state:

✓ PAYMENT VERIFIED

Payment Status
CAPTURED

Order Status
PAID

## Phase 7 Acceptance Criteria

- backend payment endpoint works
- Razorpay test flow opens
- secrets are not present in frontend
- frontend does not blindly trust client payment success
- verified backend state is displayed
- failed payment has a clear UI state
- duplicate payment click is prevented while request is running

STOP after Phase 7.

---

# ==================================================
# PHASE 8 — ORDER STATUS
# ==================================================

## Goal

Implement order tracking.

Use current order_id automatically when available.

Also allow manual order ID lookup for judge demonstration if useful.

Inspect the backend order-status response.

Display actual backend values.

Create a simple order lifecycle visualization.

Possible lifecycle:

PENDING_PAYMENT
↓
PAID
↓
CONFIRMED
↓
PROCESSING
↓
SHIPPED
↓
OUT_FOR_DELIVERY
↓
DELIVERED

Do not assume every status exists.

Use statuses supported by backend.

Display available data such as:

- order ID
- order status
- payment status
- tracking number
- courier
- ETA
- delivery date

Only display fields that exist.

## Phase 8 Acceptance Criteria

- real order status endpoint called
- current order automatically trackable
- manual lookup works if implemented
- unknown order handled
- payment status visible when available
- order state visually understandable
- no fake tracking information

STOP after Phase 8.

---

# ==================================================
# PHASE 9 — JUDGE-FACING TRUST PANEL
# ==================================================

## Goal

Add explanation only.

Do not add new backend features.

Create a section:

Why is this safe for autonomous AI buyers?

Display concise cards explaining existing backend features.

Possible cards:

API Authentication

Only authorized AI clients can access protected operations.

Idempotency

Repeated AI-agent retries do not create duplicate transactional actions.

Atomic Inventory Reservation

Inventory is revalidated and safely reserved during checkout.

Expiring Quotes

Commercial offers remain valid only for a limited time.

Verified Razorpay Webhooks

Client-side payment success is not trusted as the final source of truth.

Audit Logging

Important API actions can be traced.

Only claim capabilities that actually exist in backend.

## Phase 9 Acceptance Criteria

- section is visually clear
- descriptions are concise
- no false claims
- no backend changes
- no new dependencies

STOP after Phase 9.

---

# ==================================================
# PHASE 10 — AI BUYER JOURNEY
# ==================================================

## Goal

Create one visual summary for judges.

This should NOT introduce another agent framework.

Use data already generated during the user's interaction.

At the top show something such as:

AI Buyer Goal

"I need a wireless mouse under ₹1000."

Then show completed workflow steps:

✓ Merchant discovered
✓ Product found
✓ Availability verified
✓ Quote generated
✓ Order created
✓ Payment initiated
✓ Payment verified
✓ Order tracked

Only mark a step complete when the corresponding action actually succeeded.

Use React state already available.

Do not fake successful steps.

This is mainly a presentation layer.

## Phase 10 Acceptance Criteria

- judge can understand overall workflow immediately
- completed steps reflect real API calls
- failed steps are not shown as successful
- no backend changes
- no additional AI framework

STOP after Phase 10.

---

# ==================================================
# PHASE 11 — FINAL UI POLISHING
# ==================================================

## Goal

Improve presentation without changing architecture.

Focus only on:

- spacing
- typography
- button consistency
- cards
- status badges
- success states
- error states
- loading indicators
- responsive desktop layout
- visual hierarchy

Use a clean professional interface.

Avoid excessive animations.

Do not restructure working components unless necessary.

Do not introduce new major dependencies.

Ensure the judge can easily identify:

1. What the AI buyer wants
2. Which API step is currently happening
3. What data the merchant returned
4. Whether the action succeeded
5. What the next step is

## Phase 11 Acceptance Criteria

- no console errors
- no broken buttons
- consistent layout
- readable API states
- demo flow visually obvious
- no functionality regression

STOP after Phase 11.

---

# ==================================================
# PHASE 12 — FINAL END-TO-END TEST
# ==================================================

## Goal

Do NOT implement new features.

Run the complete system from frontend.

Test:

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
Payment
↓
Order Status

Check:

- no frontend console errors
- no CORS errors
- no undefined/null rendering problems
- no duplicate submissions
- API errors are visible
- loading states work
- IDs propagate correctly
- quote_id propagates to checkout
- order_id propagates to payment
- order_id propagates to tracking

Also test at least these failures:

1. Product search with no results
2. Out-of-stock product
3. Invalid quantity
4. Expired/invalid quote if practical
5. Invalid order ID
6. Payment failure if existing backend supports easy testing

DO NOT start adding features while doing final testing.

Only fix bugs that affect the demonstration.

After finishing, report:

- tests performed
- failures discovered
- bugs fixed
- remaining known limitations

STOP.

---

# ==================================================
# PHASE 13 — DEPLOYMENT CHECK
# ==================================================

## Goal

Prepare frontend for production deployment.

Use the existing deployment approach selected by the project owner.

Likely frontend host:

Vercel

The frontend must use:

VITE_API_BASE_URL=<deployed-backend-url>

Ensure the backend CORS configuration allows:

- local development frontend
- deployed frontend URL

Do not use localhost URLs in deployed frontend.

After deployment, test the actual deployed stack:

Deployed Frontend
↓
Deployed FastAPI
↓
PostgreSQL
↓
Razorpay Test Mode

Do not consider localhost testing sufficient.

Perform one successful end-to-end transaction on the deployed application.

STOP after deployment verification.