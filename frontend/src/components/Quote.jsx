import { useState } from 'react'
import { createQuote } from '../services/api.js'

const COUNTRY_REGIONS = {
  India: [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
    'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim',
    'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
    'West Bengal',
  ],
  'United States': [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
    'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
    'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
    'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
    'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
    'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota',
    'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
    'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
    'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming',
    'Washington, D.C.',
  ],
  'United Kingdom': [
    'England', 'Scotland', 'Wales', 'Northern Ireland',
  ],
  Canada: [
    'Alberta', 'British Columbia', 'Manitoba', 'New Brunswick',
    'Newfoundland and Labrador', 'Nova Scotia', 'Ontario', 'Prince Edward Island',
    'Quebec', 'Saskatchewan',
  ],
  Australia: [
    'Australian Capital Territory', 'New South Wales', 'Northern Territory',
    'Queensland', 'South Australia', 'Tasmania', 'Victoria', 'Western Australia',
  ],
}

function Quote({ selectedSku, quantity, onBack, onQuoteCreated, onProceedToCheckout, onFailed }) {
  const [shippingAddress, setShippingAddress] = useState({ state: '', country: '' })
  const [statePage, setStatePage] = useState(0)
  const [quote, setQuote] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  function updateAddress(event) {
    const { name, value } = event.target
    setShippingAddress((currentAddress) => ({ ...currentAddress, [name]: value }))
  }

  function updateCountry(event) {
    setShippingAddress((currentAddress) => ({
      ...currentAddress,
      country: event.target.value,
      state: '',
    }))
    setStatePage(0)
  }

  async function handleQuote(event) {
    event.preventDefault()
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) {
      onFailed?.()
      setError('Quantity must be a whole number between 1 and 1000.')
      return
    }
    if (!shippingAddress.state.trim() || !shippingAddress.country.trim()) {
      onFailed?.()
      setError('Enter a shipping state and country to generate the quote.')
      return
    }

    setIsLoading(true)
    setError('')
    try {
      const response = await createQuote(selectedSku, quantity, {
        state: shippingAddress.state.trim(),
        country: shippingAddress.country.trim(),
      })
      setQuote(response)
      onQuoteCreated(response.quote_id)
    } catch (quoteError) {
      setQuote(null)
      onFailed?.()
      setError(quoteError.message || 'Quote creation failed')
    } finally {
      setIsLoading(false)
    }
  }

  const item = quote?.items?.[0]

  return (
    <section className="quote-panel" aria-labelledby="quote-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Phase 5 / Quote Engine</p>
          <h2 id="quote-title">Create a backend-priced quote</h2>
          <p className="panel-description">Pricing, tax, shipping, and validity come from the merchant API.</p>
        </div>
      </div>

      <div className="idempotency-badge" role="status">
        <strong>🛡 Idempotency Protected</strong>
        <span>Repeated requests with the same key will not create duplicate transactions.</span>
      </div>

      <form className="quote-form" onSubmit={handleQuote}>
        <div className="quote-selection">
          <span>Selected SKU</span>
          <strong>{selectedSku}</strong>
          <span>Quantity</span>
          <strong>{quantity}</strong>
        </div>
        <div className="quote-address-fields">
          <label>
            Country
            <select name="country" value={shippingAddress.country} onChange={updateCountry}>
              <option value="">Select country</option>
              {Object.keys(COUNTRY_REGIONS).map((country) => <option key={country} value={country}>{country}</option>)}
            </select>
          </label>
          <label>
            State / Province / Region
            {shippingAddress.country && (
              <div className="region-select-wrap">
                {COUNTRY_REGIONS[shippingAddress.country].length > 10 && (
                  <div className="region-page-controls">
                    <button type="button" onClick={() => setStatePage((page) => page - 1)} disabled={statePage === 0}>
                      Previous 10
                    </button>
                    <span>{statePage + 1} / {Math.ceil(COUNTRY_REGIONS[shippingAddress.country].length / 10)}</span>
                    <button type="button" onClick={() => setStatePage((page) => page + 1)} disabled={(statePage + 1) * 10 >= COUNTRY_REGIONS[shippingAddress.country].length}>
                      Next 10
                    </button>
                  </div>
                )}
                <select name="state" value={shippingAddress.state} onChange={updateAddress}>
                  <option value="">Select a state / region</option>
                  {COUNTRY_REGIONS[shippingAddress.country].slice(statePage * 10, statePage * 10 + 10).map((region) => (
                    <option key={region} value={region}>{region}</option>
                  ))}
                </select>
              </div>
            )}
          </label>
        </div>
        <div className="phase-actions">
          <button className="back-button availability-back" type="button" onClick={onBack}>
            ← Back to Availability
          </button>
          <button
            className="quote-button quote-submit"
            type="submit"
            disabled={isLoading || !selectedSku || !Number.isInteger(quantity) || quantity < 1 || quantity > 1000}
          >
            {isLoading ? 'Generating...' : 'Generate Quote'}
          </button>
        </div>
      </form>

      {error && <div className="status-message error-message" role="alert">{error}</div>}

      {quote && item && (
        <div className="quote-result" aria-live="polite">
          <div className="quote-result-heading">
            <div>
              <p className="result-label">Quote created</p>
              <h3>{item.product_name}</h3>
            </div>
            <span className="quote-status">{quote.status}</span>
          </div>
          <p className="quote-id"><span>Quote ID</span> {quote.quote_id}</p>
          <div className="quote-facts">
            <div><span>Quantity</span><strong>{item.quantity}</strong></div>
            <div><span>Currency</span><strong>{quote.currency}</strong></div>
            <div><span>Valid for</span><strong>{Math.round(quote.valid_for_seconds / 60)} min</strong></div>
          </div>
          <dl className="quote-pricing">
            <div><dt>Subtotal</dt><dd>{quote.currency} {quote.pricing.subtotal}</dd></div>
            <div><dt>Discount</dt><dd>{quote.currency} {quote.pricing.discount}</dd></div>
            <div><dt>Tax ({item.gst_rate}% GST)</dt><dd>{quote.currency} {quote.pricing.tax}</dd></div>
            <div><dt>Shipping</dt><dd>{quote.currency} {quote.pricing.shipping}</dd></div>
            <div className="quote-total"><dt>Total</dt><dd>{quote.currency} {quote.pricing.total}</dd></div>
          </dl>
          <div className="pricing-explanation">
            <p className="result-label">Pricing verification</p>
            <ul>
              {quote.pricing_explanation.map((explanation) => (
                <li key={explanation}>{explanation}</li>
              ))}
            </ul>
          </div>
          <p className="quote-expiry">
            Quote expires on {new Intl.DateTimeFormat('en-IN', {
              day: '2-digit',
              month: 'short',
              year: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
              timeZoneName: 'short',
            }).format(new Date(quote.expires_at))}
          </p>
          <button className="continue-button" type="button" onClick={() => onProceedToCheckout(shippingAddress)}>
            Proceed to Checkout →
          </button>
        </div>
      )}
    </section>
  )
}

export default Quote