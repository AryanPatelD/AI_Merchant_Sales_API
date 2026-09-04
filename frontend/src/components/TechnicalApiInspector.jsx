function TechnicalApiInspector({ trace }) {
  return (
    <details className="api-inspector">
      <summary>View API Details</summary>
      {!trace ? (
        <p className="api-inspector-empty">No API activity yet.</p>
      ) : (
        <div className="api-inspector-content">
          <p className="api-inspector-endpoint">
            <strong>{trace.method}</strong> {trace.endpoint}
          </p>
          <div className="api-inspector-block">
            <span>Request</span>
            <pre>{JSON.stringify(trace.request, null, 2)}</pre>
          </div>
          <div className="api-inspector-block">
            <span>Response</span>
            <pre>{JSON.stringify(trace.response, null, 2)}</pre>
          </div>
        </div>
      )}
    </details>
  )
}

export default TechnicalApiInspector
