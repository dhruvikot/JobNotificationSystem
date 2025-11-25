import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/dashboard" className="navbar-logo">
          📡 Distributed Events
        </Link>
        
        <div className="navbar-menu">
          <Link to="/dashboard" className="navbar-link">Dashboard</Link>
          <Link to="/subscriptions" className="navbar-link">Subscriptions</Link>
          <Link to="/events" className="navbar-link">Events</Link>
          <Link to="/notifications" className="navbar-link">Notifications</Link>
          
          {user && (user.role === 'organizer' || user.role === 'admin') && (
            <Link to="/events/create" className="navbar-link">Create Event</Link>
          )}
        </div>
        
        <div className="navbar-user">
          <span className="navbar-username">{user?.name}</span>
          <button onClick={handleLogout} className="btn btn-secondary btn-sm">
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;


