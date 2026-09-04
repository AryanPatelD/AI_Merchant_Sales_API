import { useState } from 'react'
import { checkAvailability, createCheckout, createQuote, discoverMerchant, getOrderStatus, searchProducts } from '../services/api.js'
import OrderTracking from './OrderTracking.jsx'
import Payment from './Payment.jsx'
import AIBuyerJourney from './AIBuyerJourney.jsx'

const INITIAL_PROGRESS = [
  { key: 'discovery', label: 'Merchant discovered', status: 'pending' },
  { key: 'search', label: 'Products searched', status: 'pending' },
  { key: 'selection', label: 'Product selected', status: 'pending' },
  { key: 'availability', label: 'Availability verified', status: 'pending' },
  { key: 'quote', label: 'Quote generated', status: 'pending' },
  { key: 'order', label: 'Order created', status: 'pending' },
  { key: 'consent', label: 'Waiting for payment authorization', status: 'pending' },
  { key: 'verification', label: 'Payment verification', status: 'pending' },
  { key: 'tracking', label: 'Order tracking', status: 'pending' },
]

function AgentMode() {
  const [goal, setGoal] = useState('wireless mouse')
  const [constraints, setConstraints] = useState({ maxPrice: '', category: '', brand: '', quantity: '1' })
  const [buyer, setBuyer] = useState({ name: '', email: '', phone: '' })
  const [shipping, setShipping] = useState({
    recipient_name: '', address_line1: '', address_line2: '', city: '', state: '', postal_code: '', country: '',
  })
  const [progress, setProgress] = useState(INITIAL_PROGRESS)
  const [isRunning, setIsRunning] = useState(false)
  const [phase, setPhase] = useState('form')
  const [error, setError] = useState('')
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [quote, setQuote] = useState(null)
  const [order, setOrder] = useState(null)

  function updateObject(setter, event) {
    const { name, value } = event.target
    setter((current) => ({ ...current, [name]: value }))
  }

  function setStepStatus(key, status) {
    setProgress((current) => current.map((step) => step.key === key ? { ...step, status } : step))
  }

  function validateInputs() {
    const quantity = Number(constraints.quantity)
    if (!goal.trim()) return 'Enter an AI buyer goal.'
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) return 'Quantity must be a whole number between 1 and 1000.'
    if (!buyer.name.trim() || (!buyer.email.trim() && !buyer.phone.trim())) return 'Enter the buyer name and either an email or phone number.'
    if (!shipping.recipient_name.trim() || !shipping.address_line1.trim() || !shipping.city.trim() || !shipping.state.trim() || !shipping.postal_code.trim() || !shipping.country.trim()) {
      return 'Complete all required shipping fields before running the agent.'
    }
    return ''
  }

  async function runAgent(event) {
    event.preventDefault()
    const validationError = validateInputs()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsRunning(true)
    setPhase('running')
    setError('')
    setProgress(INITIAL_PROGRESS)
    setSelectedProduct(null)
    setQuote(null)
    setOrder(null)

    let activeStep = 'discovery'
    try {
      setStepStatus(activeStep, 'running')
      await discoverMerchant()
      setStepStatus(activeStep, 'complete')

      activeStep = 'search'
      setStepStatus(activeStep, 'running')
      const searchFilters = {
        query: goal.trim(),
        category: constraints.category.trim(),
        brand: constraints.brand.trim(),
        max_price: constraints.maxPrice.trim(),
        sort_by: 'relevance',
        sort_order: 'desc',
      }
      const searchResponse = await searchProducts(searchFilters)
      setStepStatus(activeStep, 'complete')
      const product = searchResponse.results.find((result) => result.active && (!constraints.maxPrice || Number(result.price) <= Number(constraints.maxPrice)))
      if (!product) throw new Error('No product matched the AI buyer goal and constraints.')

      activeStep = 'selection'
      setStepStatus(activeStep, 'running')
      setSelectedProduct(product)
      setStepStatus(activeStep, 'complete')

      activeStep = 'availability'
      setStepStatus(activeStep, 'running')
      const quantity = Number(constraints.quantity)
      const availability = await checkAvailability(product.sku, quantity)
      if (!availability.in_stock || availability.requested_quantity_available === false) {
        throw new Error(`Insufficient inventory for ${product.sku}: requested ${quantity}, available ${availability.available_quantity}.`)
      }
      setStepStatus(activeStep, 'complete')

      activeStep = 'quote'
      setStepStatus(activeStep, 'running')
      const shippingAddress = {
        state: shipping.state.trim(),
        country: shipping.country.trim(),
      }
      const quoteResponse = await createQuote(product.sku, quantity, shippingAddress)
      setQuote(quoteResponse)
      setStepStatus(activeStep, 'complete')

      activeStep = 'order'
      setStepStatus(activeStep, 'running')
      const orderResponse = await createCheckout(quoteResponse.quote_id, {
        name: buyer.name.trim(),
        email: buyer.email.trim() || null,
        phone: buyer.phone.trim() || null,
      }, {
        ...shipping,
        recipient_name: shipping.recipient_name.trim(),
        address_line1: shipping.address_line1.trim(),
        address_line2: shipping.address_line2.trim() || null,
        city: shipping.city.trim(),
        state: shipping.state.trim(),
        postal_code: shipping.postal_code.trim(),
        country: shipping.country.trim(),
      })
      setOrder(orderResponse)
      setStepStatus(activeStep, 'complete')
      setStepStatus('consent', 'current')
      setStepStatus('verification', 'current')
      setPhase('payment')
    } catch (agentError) {
      setStepStatus(activeStep, 'failed')
      setError(agentError.message || 'Agent flow failed')
      setPhase('error')
    } finally {
      setIsRunning(false)
    }
  }

  async function handleTrackOrder() {
    if (!order) return
    setStepStatus('verification', 'running')
    setError('')
    try {
      const status = await getOrderStatus(order.order_id)
      if (status.order_status !== 'PAID') throw new Error(`Backend order status is ${status.order_status}; payment is not verified.`)
      setStepStatus('verification', 'complete')
      setStepStatus('consent', 'complete')
      setStepStatus('tracking', 'complete')
      setPhase('tracking')
    } catch (statusError) {
      setStepStatus('verification', 'failed')
      setError(statusError.message || 'Order verification failed')
      setPhase('error')
    }
  }

  const journey = [
    { key: 'discovered', status: progress.find((step) => step.key === 'discovery').status },
    { key: 'product', status: progress.find((step) => step.key === 'selection').status },
    { key: 'availability', status: progress.find((step) => step.key === 'availability').status },
    { key: 'quote', status: progress.find((step) => step.key === 'quote').status },
    { key: 'order', status: progress.find((step) => step.key === 'order').status },
    { key: 'initiated', status: progress.find((step) => step.key === 'consent').status === 'complete' ? 'complete' : 'pending' },
    { key: 'verified', status: progress.find((step) => step.key === 'verification').status },
    { key: 'tracked', status: progress.find((step) => step.key === 'tracking').status },
  ]

  if (phase === 'payment' && order) {
    return (
      <div className="agent-payment-view">
        <div className="agent-progress-header">
          <p className="eyebrow">Agent Mode / Human authorization required</p>
          <h2>Review and authorize payment</h2>
          <p className="panel-description">The agent stopped before Razorpay. Payment remains a deliberate human action.</p>
        </div>
        <AIBuyerJourney goal={goal} steps={journey} selectedSku={selectedProduct?.sku} quoteId={quote?.quote_id} orderId={order?.order_id} />
        <Payment
          order={order}
          productName={selectedProduct?.name}
          isAgentMode
          onBack={() => setPhase('running')}
          onPaymentInitiated={() => setStepStatus('consent', 'complete')}
          onPaymentFailed={() => setStepStatus('verification', 'failed')}
          onTrackOrder={handleTrackOrder}
          onVerified={handleTrackOrder}
        />
      </div>
    )
  }

  if (phase === 'tracking' && order) {
    return (
      <div className="agent-tracking-view">
        <AIBuyerJourney goal={goal} steps={journey} selectedSku={selectedProduct?.sku} quoteId={quote?.quote_id} orderId={order.order_id} />
        <OrderTracking currentOrderId={order.order_id} onBack={() => setPhase('payment')} />
      </div>
    )
  }

  return (
    <section className="agent-panel" aria-labelledby="agent-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Agent Mode / Deterministic orchestration</p>
          <h2 id="agent-title">Run the AI buyer journey</h2>
          <p className="panel-description">Safe machine-driven API calls run in order; payment still requires your authorization.</p>
        </div>
      </div>

      <form className="agent-form" onSubmit={runAgent}>
        <div className="agent-goal-section">
          <p className="result-label">AI Buyer Goal</p>
          <input className="agent-goal-input" value={goal} onChange={(event) => setGoal(event.target.value)} placeholder="wireless mouse" aria-label="AI buyer goal" />
        </div>
        <div className="agent-form-section">
          <p className="result-label">Optional constraints</p>
          <div className="agent-fields agent-constraint-fields">
            <label>Max price<input name="maxPrice" type="number" min="0" value={constraints.maxPrice} onChange={(event) => updateObject(setConstraints, event)} /></label>
            <label>Category<input name="category" value={constraints.category} onChange={(event) => updateObject(setConstraints, event)} /></label>
            <label>Brand<input name="brand" value={constraints.brand} onChange={(event) => updateObject(setConstraints, event)} /></label>
            <label>Quantity<input name="quantity" type="number" min="1" value={constraints.quantity} onChange={(event) => updateObject(setConstraints, event)} /></label>
          </div>
        </div>
        <div className="agent-form-section">
          <p className="result-label">Buyer and shipping information</p>
          <div className="agent-fields">
            <label>Name *<input name="name" value={buyer.name} onChange={(event) => updateObject(setBuyer, event)} /></label>
            <label>Email<input name="email" type="email" value={buyer.email} onChange={(event) => updateObject(setBuyer, event)} /></label>
            <label>Phone<input name="phone" type="tel" value={buyer.phone} onChange={(event) => updateObject(setBuyer, event)} /></label>
            <label>Recipient name *<input name="recipient_name" value={shipping.recipient_name} onChange={(event) => updateObject(setShipping, event)} /></label>
            <label>Address line 1 *<input name="address_line1" value={shipping.address_line1} onChange={(event) => updateObject(setShipping, event)} /></label>
            <label>Address line 2<input name="address_line2" value={shipping.address_line2} onChange={(event) => updateObject(setShipping, event)} /></label>
            <label>City *<input name="city" value={shipping.city} onChange={(event) => updateObject(setShipping, event)} /></label>
            <label>State / Province / Region *<input name="state" value={shipping.state} onChange={(event) => updateObject(setShipping, event)} /></label>
            <label>Postal code *<input name="postal_code" value={shipping.postal_code} onChange={(event) => updateObject(setShipping, event)} /></label>
            <label>Country *<input name="country" value={shipping.country} onChange={(event) => updateObject(setShipping, event)} /></label>
          </div>
        </div>
        <button className="quote-button agent-run-button" type="submit" disabled={isRunning}>
          {isRunning ? 'Running AI Buyer...' : 'Run AI Buyer'}
        </button>
      </form>

      {error && <div className="status-message error-message" role="alert">{error}</div>}
      <AIBuyerJourney goal={goal} steps={journey} selectedSku={selectedProduct?.sku} quoteId={quote?.quote_id} orderId={order?.order_id} />
    </section>
  )
}

export default AgentMode
