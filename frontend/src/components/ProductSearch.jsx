import { useState } from 'react'
import { searchProducts } from '../services/api.js'

function ProductSearch({ onBack, onProductSelected, onCheckAvailability, onGoalChange, onSearchFailed }) {
  const [query, setQuery] = useState('')
  const [recentQueries, setRecentQueries] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('ai-merchant-recent-searches') || '[]')
    } catch {
      return []
    }
  })
  const [filters, setFilters] = useState({
    category: '',
    brand: '',
    min_price: '',
    max_price: '',
    sort_by: 'relevance',
    sort_order: 'desc',
  })
  const [searchResponse, setSearchResponse] = useState(null)
  const [selectedSku, setSelectedSku] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  function updateFilter(event) {
    const { name, value } = event.target
    setFilters((currentFilters) => ({ ...currentFilters, [name]: value }))
  }

  async function handleSearch(event) {
    event.preventDefault()
    if (!query.trim()) {
      onSearchFailed?.()
      setError('Enter a product or category to search.')
      setSearchResponse(null)
      return
    }

    setIsLoading(true)
    setError('')
    setSelectedSku('')

    const nextRecentQueries = [
      query.trim(),
      ...recentQueries.filter((recentQuery) => recentQuery !== query.trim()),
    ].slice(0, 5)
    setRecentQueries(nextRecentQueries)
    localStorage.setItem('ai-merchant-recent-searches', JSON.stringify(nextRecentQueries))

    try {
      setSearchResponse(await searchProducts({ query: query.trim(), ...filters }))
    } catch (searchError) {
      setSearchResponse(null)
      onSearchFailed?.()
      setError(searchError.message || 'Product search failed')
    } finally {
      setIsLoading(false)
    }
  }

  function selectProduct(sku) {
    const nextSku = selectedSku === sku ? '' : sku
    setSelectedSku(nextSku)
    onProductSelected(nextSku)
  }

  function clearFilters() {
    setFilters({
      category: '',
      brand: '',
      min_price: '',
      max_price: '',
      sort_by: 'relevance',
      sort_order: 'desc',
    })
  }

  return (
    <section className="search-panel" aria-labelledby="search-title">
      <div className="panel-heading">
        <div>
          <button className="back-button" type="button" onClick={onBack}>← Back to Merchant Discovery</button>
          <p className="eyebrow">Phase 3 / Product Search</p>
          <h2 id="search-title">What does the AI buyer want?</h2>
          <p className="panel-description">
            Search the merchant catalog with supported buyer filters.
          </p>
        </div>
      </div>

      <form className="search-form" onSubmit={handleSearch}>
        <label className="search-query-label" htmlFor="product-query">
          What are you looking for?
        </label>
        <div className="search-query-row">
          <input
            id="product-query"
            name="query"
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              onGoalChange?.(event.target.value)
            }}
            placeholder="Try wireless mouse"
            autoComplete="off"
            list="recent-searches"
          />
          <datalist id="recent-searches">
            {recentQueries.map((recentQuery) => (
              <option key={recentQuery} value={recentQuery} />
            ))}
          </datalist>
          <button className="search-button" type="submit" disabled={isLoading}>
            {isLoading ? 'Searching...' : 'Search Products'}
          </button>
        </div>

        <div className="search-filters">
          <input name="category" value={filters.category} onChange={updateFilter} placeholder="Category" aria-label="Category filter" />
          <input name="brand" value={filters.brand} onChange={updateFilter} placeholder="Brand" aria-label="Brand filter" />
          <input name="min_price" type="number" min="0" value={filters.min_price} onChange={updateFilter} placeholder="Min price" aria-label="Minimum price" />
          <input name="max_price" type="number" min="0" value={filters.max_price} onChange={updateFilter} placeholder="Max price" aria-label="Maximum price" />
          <select name="sort_by" value={filters.sort_by} onChange={updateFilter} aria-label="Sort products by">
            <option value="relevance">Sort: Relevance</option>
            <option value="price">Sort: Price</option>
            <option value="name">Sort: Name</option>
            <option value="sku">Sort: SKU</option>
          </select>
          <select name="sort_order" value={filters.sort_order} onChange={updateFilter} aria-label="Sort order">
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </form>

      {error && <div className="status-message error-message" role="alert">{error}</div>}

      {searchResponse && searchResponse.results.length === 0 && (
        <div className="empty-search" role="status">
          <strong>No products found</strong>
          <p>Try a broader search or remove one of the filters.</p>
          <button className="clear-filters-button" type="button" onClick={clearFilters}>Clear filters</button>
        </div>
      )}

      {searchResponse && searchResponse.results.length > 0 && (
        <div className="search-results" aria-live="polite">
          <div className="results-heading">
            <p className="result-label">Search results</p>
            <span>{searchResponse.total_matches} match{searchResponse.total_matches === 1 ? '' : 'es'}</span>
          </div>
          <div className="product-grid">
            {searchResponse.results.map((product) => (
              <article className={'product-card' + (selectedSku === product.sku ? ' is-selected' : '')} key={product.sku}>
                <div className="product-card-topline">
                  <span className="product-category">Category: {product.category || 'Uncategorized'}</span>
                  <span className="product-status">{product.active ? 'ACTIVE' : product.status}</span>
                </div>
                <h3>{product.name}</h3>
                <p className="product-sku">SKU: {product.sku}</p>
                <div className="product-meta">
                  <strong>{product.currency} {Number(product.price).toLocaleString('en-IN')}</strong>
                  <span>Brand: {product.brand || 'Not specified'}</span>
                </div>
                <button className="availability-button" type="button" onClick={() => {
                  if (selectedSku === product.sku) {
                    selectProduct(product.sku)
                    return
                  }
                  selectProduct(product.sku)
                  onCheckAvailability(product)
                }}>
                  {selectedSku === product.sku ? 'Deselect product' : 'Check Availability'}
                </button>
              </article>
            ))}
          </div>
          {selectedSku && (
            <p className="selection-note" role="status">Selected product SKU: <strong>{selectedSku}</strong></p>
          )}
        </div>
      )}
    </section>
  )
}

export default ProductSearch