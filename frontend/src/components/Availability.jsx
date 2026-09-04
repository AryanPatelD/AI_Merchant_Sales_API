import { useEffect, useState } from 'react'
import { checkAvailability } from '../services/api.js'

function Availability({ selectedSku, productName, onBack, onGenerateQuote, onFailed }) {
  const [quantity, setQuantity] = useState(1)
  const [availability, setAvailability] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const stockAvailable = availability?.in_stock && availability.requested_quantity_available !== false
  const stockState = !availability ? '' : !availability.in_stock || availability.requested_quantity_available === false
    ? 'out-of-stock'
    : availability.available_quantity <= 5 ? 'low-stock' : 'in-stock'

  useEffect(() => {
    if (selectedSku) {
      loadAvailability(1)
    }
  }, [selectedSku])

  async function loadAvailability(requestedQuantity = quantity) {
    setIsLoading(true)
    setError('')

    try {
      const response = await checkAvailability(selectedSku, requestedQuantity)
      setAvailability(response)
    } catch (availabilityError) {
      setAvailability(null)
      onFailed?.()
      setError(availabilityError.message || 'Availability check failed')
    } finally {
      setIsLoading(false)
    }
  }

  function handleQuantityChange(event) {
    setQuantity(event.target.value === '' ? '' : Number(event.target.value))
  }

  function adjustQuantity(change) {
    const nextQuantity = Number(quantity || 0) + change
    const maximum = availability?.available_quantity
    setQuantity(Math.max(1, maximum ? Math.min(nextQuantity, maximum) : nextQuantity))
  }

  function handleCheck(event) {
    event.preventDefault()
    if (!Number.isInteger(quantity) || quantity < 1) {
      onFailed?.()
      setError('Quantity must be at least 1.')
      return
    }
    loadAvailability(quantity)
  }

  return (
    <section className="availability-panel" aria-labelledby="availability-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Step 3 of 7 <span>/ Availability</span></p>
          <h2 id="availability-title">Check product availability</h2>
          <p className="panel-description">Verify stock and estimated delivery before creating a quote.</p>
        </div>
        <span className="availability-heading-label">AVAILABILITY</span>
      </div>

      <div className="availability-product-card">
        <p className="result-label">Product</p>
        <h3>{productName || 'Selected product'}</h3>
        <p className="product-sku">SKU: {selectedSku}</p>
        <form className="quantity-form" onSubmit={handleCheck}>
          <label htmlFor="requested-quantity">Quantity</label>
          <button
            className="quantity-adjustment"
            type="button"
            onClick={() => adjustQuantity(-1)}
            disabled={isLoading || quantity <= 1 || availability?.available_quantity === 0}
            aria-label="Decrease quantity"
          >
            −
          </button>
          <input
            id="requested-quantity"
            type="number"
            min="1"
            value={quantity}
            onChange={handleQuantityChange}
            disabled={isLoading || availability?.available_quantity === 0}
          />
          <button
            className="quantity-adjustment"
            type="button"
            onClick={() => adjustQuantity(1)}
            disabled={isLoading || availability?.available_quantity === 0 || quantity >= availability?.available_quantity}
            aria-label="Increase quantity"
          >
            +
          </button>
        </form>
      </div>

      <details className="availability-request">
        <summary>&lt;/&gt; View API Request</summary>
        <code>GET /api/v1/availability<br />sku={selectedSku}<br />quantity={quantity}</code>
      </details>

      {error && <div className="status-message error-message" role="alert">{error}</div>}

      {availability && (
        <div className="availability-result" aria-live="polite">
          <div className={`stock-status ${stockState}`}>
            <span aria-hidden="true">{stockAvailable ? (stockState === 'low-stock' ? '⚠' : '✓') : '✕'}</span>
            {stockAvailable ? (stockState === 'low-stock' ? 'Low Stock' : 'In Stock') : 'Out of Stock'}
          </div>
          <div className="stock-summary">
            <strong>{availability.available_quantity} units available</strong>
            <span>Delivery in approximately {availability.eta_days} days</span>
          </div>
          <div className="availability-facts">
            <div>
              <span>Available quantity</span>
              <strong>{availability.available_quantity}</strong>
            </div>
            <div>
              <span>ETA</span>
              <strong>{availability.eta_days != null ? `${availability.eta_days} days` : 'Not provided'}</strong>
            </div>
            <div>
              <span>SKU</span>
              <strong>{availability.sku}</strong>
            </div>
          </div>
          <div className="availability-actions">
            <button className="back-button availability-back" type="button" onClick={onBack}>
              ← Back to Product Search
            </button>
            <button
              className="quote-button"
              type="button"
              onClick={() => onGenerateQuote(quantity)}
              disabled={
                !availability.in_stock ||
                !Number.isInteger(quantity) ||
                quantity < 1 ||
                quantity > availability.available_quantity
              }
            >
              Generate Quote
            </button>
          </div>
        </div>
      )}
    </section>
  )
}

export default Availability