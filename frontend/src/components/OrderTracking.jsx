import { useEffect, useState } from 'react'
import { getOrderStatus } from '../services/api.js'

const LIFECYCLE = [
  'PENDING_PAYMENT',
  'PAYMENT_FAILED',
  'PAID',
  'CONFIRMED',
  'PROCESSING',
  'SHIPPED',
  'OUT_FOR_DELIVERY',
  'DELIVERED',
  'CANCELLED',
  'RETURN_REQUESTED',
  'RETURNED',
  'REFUND_PENDING',
  'REFUNDED',
]

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function OrderTracking({ currentOrderId, onBack, onOrderTracked, onFailed }) {
  const [orderId, setOrderId] = useState(currentOrderId || '')
  const [orderStatus, setOrderStatus] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function lookupOrder(id = orderId) {
    const normalizedOrderId = id.trim()
    if (!normalizedOrderId) {
      onFailed?.()
      setError('Enter an order ID to check its status.')
      return
    }
    if (!UUID_PATTERN.test(normalizedOrderId)) {
      onFailed?.()
      setError('Enter a valid order ID in UUID format.')
      setOrderStatus(null)
      return
    }

    setIsLoading(true)
    setError('')
    try {
      const response = await getOrderStatus(normalizedOrderId)
      setOrderStatus(response)
      onOrderTracked?.(response)
    } catch (statusError) {
      setOrderStatus(null)
      onFailed?.()
      setError(statusError.message || 'Could not load order status')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (!currentOrderId) return undefined
    const lookupTimeout = window.setTimeout(() => lookupOrder(currentOrderId), 0)
    return () => window.clearTimeout(lookupTimeout)
  }, [currentOrderId])

  const historyByStatus = new Map((orderStatus?.status_history || []).map((entry) => [entry.status, entry]))

  return (
    <section className="tracking-panel" aria-labelledby="tracking-title">
      <button className="back-button availability-back" type="button" onClick={onBack}>← Back to Payment</button>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Phase 8 / Order Status</p>
          <h2 id="tracking-title">Track the order lifecycle</h2>
          <p className="panel-description">Order progress is read from the backend status service.</p>
        </div>
      </div>

      <form className="tracking-search" onSubmit={(event) => { event.preventDefault(); lookupOrder() }}>
        <label htmlFor="tracking-order-id">Order ID</label>
        <div className="tracking-search-row">
          <input id="tracking-order-id" value={orderId} onChange={(event) => setOrderId(event.target.value)} placeholder="Paste an order ID" />
          <button className="quote-button" type="submit" disabled={isLoading}>
            {isLoading ? 'Checking...' : 'Check Status'}
          </button>
        </div>
      </form>

      {error && <div className="status-message error-message" role="alert">{error}</div>}

      {orderStatus && (
        <div className="tracking-result" aria-live="polite">
          <div className="tracking-summary">
            <div>
              <p className="result-label">Current order status</p>
              <h3>{orderStatus.order_status}</h3>
            </div>
            {orderStatus.payment_status && <span className="quote-status">Payment: {orderStatus.payment_status}</span>}
          </div>
          <p className="quote-id"><span>Order ID</span> {orderStatus.order_id}</p>

          <div className="lifecycle" aria-label="Order lifecycle">
            {LIFECYCLE.map((status, index) => {
              const current = status === orderStatus.order_status
              const completed = historyByStatus.has(status) && !current
              const entry = historyByStatus.get(status)
              return (
                <div className={'lifecycle-step' + (completed ? ' is-reached' : '') + (current ? ' is-current' : '')} key={status}>
                  <span className="lifecycle-dot" aria-hidden="true">{completed ? '✓' : current ? '●' : index + 1}</span>
                  <strong>{status}</strong>
                  {entry && <time dateTime={entry.changed_at}>{new Date(entry.changed_at).toLocaleDateString()}</time>}
                </div>
              )
            })}
          </div>

          <div className="tracking-facts">
            <div><span>ETA</span><strong>{orderStatus.eta_days !== null ? `${orderStatus.eta_days} days` : 'Not available'}</strong></div>
            <div><span>Estimated delivery</span><strong>{orderStatus.estimated_delivery_date || 'Not available'}</strong></div>
            {orderStatus.tracking?.courier_name && <div><span>Courier</span><strong>{orderStatus.tracking.courier_name}</strong></div>}
            {orderStatus.tracking?.tracking_number && <div><span>Tracking number</span><strong>{orderStatus.tracking.tracking_number}</strong></div>}
          </div>
          {orderStatus.tracking?.shipment_status && <p className="payment-note">Shipment status: {orderStatus.tracking.shipment_status}</p>}
        </div>
      )}
    </section>
  )
}

export default OrderTracking
