import React, { useState } from 'react';
import { reportService } from '../services/apiService';

const MAX_STOCKS = 5;

const TIMEFRAMES = [
  { value: '1week', label: '1 Week' },
  { value: '1month', label: '1 Month' },
  { value: '3months', label: '3 Months' },
  { value: '6months', label: '6 Months' },
  { value: '1year', label: '1 Year' },
  { value: '5years', label: '5 Years' },
];

const METRICS = [
  { value: 'price', label: 'Price (latest, high, low)' },
  { value: 'volume', label: 'Average Volume' },
  { value: 'change', label: 'Price Change' },
];

const formatNumber = (value, digits = 2) =>
  value === null || value === undefined
    ? 'N/A'
    : value.toLocaleString('en-AU', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });

const changeClass = (value) => (value > 0 ? 'positive' : value < 0 ? 'negative' : '');

const ReportBuilderPage = () => {
  const [stocks, setStocks] = useState([]);
  const [stockInput, setStockInput] = useState('');
  const [timeframe, setTimeframe] = useState('1month');
  const [metrics, setMetrics] = useState(['price', 'volume', 'change']);
  const [report, setReport] = useState(null);
  const [buildingReport, setBuildingReport] = useState(false);
  const [error, setError] = useState('');

  const handleMetricChange = (e) => {
    const { value, checked } = e.target;
    setMetrics((prev) => (checked ? [...prev, value] : prev.filter((metric) => metric !== value)));
  };

  const handleAddStock = () => {
    const symbol = stockInput.trim().toUpperCase();
    if (!symbol || stocks.includes(symbol) || stocks.length >= MAX_STOCKS) return;

    setStocks((prev) => [...prev, symbol]);
    setStockInput('');
  };

  const handleRemoveStock = (stockToRemove) => {
    setStocks((prev) => prev.filter((stock) => stock !== stockToRemove));
  };

  const handleBuildReport = async (e) => {
    e.preventDefault();
    setBuildingReport(true);
    setError('');

    try {
      const response = await reportService.buildReport({
        stock_symbols: stocks,
        data_fields: metrics,
        time_period: timeframe,
      });
      setReport(response.data);
    } catch (err) {
      console.error('Error building report:', err);
      setError(err.response?.data?.message || 'Failed to build report. Please try again.');
    } finally {
      setBuildingReport(false);
    }
  };

  const shows = (metric) => report?.data_fields.includes(metric);

  return (
    <div className="report-builder-page">
      <h1>Report Builder</h1>

      {error && <div className="error-message">{error}</div>}

      <div className="report-builder-container">
        <section className="report-form-section">
          <h2>Build a Report</h2>

          <form onSubmit={handleBuildReport} className="report-form">
            <div className="form-group">
              <label htmlFor="stock-input">Stocks to Include (up to {MAX_STOCKS})</label>
              <div className="stock-input-group">
                <input
                  type="text"
                  id="stock-input"
                  value={stockInput}
                  onChange={(e) => setStockInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddStock();
                    }
                  }}
                  placeholder="Enter stock symbol (e.g., BHP.AX)"
                />
                <button
                  type="button"
                  onClick={handleAddStock}
                  disabled={stocks.length >= MAX_STOCKS}
                  className="add-stock-button"
                >
                  Add
                </button>
              </div>

              {stocks.length > 0 && (
                <div className="selected-stocks">
                  <p>Selected Stocks:</p>
                  <ul>
                    {stocks.map((stock) => (
                      <li key={stock}>
                        {stock}
                        <button
                          type="button"
                          onClick={() => handleRemoveStock(stock)}
                          className="remove-stock-button"
                          aria-label={`Remove ${stock}`}
                        >
                          ✕
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="timeframe">Timeframe</label>
              <select
                id="timeframe"
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
              >
                {TIMEFRAMES.map(({ value, label }) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Metrics to Include</label>
              <div className="metrics-checkboxes">
                {METRICS.map(({ value, label }) => (
                  <div className="checkbox-item" key={value}>
                    <input
                      type="checkbox"
                      id={`metric-${value}`}
                      value={value}
                      checked={metrics.includes(value)}
                      onChange={handleMetricChange}
                    />
                    <label htmlFor={`metric-${value}`}>{label}</label>
                  </div>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={buildingReport || stocks.length === 0 || metrics.length === 0}
              className="build-report-button"
            >
              {buildingReport ? 'Building Report...' : 'Build Report'}
            </button>
          </form>
        </section>

        <section className="report-results-section">
          <h2>Results</h2>

          {!report ? (
            <div className="empty-reports">
              <p>Add some stocks and build a report to compare them here.</p>
            </div>
          ) : (
            <table className="report-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Period</th>
                  {shows('price') && (
                    <>
                      <th>Latest Close</th>
                      <th>High</th>
                      <th>Low</th>
                    </>
                  )}
                  {shows('volume') && (
                    <th>Avg Volume ({report.interval === 'weekly' ? 'per week' : 'per day'})</th>
                  )}
                  {shows('change') && (
                    <>
                      <th>Change</th>
                      <th>Change %</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {report.results.map((result) => (
                  <tr key={result.symbol}>
                    <td>{result.symbol}</td>
                    {result.error ? (
                      <td colSpan={99}>{result.error}</td>
                    ) : (
                      <>
                        <td>
                          {result.from} – {result.to}
                        </td>
                        {shows('price') && (
                          <>
                            <td>{formatNumber(result.latest_close)}</td>
                            <td>{formatNumber(result.period_high)}</td>
                            <td>{formatNumber(result.period_low)}</td>
                          </>
                        )}
                        {shows('volume') && <td>{formatNumber(result.average_volume, 0)}</td>}
                        {shows('change') && (
                          <>
                            <td className={changeClass(result.change)}>
                              {formatNumber(result.change)}
                            </td>
                            <td className={changeClass(result.change)}>
                              {formatNumber(result.change_percent)}%
                            </td>
                          </>
                        )}
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </div>
  );
};

export default ReportBuilderPage;
