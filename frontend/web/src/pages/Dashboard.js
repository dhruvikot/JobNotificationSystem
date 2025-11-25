import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { subscriptionsAPI, eventsAPI, notificationsAPI } from '../api/api';
import './Dashboard.css';

function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    subscriptions: 0,
    events: 0,
    notifications: 0
  });
  const [recentEvents, setRecentEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [subsRes, eventsRes, notifsRes] = await Promise.all([
        subscriptionsAPI.getSubscriptions(),
        eventsAPI.getEvents({ limit: 5 }),
        notificationsAPI.getNotifications(user.user_id, { limit: 5 })
      ]);

      setStats({
        subscriptions: subsRes.data.subscriptions?.length || 0,
        events: eventsRes.data.count || 0,
        notifications: notifsRes.data.count || 0
      });

      setRecentEvents(eventsRes.data.events || []);
    } catch (err) {
      console.error('Error loading dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1>Welcome, {user?.name}!</h1>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📬</div>
          <div className="stat-value">{stats.subscriptions}</div>
          <div className="stat-label">Subscriptions</div>
          <Link to="/subscriptions" className="stat-link">Manage →</Link>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📅</div>
          <div className="stat-value">{stats.events}</div>
          <div className="stat-label">Events Available</div>
          <Link to="/events" className="stat-link">Browse →</Link>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🔔</div>
          <div className="stat-value">{stats.notifications}</div>
          <div className="stat-label">Notifications</div>
          <Link to="/notifications" className="stat-link">View →</Link>
        </div>
      </div>

      <div className="card">
        <h2>Recent Events</h2>
        {recentEvents.length === 0 ? (
          <p className="empty-state">No events available yet.</p>
        ) : (
          <div className="events-list">
            {recentEvents.map((event) => (
              <div key={event.event_id} className="event-item">
                <div>
                  <h3>{event.title}</h3>
                  <p className="event-topic">
                    <span className="badge badge-primary">{event.topic}</span>
                  </p>
                  <p>{event.description?.substring(0, 100)}...</p>
                </div>
                <Link to={`/events`} className="btn btn-secondary btn-sm">
                  View Details
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;


