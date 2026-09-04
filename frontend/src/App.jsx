import { useEffect, useState } from 'react'
import Header from './components/Header.jsx'
import CommerceStepper from './components/CommerceStepper.jsx'
import Availability from './components/Availability.jsx'
import MerchantDiscovery from './components/MerchantDiscovery.jsx'
import ProductSearch from './components/ProductSearch.jsx'
import Quote from './components/Quote.jsx'
import Checkout from './components/Checkout.jsx'
import Payment from './components/Payment.jsx'
import OrderTracking from './components/OrderTracking.jsx'
import TrustPanel from './components/TrustPanel.jsx'
import AgentMode from './components/AgentMode.jsx'
import AIBuyerJourney from './components/AIBuyerJourney.jsx'
import TechnicalApiInspector from './components/TechnicalApiInspector.jsx'
import { subscribeApiTrace } from './services/api.js'
import './App.css'

const INITIAL_JOURNEY = [
  { key: 'discovered', status: 'pending' },
  { key: 'product', status: 'pending' },
  { key: 'availability', status: 'pending' },
  { key: 'quote', status: 'pending' },
  { key: 'order', status: 'pending' },
  { key: 'initiated', status: 'pending' },
  { key: 'verified', status: 'pending' },
  { key: 'tracked', status: 'pending' },
]

function App() {
  const [mode, setMode] = useState('manual')
  const [activeStep, setActiveStep] = useState(0)
  const [discoveryCompleted, setDiscoveryCompleted] = useState(false)
  const [selectedSku, setSelectedSku] = useState('')
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [selectedQuantity, setSelectedQuantity] = useState(1)
  const [quoteId, setQuoteId] = useState('')
  const [quoteAddress, setQuoteAddress] = useState({ state: '', country: '' })
  const [order, setOrder] = useState(null)
  const [buyerGoal, setBuyerGoal] = useState('')
  const [journey, setJourney] = useState(INITIAL_JOURNEY)
  const [apiTrace, setApiTrace] = useState(null)

  useEffect(() => subscribeApiTrace(setApiTrace), [])

  function setJourneyStatus(key, status) {
    setJourney((current) => current.map((step) => step.key === key ? { ...step, status } : step))
  }

  return (
    <div className="app">
      <Header />
      <section className="mode-selector" aria-label="Commerce mode">
        <div className="mode-buttons" role="group" aria-label="Choose commerce mode">
          <button className={mode === 'manual' ? 'mode-button is-active' : 'mode-button'} type="button" onClick={() => setMode('manual')}>
            Manual Mode
          </button>
          <button className={mode === 'agent' ? 'mode-button is-active' : 'mode-button'} type="button" onClick={() => setMode('agent')}>
            ⚡ Agent Mode
          </button>
        </div>
        <p>{mode === 'manual' ? 'Inspect each commerce operation.' : 'Provide the goal once and let the commerce workflow execute automatically.'}</p>
      </section>
      {mode === 'manual' && (
        <CommerceStepper
          activeStep={activeStep}
          completedThrough={discoveryCompleted ? (order ? 6 : quoteId ? 3 : selectedSku ? 2 : 1) : 0}
          onStepClick={setActiveStep}
        />
      )}
      <main className="app-main">
        {mode === 'agent' ? <AgentMode /> : <>
        <div className={activeStep === 0 ? 'phase-view' : 'phase-view is-hidden'}>
          <MerchantDiscovery
            onFailed={() => setJourneyStatus('discovered', 'failed')}
            onDiscovered={() => {
              setDiscoveryCompleted(true)
              setJourneyStatus('discovered', 'complete')
            }}
            onContinue={() => setActiveStep(1)}
          />
        </div>
        <div className={activeStep === 1 ? 'phase-view' : 'phase-view is-hidden'}>
          <ProductSearch
            onBack={() => setActiveStep(0)}
            onGoalChange={setBuyerGoal}
            onSearchFailed={() => setJourneyStatus('product', 'failed')}
            onProductSelected={(sku) => {
              setSelectedSku(sku)
              if (!sku) setSelectedProduct(null)
              setJourneyStatus('product', sku ? 'complete' : 'pending')
            }}
            onCheckAvailability={(product) => {
              setSelectedSku(product.sku)
              setSelectedProduct(product)
              setActiveStep(2)
            }}
          />
        </div>
        <div className={activeStep === 2 ? 'phase-view' : 'phase-view is-hidden'}>
          <Availability
            selectedSku={selectedSku}
            productName={selectedProduct?.name}
            onBack={() => setActiveStep(1)}
            onFailed={() => setJourneyStatus('availability', 'failed')}
            onGenerateQuote={(quantity) => {
              setSelectedQuantity(quantity)
              setJourneyStatus('availability', 'complete')
              setActiveStep(3)
            }}
          />
        </div>
        <div className={activeStep === 3 ? 'phase-view' : 'phase-view is-hidden'}>
          <Quote
            selectedSku={selectedSku}
            quantity={selectedQuantity}
            onBack={() => setActiveStep(2)}
            onFailed={() => setJourneyStatus('quote', 'failed')}
            onQuoteCreated={(id) => {
              setQuoteId(id)
              setJourneyStatus('quote', 'complete')
            }}
            onProceedToCheckout={(address) => {
              setQuoteAddress(address)
              setActiveStep(4)
            }}
          />
        </div>
        <div className={activeStep === 4 ? 'phase-view' : 'phase-view is-hidden'}>
          <Checkout
            quoteId={quoteId}
            quoteAddress={quoteAddress}
            onBack={() => setActiveStep(3)}
            onFailed={() => setJourneyStatus('order', 'failed')}
            onOrderCreated={(createdOrder) => {
              setOrder(createdOrder)
              setJourneyStatus('order', 'complete')
            }}
            onProceedToPayment={() => setActiveStep(5)}
          />
        </div>
        <div className={activeStep === 5 ? 'phase-view' : 'phase-view is-hidden'}>
          {order && (
            <Payment
              order={order}
              onBack={() => setActiveStep(4)}
              onPaymentInitiated={() => setJourneyStatus('initiated', 'complete')}
              onPaymentFailed={() => setJourneyStatus('initiated', 'failed')}
              onVerified={() => setJourneyStatus('verified', 'complete')}
              onTrackOrder={() => setActiveStep(6)}
            />
          )}
        </div>
        <div className={activeStep === 6 ? 'phase-view' : 'phase-view is-hidden'}>
          <OrderTracking
            currentOrderId={order?.order_id}
            onBack={() => setActiveStep(5)}
            onFailed={() => setJourneyStatus('tracked', 'failed')}
            onOrderTracked={() => setJourneyStatus('tracked', 'complete')}
          />
        </div>
        </>}
      </main>
      {mode === 'manual' && <AIBuyerJourney goal={buyerGoal} steps={journey} selectedSku={selectedSku} quoteId={quoteId} orderId={order?.order_id} />}
      <TrustPanel />
      <TechnicalApiInspector trace={apiTrace} />
    </div>
  )
}

export default App