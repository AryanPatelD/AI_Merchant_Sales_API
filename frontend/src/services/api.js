const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const apiTraceListeners = new Set()
const SENSITIVE_FIELD = /authorization|api[-_]?key|key_id|secret|password|credential|token|webhook/i

function sanitize(value, fieldName = '') {
	if (SENSITIVE_FIELD.test(fieldName)) return '[REDACTED]'
	if (Array.isArray(value)) return value.map((item) => sanitize(item))
	if (value && typeof value === 'object') {
		return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, sanitize(item, key)]))
	}
	return value
}

function publishApiTrace(method, endpoint, request, response) {
	const trace = { method, endpoint, request: sanitize(request), response: sanitize(response) }
	apiTraceListeners.forEach((listener) => listener(trace))
}

function subscribeApiTrace(listener) {
	apiTraceListeners.add(listener)
	return () => apiTraceListeners.delete(listener)
}

async function discoverMerchant() {
	const response = await fetch(`${API_BASE_URL}/.well-known/ai-commerce`)
	const payload = await response.json()
	publishApiTrace('GET', '/.well-known/ai-commerce', {}, payload)

	if (!response.ok) {
		throw new Error(payload.detail || 'Merchant discovery failed')
	}

	return payload
}

async function searchProducts(filters) {
	const params = new URLSearchParams({ q: filters.query })

	for (const [key, value] of Object.entries(filters)) {
		if (key !== 'query' && value) {
			params.set(key, value)
		}
	}

	const response = await fetch(`${API_BASE_URL}/api/v1/search?${params}`)
	const payload = await response.json()
	publishApiTrace('GET', '/api/v1/search', Object.fromEntries(params), payload)

	if (!response.ok) {
		throw new Error(payload.detail || 'Product search failed')
	}

	return payload
}

async function checkAvailability(sku, quantity) {
	const params = new URLSearchParams({ sku, quantity: String(quantity) })
	const response = await fetch(`${API_BASE_URL}/api/v1/availability?${params}`)
	const payload = await response.json()
	publishApiTrace('GET', '/api/v1/availability', Object.fromEntries(params), payload)

	if (!response.ok) {
		throw new Error(payload.detail || 'Availability check failed')
	}

	return payload
}

async function createQuote(sku, quantity, shippingAddress) {
	const response = await fetch(`${API_BASE_URL}/api/v1/quote`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Idempotency-Key': crypto.randomUUID(),
		},
		body: JSON.stringify({
			items: [{ sku, quantity }],
			shipping_address: shippingAddress,
		}),
	})
	const payload = await response.json()
	publishApiTrace('POST', '/api/v1/quote', {
		items: [{ sku, quantity }],
		shipping_address: shippingAddress,
	}, payload)

	if (!response.ok) {
		throw new Error(payload.detail || 'Quote creation failed')
	}

	return payload
}

async function createCheckout(quoteId, buyer, shippingAddress, idempotencyKey = crypto.randomUUID()) {
	const response = await fetch(`${API_BASE_URL}/api/v1/checkout`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Idempotency-Key': idempotencyKey,
		},
		body: JSON.stringify({
			quote_id: quoteId,
			buyer,
			shipping_address: shippingAddress,
		}),
	})
	const payload = await response.json()
	publishApiTrace('POST', '/api/v1/checkout', {
		quote_id: quoteId,
		buyer,
		shipping_address: shippingAddress,
	}, payload)

	if (!response.ok) {
		throw new Error(payload.detail || 'Checkout failed')
	}

	return payload
}

async function createPayment(orderId) {
	const response = await fetch(`${API_BASE_URL}/api/v1/payment`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Idempotency-Key': crypto.randomUUID(),
		},
		body: JSON.stringify({ order_id: orderId }),
	})
	const payload = await response.json()
	publishApiTrace('POST', '/api/v1/payment', { order_id: orderId }, payload)

	if (!response.ok) {
		throw new Error(payload.detail || 'Payment initiation failed')
	}

	return payload
}

async function getOrderStatus(orderId) {
	const response = await fetch(`${API_BASE_URL}/api/v1/order-status?order_id=${orderId}`)
	const payload = await response.json()
	publishApiTrace('GET', '/api/v1/order-status', { order_id: orderId }, payload)

	if (!response.ok) {
		throw new Error(payload.detail || 'Could not verify order status')
	}

	return payload
}

export { API_BASE_URL, checkAvailability, createCheckout, createPayment, createQuote, discoverMerchant, getOrderStatus, searchProducts, subscribeApiTrace }