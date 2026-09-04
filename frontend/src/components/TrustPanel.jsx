import { useState } from 'react'

const TRUST_FEATURES = [
  {
    icon: '🔑',
    title: 'API Authentication',
    status: 'Configurable',
    description: 'Protected operations require an active API key when authentication is enabled.',
    marker: '01',
  },
  {
    icon: '♻️',
    title: 'Idempotency',
    status: 'Active',
    description: 'Retries on transactional endpoints return the stored result instead of creating duplicates.',
    marker: '02',
  },
  {
    icon: '🔒',
    title: 'Atomic Inventory Reservation',
    status: 'Enabled',
    description: 'Checkout revalidates and reserves stock in the same database transaction as order creation.',
    marker: '03',
  },
  {
    icon: '⏱',
    title: 'Expiring Quotes',
    status: 'Enforced',
    description: 'Quotes have a controlled validity window and are checked before checkout.',
    marker: '04',
  },
  {
    icon: '✓',
    title: 'Verified Razorpay Webhooks',
    status: 'Enabled',
    description: 'Verified webhook signatures, not browser callbacks, drive payment and order status changes.',
    marker: '05',
  },
  {
    icon: '📜',
    title: 'Audit Logging',
    status: 'Configurable',
    description: 'When enabled, API activity records the client, endpoint, request ID, and response status.',
    marker: '06',
  },
]

function TrustPanel() {
  const [showDetails, setShowDetails] = useState(false)

  return (
    <section className="trust-panel" aria-labelledby="trust-panel-title">
      <div className="trust-heading">
        <p className="eyebrow">Built for accountable automation</p>
        <h2 id="trust-panel-title">Why is this safe for autonomous AI buyers?</h2>
        <p>Each transaction is bounded by server-side validation, traceability, and verified state changes.</p>
      </div>
      <div className="trust-grid">
        {TRUST_FEATURES.map((feature) => (
          <article className="trust-feature" key={feature.title}>
            <span className="trust-marker" aria-hidden="true">{feature.icon}</span>
            <div>
              <h3>{feature.title}</h3>
              <span className="trust-status">{feature.status}</span>
              {showDetails && <p>{feature.description}</p>}
            </div>
          </article>
        ))}
      </div>
      <button className="trust-details-button" type="button" onClick={() => setShowDetails((current) => !current)}>
        {showDetails ? 'Hide safety architecture' : 'View safety architecture'} <span aria-hidden="true">→</span>
      </button>
    </section>
  )
}

export default TrustPanel