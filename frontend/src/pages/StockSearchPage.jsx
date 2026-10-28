import React, { useState } from 'react';
import { stockService } from '../services/apiService';

const StockSearchPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [exchange, setExchange] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const resultsPerPage = 10;

  const handleSearch = (e) => {
    e.preventDefault();
    goToPage(1); // a new search starts from the first page
  };

  // Takes the page explicitly: reading `page` right after setPage() would see the old value
  const goToPage = async (pageNumber) => {
    if (!searchTerm && !exchange) return;

    setPage(pageNumber);

    setLoading(true);
    setError('');

    try {
      const offset = (pageNumber - 1) * resultsPerPage;
      const response = await stockService.searchStocks({
        search_term: searchTerm,
        exchange: exchange,
        limit: resultsPerPage,
        offset: offset,
      });

      setSearchResults(response.data.data);
      setTotalResults(response.data.total);
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to search stocks. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(totalResults / resultsPerPage);

  return (
    <div className="stock-search-page">
      <h1>Search Stocks</h1>

      <form onSubmit={handleSearch} className="search-form">
        <div className="form-group">
          <label htmlFor="searchTerm">Stock Name or Symbol</label>
          <input
            type="text"
            id="searchTerm"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="e.g., BHP or Commonwealth Bank"
          />
        </div>

        <div className="form-group">
          <label htmlFor="exchange">Exchange</label>
          <select id="exchange" value={exchange} onChange={(e) => setExchange(e.target.value)}>
            <option value="">All Exchanges</option>
            <option value="ASX">Australian Securities Exchange (ASX)</option>
            <option value="NYSE">New York Stock Exchange (NYSE)</option>
            <option value="NASDAQ">NASDAQ</option>
          </select>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}

      <div className="search-results">
        {loading ? (
          <div className="loading">Searching for stocks...</div>
        ) : searchResults.length > 0 ? (
          <>
            <h2>Search Results</h2>
            <p>Found {totalResults} results for your search.</p>

            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Name</th>
                  <th>Exchange</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((stock) => (
                  <tr key={stock.symbol}>
                    <td>{stock.symbol}</td>
                    <td>{stock.name}</td>
                    <td>{stock.exchange}</td>
                    <td>
                      <a href={`/stocks/${stock.symbol}`} className="view-button">
                        View Details
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pagination">
                <button onClick={() => goToPage(Math.max(page - 1, 1))} disabled={page === 1}>
                  Previous
                </button>

                <span>
                  Page {page} of {totalPages}
                </span>

                <button
                  onClick={() => goToPage(Math.min(page + 1, totalPages))}
                  disabled={page === totalPages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        ) : searchTerm || exchange ? (
          <div className="no-results">
            <p>No stocks found matching your search criteria.</p>
            <p>Try broadening your search or using different keywords.</p>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default StockSearchPage;
