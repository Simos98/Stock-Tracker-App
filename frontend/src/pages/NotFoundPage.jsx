import React from 'react';

const NotFoundPage = () => {
  return (
    <div className="not-found-page">
      <h1>404 - Page Not Found</h1>
      <p>The page you are looking for does not exist or has been moved.</p>
      <div className="not-found-actions">
        <a href="/" className="home-button">
          Go to Dashboard
        </a>
        <a href="/search" className="search-button">
          Search for Stocks
        </a>
      </div>
    </div>
  );
};

export default NotFoundPage;
