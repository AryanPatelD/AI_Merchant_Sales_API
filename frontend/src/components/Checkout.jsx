import { useState } from 'react'
import { createCheckout } from '../services/api.js'

function Checkout({ quoteId, quoteAddress, onBack, onOrderCreated, onProceedToPayment, onFailed }) {
  const [buyer, setBuyer] = useState({ name: '', email: '', phone: '' })
  const [shippingAddress, setShippingAddress] = useState({
    recipient_name: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: quoteAddress.state,
    postal_code: '',
    country: quoteAddress.country,
  })
  const [order, setOrder] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPostalConfirmation, setShowPostalConfirmation] = useState(false)
  const [orderIdCopied, setOrderIdCopied] = useState(false)
  const [idempotencyKey] = useState(() => crypto.randomUUID())
  const [submittedCheckout, setSubmittedCheckout] = useState(null)
  const [idempotencyResult, setIdempotencyResult] = useState('')

  function updateBuyer(event) {
    const { name, value } = event.target
    setBuyer((currentBuyer) => ({ ...currentBuyer, [name]: value }))
  }

  function updateAddress(event) {
    const { name, value } = event.target
    setShippingAddress((currentAddress) => ({ ...currentAddress, [name]: value }))
  }

  async function copyOrderId() {
    await navigator.clipboard.writeText(order.order_id)
    setOrderIdCopied(true)
    window.setTimeout(() => setOrderIdCopied(false), 1600)
  }

  async function submitCheckout() {
    setShowPostalConfirmation(false)
    if (!buyer.name.trim() || (!buyer.email.trim() && !buyer.phone.trim())) {
      onFailed?.()
      setError('Enter your name and either an email or phone number.')
      return
    }
    if (!shippingAddress.recipient_name.trim() || !shippingAddress.address_line1.trim() || !shippingAddress.city.trim() || !shippingAddress.state.trim() || !shippingAddress.postal_code.trim() || !shippingAddress.country.trim()) {
      onFailed?.()
      setError('Complete all required shipping fields.')
      return
    }

    setIsLoading(true)
    setError('')
    setIdempotencyResult('')
    const checkoutRequest = {
      buyer: {
        name: buyer.name.trim(),
        email: buyer.email.trim() || null,
        phone: buyer.phone.trim() || null,
      },
      shippingAddress: {
        ...shippingAddress,
        recipient_name: shippingAddress.recipient_name.trim(),
        address_line1: shippingAddress.address_line1.trim(),
        address_line2: shippingAddress.address_line2.trim() || null,
        city: shippingAddress.city.trim(),
        state: shippingAddress.state.trim(),
        postal_code: shippingAddress.postal_code.trim(),
        country: shippingAddress.country.trim(),
      },
    }
    setSubmittedCheckout(checkoutRequest)
    try {
      const response = await createCheckout(quoteId, checkoutRequest.buyer, checkoutRequest.shippingAddress, idempotencyKey)
      setOrder(response)
      onOrderCreated(response)
    } catch (checkoutError) {
      setOrder(null)
      onFailed?.()
      setError(checkoutError.message || 'Checkout failed')
    } finally {
      setIsLoading(false)
    }
  }

  async function retrySameCheckout() {
    if (!order || !submittedCheckout || isLoading) return

    setIsLoading(true)
    setError('')
    setIdempotencyResult('')
    try {
      const response = await createCheckout(quoteId, submittedCheckout.buyer, submittedCheckout.shippingAddress, idempotencyKey)
      setOrder(response)
      onOrderCreated(response)
      setIdempotencyResult(
        response.order_id === order.order_id
          ? 'Duplicate request detected. No second order was created.'
          : 'The retry returned a different order ID. Review the backend response.'
      )
    } catch (retryError) {
      setError(retryError.message || 'Retry failed')
    } finally {
      setIsLoading(false)
    }
  }

  function handleCheckout(event) {
    event.preventDefault()
    if (!buyer.name.trim() || (!buyer.email.trim() && !buyer.phone.trim())) {
      onFailed?.()
      setError('Enter your name and either an email or phone number.')
      return
    }
    if (!shippingAddress.recipient_name.trim() || !shippingAddress.address_line1.trim() || !shippingAddress.city.trim() || !shippingAddress.state.trim() || !shippingAddress.postal_code.trim() || !shippingAddress.country.trim()) {
      onFailed?.()
      setError('Complete all required shipping fields.')
      return
    }
    setError('')
    setShowPostalConfirmation(true)
  }

  return (
    <section className="checkout-panel" aria-labelledby="checkout-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Phase 6 / Checkout</p>
          <h2 id="checkout-title">Create your order</h2>
          <p className="panel-description">Use the active quote to create an order for payment.</p>
        </div>
      </div>

      <form className="checkout-form" onSubmit={handleCheckout}>
        <div className="checkout-section">
          <p className="result-label">Buyer details</p>
          <div className="checkout-fields">
            <label>Name *<input name="name" value={buyer.name} onChange={updateBuyer} autoComplete="name" /></label>
            <label>Email or phone *<input name="email" type="email" value={buyer.email} onChange={updateBuyer} placeholder="Email address" autoComplete="email" /></label>
            <label>Phone<input name="phone" type="tel" value={buyer.phone} onChange={updateBuyer} placeholder="Optional if email is provided" autoComplete="tel" /></label>
          </div>
        </div>
        <div className="checkout-section">
          <p className="result-label">Shipping</p>
          <div className="checkout-fields">
            <label>Recipient name *<input name="recipient_name" value={shippingAddress.recipient_name} onChange={updateAddress} autoComplete="shipping name" /></label>
            <label>Address line 1 *<input name="address_line1" value={shippingAddress.address_line1} onChange={updateAddress} autoComplete="shipping address-line1" /></label>
            <label>Address line 2<input name="address_line2" value={shippingAddress.address_line2} onChange={updateAddress} autoComplete="shipping address-line2" /></label>
            <label>City *<input name="city" value={shippingAddress.city} onChange={updateAddress} autoComplete="shipping address-level2" /></label>
            <label>State / Province / Region *<input name="state" value={shippingAddress.state} onChange={updateAddress} autoComplete="shipping address-level1" /></label>
            <label>Postal code *<input name="postal_code" value={shippingAddress.postal_code} onChange={updateAddress} autoComplete="shipping postal-code" /></label>
            <label>Country *<input name="country" value={shippingAddress.country} onChange={updateAddress} autoComplete="shipping country-name" /></label>
          </div>
        </div>
        <div className="phase-actions">
          <button className="back-button availability-back" type="button" onClick={onBack}>
            ← Back to Quote
          </button>
          <button className="quote-button checkout-submit" type="submit" disabled={isLoading || !quoteId}>
            {isLoading ? 'Creating Order...' : 'Create Order'}
          </button>
        </div>
      </form>

      {error && <div className="status-message error-message" role="alert">{error}</div>}

      {showPostalConfirmation && (
        <div className="postal-modal-backdrop" role="presentation">
          <div className="postal-modal" role="dialog" aria-modal="true" aria-labelledby="postal-confirmation-title">
            <p className="eyebrow">Delivery confirmation</p>
            <h3 id="postal-confirmation-title">Check your postal code</h3>
            <p>
              Delivery availability and timing depend on postal code <strong>{shippingAddress.postal_code}</strong>.
            </p>
            <p className="postal-modal-note">Please confirm it is correct before creating your order.</p>
            <div className="postal-modal-actions">
              <button className="back-button availability-back" type="button" onClick={() => setShowPostalConfirmation(false)}>
                Edit details
              </button>
              <button className="quote-button" type="button" onClick={submitCheckout} disabled={isLoading}>
                {isLoading ? 'Creating Order...' : 'Confirm Postal Code'}
              </button>
            </div>
          </div>
        </div>
      )}

      {order && (
        <div className="order-result" aria-live="polite">
          <div className="quote-result-heading">
            <div>
              <p className="result-label">ORDER CREATED</p>
              <h3>Ready for payment</h3>
            </div>
            <span className="quote-status">{order.status}</span>
          </div>
          <div className="order-id-row">
            <p className="quote-id"><span>Order ID</span> {order.order_id}</p>
            <button className="copy-order-id" type="button" onClick={copyOrderId}>
              {orderIdCopied ? 'Copied' : 'Copy Order ID'}
            </button>
          </div>
          <div className="quote-facts">
            <div><span>Subtotal</span><strong>{order.currency} {order.subtotal}</strong></div>
            <div><span>Tax</span><strong>{order.currency} {order.tax}</strong></div>
            <div><span>Shipping</span><strong>{order.currency} {order.shipping}</strong></div>
          </div>
          <div className="order-total"><span>Total</span><strong>{order.currency} {order.total}</strong></div>
          <button className="quote-button" type="button" onClick={() => onProceedToPayment(order)}>
            Pay with Razorpay
          </button>
          <div className="idempotency-demo">
            <p className="result-label">Advanced / Judge Demo</p>
            <p>Repeated agent retries do not create duplicate orders.</p>
            <p className="idempotency-key">Key: {idempotencyKey}</p>
            <button className="copy-order-id" type="button" onClick={retrySameCheckout} disabled={isLoading}>
              {isLoading ? 'Retrying...' : 'Retry Same Checkout'}
            </button>
            {idempotencyResult && <p className="idempotency-result" role="status">{idempotencyResult}</p>}
            <p className="idempotency-order">Existing Order ID: <strong>{order.order_id}</strong></p>
          </div>
        </div>
      )}
    </section>
  )
}

export default Checkout