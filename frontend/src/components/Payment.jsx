import { useEffect, useRef, useState } from 'react'
import { createPayment, getOrderStatus } from '../services/api.js'

const RAZORPAY_SCRIPT = 'https://checkout.razorpay.com/v1/checkout.js'

function loadRazorpay() {
  if (window.Razorpay) return Promise.resolve()

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = RAZORPAY_SCRIPT
    script.onload = resolve
    script.onerror = () => reject(new Error('Razorpay checkout could not be loaded'))
    document.body.appendChild(script)
  })
}

function Payment({ order, onBack, onTrackOrder, onVerified, onPaymentInitiated, onPaymentFailed, productName, isAgentMode = false }) {
  const [payment, setPayment] = useState(null)
  const [orderStatus, setOrderStatus] = useState(null)
  const [paymentState, setPaymentState] = useState('idle')
  const [error, setError] = useState('')
  const [orderIdCopied, setOrderIdCopied] = useState(false)
  const clientPaymentCompleted = useRef(false)

  useEffect(() => {
    if (!payment || paymentState !== 'waiting') return undefined

    let cancelled = false
    let attempts = 0
    async function refreshStatus() {
      try {
        const status = await getOrderStatus(order.order_id)
        if (cancelled) return
        setOrderStatus(status)
        if (status.order_status === 'PAID') {
          setPaymentState('verified')
          onVerified?.()
          return
        }
        if (status.order_status === 'PAYMENT_FAILED') {
          setPaymentState('failed')
          onPaymentFailed?.()
          setError('The backend reports that this payment failed.')
          return
        }
        attempts += 1
        if (attempts < 10) window.setTimeout(refreshStatus, 3000)
      } catch (statusError) {
        if (!cancelled) setError(statusError.message || 'Could not verify payment status')
      }
    }

    refreshStatus()
    return () => {
      cancelled = true
    }
  }, [payment, paymentState, order.order_id])

  async function handlePayment() {
    setPaymentState('initiating')
    setError('')
    clientPaymentCompleted.current = false
    try {
      const paymentOrder = await createPayment(order.order_id)
      setPayment(paymentOrder)
      setPaymentState('initiated')
      onPaymentInitiated?.()
      await loadRazorpay()
      const razorpay = new window.Razorpay({
        key: paymentOrder.key_id,
        amount: paymentOrder.amount_subunits,
        currency: paymentOrder.currency,
        name: 'AI Merchant Sales API',
        description: `Order ${order.order_id}`,
        order_id: paymentOrder.gateway_order_id,
        handler: () => {
          clientPaymentCompleted.current = true
          setPaymentState('waiting')
          setError('')
        },
        modal: {
          ondismiss: () => {
            if (clientPaymentCompleted.current) return
            setPaymentState('cancelled')
            onPaymentFailed?.()
            setError('Razorpay checkout was cancelled. No payment was verified.')
          },
        },
      })
      razorpay.on('payment.failed', () => {
        setPaymentState('failed')
        onPaymentFailed?.()
        setError('Payment failed in Razorpay. No order status was marked as paid.')
      })
      razorpay.open()
    } catch (paymentError) {
      setPaymentState('failed')
      onPaymentFailed?.()
      setError(paymentError.message || 'Payment initiation failed')
    }
  }

  async function copyOrderId() {
    await navigator.clipboard.writeText(order.order_id)
    setOrderIdCopied(true)
    window.setTimeout(() => setOrderIdCopied(false), 1600)
  }

  const isBusy = paymentState === 'initiating' || paymentState === 'initiated' || paymentState === 'waiting'
  const statusLabel = paymentState === 'verified'
    ? 'PAYMENT VERIFIED'
    : paymentState === 'waiting'
      ? 'WAITING FOR VERIFICATION'
      : paymentState === 'failed'
        ? 'PAYMENT FAILED'
        : paymentState === 'cancelled'
          ? 'PAYMENT CANCELLED'
          : 'PAYMENT INITIATED'

  return (
    <section className="payment-panel" aria-labelledby="payment-title">
      <button className="back-button availability-back" type="button" onClick={onBack}>← Back to Checkout</button>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Phase 7 / Razorpay Payment</p>
          <h2 id="payment-title">Complete payment securely</h2>
          <p className="panel-description">Razorpay Test Mode opens only after the backend creates a payment order.</p>
        </div>
      </div>

      <div className="payment-order-card">
        <p className="result-label">{isAgentMode ? 'AI Agent prepared this transaction' : 'Order ready for payment'}</p>
        {isAgentMode && productName && <p className="payment-prepared-product">Product: {productName}</p>}
        {isAgentMode && <p className="payment-prepared-product">Quote: {order.currency} {order.total}</p>}
        <div className="order-id-row">
          <p className="quote-id"><span>{isAgentMode ? 'Order' : 'Order ID'}</span> {order.order_id}</p>
          <button className="copy-order-id" type="button" onClick={copyOrderId}>
            {orderIdCopied ? 'Copied' : 'Copy Order ID'}
          </button>
        </div>
        <strong className="payment-amount">{order.currency} {order.total}</strong>
      </div>

      {paymentState !== 'idle' && <div className={`payment-state ${paymentState}`} role="status">{statusLabel}</div>}
      {error && <div className="status-message error-message" role="alert">{error}</div>}
      {paymentState === 'waiting' && <p className="payment-note">The browser response was received. Waiting for the verified webhook and backend order status.</p>}
      {paymentState === 'verified' && <p className="payment-note verified-note">Order status: {orderStatus?.order_status || 'PAID'}. Payment was verified by the backend.</p>}
      {paymentState === 'verified' && <button className="quote-button" type="button" onClick={onTrackOrder}>Track Order →</button>}

      {(paymentState === 'failed' || paymentState === 'cancelled') && <button className="quote-button" type="button" onClick={handlePayment} disabled={isBusy}>Try Payment Again</button>}
      {(paymentState === 'idle' || paymentState === 'initiating') && (
        <button className="quote-button payment-button" type="button" onClick={handlePayment} disabled={isBusy}>
          {paymentState === 'initiating' ? 'Starting Payment...' : isAgentMode ? 'Authorize Razorpay Payment' : 'Pay with Razorpay'}
        </button>
      )}
    </section>
  )
}

export default Payment