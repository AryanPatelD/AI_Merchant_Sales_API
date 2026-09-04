import { useState } from 'react'
import { discoverMerchant } from '../services/api.js'

function MerchantDiscovery({ onDiscovered, onContinue, onFailed }) {
  const [merchant, setMerchant] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isDiscovered, setIsDiscovered] = useState(false)

  async function handleDiscover() {
    setIsLoading(true)
    setError('')
    setIsDiscovered(false)

    try {
      setMerchant(await discoverMerchant())
      setIsDiscovered(true)
      onDiscovered()
    } catch (discoveryError) {
      setMerchant(null)
      onFailed?.()
      setError(discoveryError.message || 'Merchant discovery failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section className="discovery-panel" aria-labelledby="discovery-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Phase 2 / Merchant Discovery</p>
          <h2 id="discovery-title">Discover a transactable merchant</h2>
          <p className="panel-description">
            Read the merchant&apos;s machine-readable commerce manifest.
          </p>
        </div>
        <button
          className="discover-button"
          type="button"
          onClick={handleDiscover}
          disabled={isLoading}
        >
          {isLoading ? 'Discovering...' : 'Discover Merchant'}
        </button>
      </div>

      <div className="discovery-flow" aria-label="Merchant discovery flow">
        <div className="flow-step">
          <span className="flow-number">01</span>
          <strong>AI agent</strong>
        </div>
        <span className="flow-arrow" aria-hidden="true">↓</span>
        <div className="flow-step">
          <span className="flow-number">02</span>
          <code>GET /.well-known/ai-commerce</code>
        </div>
        <span className="flow-arrow" aria-hidden="true">↓</span>
        <div className="flow-step">
          <span className="flow-number">03</span>
          <strong>Capabilities discovered</strong>
        </div>
      </div>

      <div className="endpoint-row">
        <div>
          <span className="endpoint-label">Request</span>
          <code>GET /.well-known/ai-commerce</code>
        </div>
        <span className="response-status">200 OK</span>
      </div>

      {error && (
        <div className="status-message error-message" role="alert">
          {error}
        </div>
      )}

      {merchant && (
        <div className="merchant-result" aria-live="polite">
          {isDiscovered && (
            <div className="success-message" role="status">
              <span className="success-icon" aria-hidden="true">✓</span>
              <div>
                <strong>200 OK · Merchant discovered</strong>
                <p>Manifest successfully read from merchant discovery endpoint.</p>
              </div>
            </div>
          )}

          <div className="merchant-identity">
            <span className="merchant-mark" aria-hidden="true">
              {merchant.merchant.slice(0, 1).toUpperCase()}
            </span>
            <div>
              <p className="result-label">Active merchant</p>
              <div className="merchant-name-row">
                <h3>{merchant.merchant}</h3>
                <span className="active-badge">ACTIVE</span>
              </div>
              <p className="merchant-id">
                <span>Merchant ID</span> {merchant.merchant_id}
              </p>
            </div>
          </div>

          <dl className="merchant-facts">
            <div>
              <dt>API version</dt>
              <dd>{merchant.api_version}</dd>
            </div>
            <div>
              <dt>Currency</dt>
              <dd>{merchant.currency}</dd>
            </div>
            <div>
              <dt>Country</dt>
              <dd>{merchant.country}</dd>
            </div>
          </dl>

          <div className="capability-section">
            <p className="result-label">Capabilities</p>
            <div className="capability-list">
              {merchant.capabilities.length > 0 ? (
                merchant.capabilities.map((capability) => (
                  <span className="capability" key={capability}>
                    {capability}
                  </span>
                ))
              ) : (
                <span className="empty-value">None reported</span>
              )}
            </div>
          </div>

          <div className="gateway-section">
            <p className="result-label">Payment gateway</p>
            <div className="gateway-list">
              {merchant.payment_gateways.length > 0 ? (
                merchant.payment_gateways.map((gateway) => (
                  <span className="gateway-badge" key={gateway}>
                    {gateway.charAt(0).toUpperCase() + gateway.slice(1)}
                  </span>
                ))
              ) : (
                <span className="empty-value">None reported</span>
              )}
            </div>
          </div>

          <div className="continue-row">
            <button className="continue-button" type="button" onClick={onContinue}>
              Continue to Search <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      )}
    </section>
  )
}

export default MerchantDiscovery