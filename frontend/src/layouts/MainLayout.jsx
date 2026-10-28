import React from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const MainLayout = () => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // Show loading state
  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  // If user is not authenticated, redirect to login
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div className="main-layout">
      <header className="main-header">
        <div className="logo">
          <h1>Australian Stock Companion</h1>
        </div>
        <nav className="main-nav">
          <ul>
            <li>
              <a href="/">Dashboard</a>
            </li>
            <li>
              <a href="/search">Search</a>
            </li>
            <li>
              <a href="/watchlist">Watchlist</a>
            </li>
            <li>
              <a href="/reports">Reports</a>
            </li>
            <li>
              <a href="/profile">Profile</a>
            </li>
          </ul>
        </nav>
      </header>
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="main-footer">
        <p>&copy; 2025 Australian Stock Companion</p>
      </footer>
    </div>
  );
};

export default MainLayout;
