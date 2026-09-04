const ACTIVITY_LABELS = {
  discovered: 'Merchant discovered',
  product: 'Product found',
  availability: 'Stock verified',
  quote: 'Quote generated',
  order: 'Order created',
  initiated: 'Payment initiated',
  verified: 'Payment verified',
  tracked: 'Order tracked',
}

function AIBuyerJourney({ goal, steps, selectedSku, quoteId, orderId }) {
  return (
    <section className="ai-journey" aria-labelledby="ai-journey-title">
      <div className="ai-journey-heading">
        <div>
          <p className="eyebrow">SESSION ACTIVITY</p>
          <h2 id="ai-journey-title">{goal ? `"${goal}"` : 'No buyer goal yet'}</h2>
        </div>
        <span className="ai-journey-badge">Live audit trail</span>
      </div>
      <ol className="ai-journey-list">
        {steps.map((step) => (
          <li className={`ai-journey-step is-${step.status}`} key={step.key}>
            <span className="ai-journey-marker" aria-hidden="true">
              {step.status === 'complete' ? '✓' : step.status === 'failed' ? '!' : step.status === 'current' || step.status === 'running' ? '●' : '○'}
            </span>
            <strong>{ACTIVITY_LABELS[step.key]}</strong>
          </li>
        ))}
      </ol>
      {(selectedSku || quoteId || orderId) && (
        <div className="ai-journey-identifiers">
          {selectedSku && <span>SKU: <strong>{selectedSku}</strong></span>}
          {quoteId && <span>Quote: <strong>{quoteId}</strong></span>}
          {orderId && <span>Order: <strong>{orderId}</strong></span>}
        </div>
      )}
    </section>
  )
}

export default AIBuyerJourney
