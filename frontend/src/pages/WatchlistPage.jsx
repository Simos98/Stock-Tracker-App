import React, { useState, useEffect } from 'react';
import { watchlistService, stockService } from '../services/apiService';
import { formatPrice } from '../utils/format';

const WatchlistPage = () => {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await watchlistService.getWatchlist();
      setWatchlist(response.data);
    } catch (err) {
      console.error('Error fetching watchlist:', err);
      setError('Failed to load your watchlist. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshPrices = async () => {
    if (refreshing) return;

    setRefreshing(true);
    setError('');

    try {
      // Create a new array to hold updated stocks
      const updatedWatchlist = [];

      // Fetch latest data for each stock
      for (const stock of watchlist) {
        try {
          const response = await stockService.getStockDetails(stock.symbol);
          updatedWatchlist.push(response.data);
        } catch (err) {
          // If we can't update a particular stock, keep the old data
          console.error(`Error updating ${stock.symbol}:`, err);
          updatedWatchlist.push(stock);
        }
      }

      setWatchlist(updatedWatchlist);
    } catch (err) {
      console.error('Error refreshing prices:', err);
      setError('Failed to refresh stock prices. Please try again later.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleRemoveFromWatchlist = async (symbol) => {
    try {
      await watchlistService.removeFromWatchlist(symbol);
      // Update local state to remove the stock
      setWatchlist((prevWatchlist) => prevWatchlist.filter((stock) => stock.symbol !== symbol));
    } catch (err) {
      console.error('Error removing from watchlist:', err);
      setError('Failed to remove stock from watchlist. Please try again.');
    }
  };

  return (
    <div className="watchlist-page">
      <div className="page-header">
        <h1>Your Watchlist</h1>
        <button
          onClick={handleRefreshPrices}
          disabled={refreshing || loading}
          className="refresh-button"
        >
          {refreshing ? 'Refreshing...' : 'Refresh Prices'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading your watchlist...</div>
      ) : watchlist.length > 0 ? (
        <div className="watchlist-table">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Last Price</th>
                <th>Change</th>
                <th>Change %</th>
                <th>Volume</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map((stock) => (
                <tr key={stock.symbol}>
                  <td>
                    <a href={`/stocks/${stock.symbol}`}>{stock.symbol}</a>
                  </td>
                  <td>{stock.name}</td>
                  <td>{formatPrice(stock.current_price)}</td>
                  <td
                    className={stock.change > 0 ? 'positive' : stock.change < 0 ? 'negative' : ''}
                  >
                    {stock.change
                      ? `${stock.change > 0 ? '+' : ''}${stock.change.toFixed(2)}`
                      : 'N/A'}
                  </td>
                  <td
                    className={stock.change > 0 ? 'positive' : stock.change < 0 ? 'negative' : ''}
                  >
                    {stock.change_percent || 'N/A'}
                  </td>
                  <td>{stock.volume?.toLocaleString() || 'N/A'}</td>
                  <td>
                    <button
                      onClick={() => handleRemoveFromWatchlist(stock.symbol)}
                      className="remove-button"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-watchlist">
          <p>Your watchlist is empty.</p>
          <p>Add stocks to your watchlist to track their performance.</p>
          <a href="/search" className="cta-button">
            Search for Stocks
          </a>
        </div>
      )}
    </div>
  );
};

export default WatchlistPage;
