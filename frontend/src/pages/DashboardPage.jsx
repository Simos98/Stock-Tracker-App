import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { stockService, watchlistService } from '../services/apiService';
import { formatPrice } from '../utils/format';

const DashboardPage = () => {
  const { currentUser } = useAuth();
  const [watchlist, setWatchlist] = useState([]);
  const [marketOverview, setMarketOverview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        // Fetch user's watchlist
        const watchlistResponse = await watchlistService.getWatchlist();
        setWatchlist(watchlistResponse.data);

        // Fetch market overview (top ASX stocks)
        // This would typically be a separate endpoint, but we'll use the search endpoint with ASX filter
        const marketResponse = await stockService.searchStocks({
          exchange: 'ASX',
          limit: 5,
        });
        setMarketOverview(marketResponse.data.data);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="dashboard-page">
      <h1>Welcome, {currentUser?.username || 'User'}!</h1>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading dashboard data...</div>
      ) : (
        <>
          <section className="dashboard-section">
            <h2>Your Watchlist</h2>
            {watchlist.length > 0 ? (
              <div className="watchlist-preview">
                <table>
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Name</th>
                      <th>Last Price</th>
                      <th>Change</th>
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
                          className={
                            stock.change > 0 ? 'positive' : stock.change < 0 ? 'negative' : ''
                          }
                        >
                          {stock.change
                            ? `${stock.change > 0 ? '+' : ''}${stock.change.toFixed(2)}`
                            : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <a href="/watchlist" className="view-all">
                  View all watchlist items
                </a>
              </div>
            ) : (
              <div className="empty-state">
                <p>You haven't added any stocks to your watchlist yet.</p>
                <a href="/search" className="cta-button">
                  Search for stocks
                </a>
              </div>
            )}
          </section>

          <section className="dashboard-section">
            <h2>Market Overview</h2>
            {marketOverview.length > 0 ? (
              <div className="market-overview">
                <table>
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Name</th>
                      <th>Exchange</th>
                    </tr>
                  </thead>
                  <tbody>
                    {marketOverview.map((stock) => (
                      <tr key={stock.symbol}>
                        <td>
                          <a href={`/stocks/${stock.symbol}`}>{stock.symbol}</a>
                        </td>
                        <td>{stock.name}</td>
                        <td>{stock.exchange}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <a href="/search" className="view-all">
                  Search for more stocks
                </a>
              </div>
            ) : (
              <div className="empty-state">
                <p>No market data available at the moment.</p>
                <button onClick={() => window.location.reload()} className="cta-button">
                  Refresh
                </button>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
};

export default DashboardPage;
