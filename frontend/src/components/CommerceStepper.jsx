const STEPS = [
  'Discover',
  'Search',
  'Availability',
  'Quote',
  'Checkout',
  'Payment',
  'Order',
]

function CommerceStepper({ activeStep = -1, completedThrough = -1, onStepClick, interactive = true }) {
  return (
    <ol className="stepper">
      <li className="stepper-origin">
        <span className="origin-dot" aria-hidden="true">AI</span>
        <strong>AI Buyer</strong>
        <span className="stepper-arrow" aria-hidden="true">→</span>
      </li>
      {STEPS.map((step, index) => (
        <li key={step} className="stepper-item">
          {interactive ? (
            <button
              type="button"
              disabled={index > completedThrough}
              onClick={() => onStepClick(index)}
              className={
                'stepper-step' +
                (index < activeStep ? ' is-complete' : '') +
                (index === activeStep ? ' is-active' : '')
              }
            >
              {step}
            </button>
          ) : (
            <span
              className={
                'stepper-step stepper-label' +
                (index < activeStep ? ' is-complete' : '') +
                (index === activeStep ? ' is-active' : '')
              }
            >
              {step}
            </span>
          )}
          {index < STEPS.length - 1 && (
            <span className="stepper-arrow" aria-hidden="true">
              →
            </span>
          )}
        </li>
      ))}
    </ol>
  )
}

export default CommerceStepper