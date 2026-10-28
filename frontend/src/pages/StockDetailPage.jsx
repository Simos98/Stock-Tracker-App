import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { stockService, watchlistService } from '../services/apiService';
import { formatPrice } from '../utils/format';

const StockDetailPage = () => {
  const { symbol } = useParams();
  const [stock, setStock] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [interval, setInterval] = useState('daily');

  useEffect(() => {
    const fetchStockData = async () => {
      setLoading(true);
      setError('');

      try {
        // Fetch stock details
        const stockResponse = await stockService.getStockDetails(symbol);
        setStock(stockResponse.data);

        // Fetch historical data
        const historicalResponse = await stockService.getHistoricalData(symbol, {
          interval: interval,
          output_size: 'compact',
        });
        setHistoricalData(historicalResponse.data);

        // Check if stock is in user's watchlist
        try {
          const watchlistResponse = await watchlistService.getWatchlist();
          const watchlistItems = watchlistResponse.data;
          setIsInWatchlist(watchlistItems.some((item) => item.symbol === symbol.toUpperCase()));
        } catch (watchlistErr) {
          console.error('Error checking watchlist:', watchlistErr);
          // Non-critical error, don't show to user
        }
      } catch (err) {
        console.error('Error fetching stock data:', err);
        setError('Failed to load stock data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchStockData();
  }, [symbol, interval]);

  const handleAddToWatchlist = async () => {
    try {
      await watchlistService.addToWatchlist({ stock_symbol: symbol });
      setIsInWatchlist(true);
    } catch (err) {
      console.error('Error adding to watchlist:', err);
      setError('Failed to add stock to watchlist. Please try again.');
    }
  };

  const handleRemoveFromWatchlist = async () => {
    try {
      await watchlistService.removeFromWatchlist(symbol);
      setIsInWatchlist(false);
    } catch (err) {
      console.error('Error removing from watchlist:', err);
      setError('Failed to remove stock from watchlist. Please try again.');
    }
  };

  const handleIntervalChange = (e) => {
    setInterval(e.target.value);
  };

  return (
    <div className="stock-detail-page">
      {loading ? (
        <div className="loading">Loading stock data...</div>
      ) : error ? (
        <div className="error-message">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => window.history.back()}>Go Back</button>
        </div>
      ) : stock ? (
        <>
          <div className="stock-header">
            <div className="stock-title">
              <h1>
                {stock.name} ({stock.symbol})
              </h1>
              <p className="exchange">{stock.exchange}</p>
            </div>

            <div className="watchlist-actions">
              {isInWatchlist ? (
                <button onClick={handleRemoveFromWatchlist} className="remove-from-watchlist">
                  Remove from Watchlist
                </button>
              ) : (
                <button onClick={handleAddToWatchlist} className="add-to-watchlist">
                  Add to Watchlist
                </button>
              )}
            </div>
          </div>

          <div className="stock-price-info">
            <div className="current-price">
              <h2>{formatPrice(stock.current_price)}</h2>
              {stock.change && (
                <span
                  className={stock.change > 0 ? 'positive' : stock.change < 0 ? 'negative' : ''}
                >
                  {stock.change > 0 ? '+' : ''}
                  {stock.change.toFixed(2)} ({stock.change_percent})
                </span>
              )}
            </div>

            <div className="price-details">
              <div className="detail-item">
                <span className="label">Open</span>
                <span className="value">{formatPrice(stock.open_price)}</span>
              </div>
              <div className="detail-item">
                <span className="label">High</span>
                <span className="value">{formatPrice(stock.day_high)}</span>
              </div>
              <div className="detail-item">
                <span className="label">Low</span>
                <span className="value">{formatPrice(stock.day_low)}</span>
              </div>
              <div className="detail-item">
                <span className="label">Previous Close</span>
                <span className="value">{formatPrice(stock.previous_close)}</span>
              </div>
              <div className="detail-item">
                <span className="label">Volume</span>
                <span className="value">{stock.volume?.toLocaleString() || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="label">Last Updated</span>
                <span className="value">{stock.last_updated || 'N/A'}</span>
              </div>
            </div>
          </div>

          <div className="historical-data-section">
            <h2>Historical Data</h2>

            <div className="interval-selector">
              <label htmlFor="interval">Interval:</label>
              <select id="interval" value={interval} onChange={handleIntervalChange}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>

            {historicalData.length > 0 ? (
              <div className="historical-data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Open</th>
                      <th>High</th>
                      <th>Low</th>
                      <th>Close</th>
                      <th>Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historicalData.slice(0, 20).map((dataPoint) => (
                      <tr key={dataPoint.date}>
                        <td>{dataPoint.date}</td>
                        <td>${dataPoint.open.toFixed(2)}</td>
                        <td>${dataPoint.high.toFixed(2)}</td>
                        <td>${dataPoint.low.toFixed(2)}</td>
                        <td>${dataPoint.close.toFixed(2)}</td>
                        <td>{dataPoint.volume.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {historicalData.length > 20 && (
                  <p className="note">Showing the 20 most recent data points.</p>
                )}
              </div>
            ) : (
              <div className="no-data">
                <p>No historical data available for this stock.</p>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="not-found">
          <h2>Stock Not Found</h2>
          <p>We couldn't find any stock with the symbol "{symbol}".</p>
          <a href="/search" className="cta-button">
            Search for Stocks
          </a>
        </div>
      )}
    </div>
  );
};

export default StockDetailPage;
