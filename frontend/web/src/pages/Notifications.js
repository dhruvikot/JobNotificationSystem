import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { notificationsAPI } from '../api/api';
import websocketService from '../services/websocketService';
import './Notifications.css';

function Notifications() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
    
    // Subscribe to real-time notifications
    const handleNewNotification = (notification) => {
      console.log('[Notifications Page] Real-time notification received:', notification);
      setNotifications(prev => {
        console.log('[Notifications Page] Current notifications count:', prev.length);
        console.log('[Notifications Page] Adding new notification to top');
        return [notification, ...prev];
      });
    };
    
    websocketService.subscribe(handleNewNotification);
    
    // Cleanup: unsubscribe on unmount
    return () => {
      websocketService.unsubscribe(handleNewNotification);
    };
  }, []);

  const loadNotifications = async () => {
    try {
      const response = await notificationsAPI.getNotifications(user.user_id);
      setNotifications(response.data.notifications || []);
    } catch (err) {
      console.error('Error loading notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'badge-danger';
      case 'medium':
        return 'badge-warning';
      default:
        return 'badge-primary';
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading notifications...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1>Notifications</h1>
        {notifications.length > 0 && (
          <span className="notif-count">{notifications.length} unread</span>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <h2>No notifications yet</h2>
            <p>You'll see notifications here when events matching your subscriptions are published.</p>
          </div>
        </div>
      ) : (
        <div className="notifications-list">
          {notifications.map((notif, index) => (
            <div key={index} className={`notification-card ${!notif.read ? 'unread' : ''}`}>
              <div className="notif-header">
                <span className={`badge ${getPriorityColor(notif.priority)}`}>
                  {notif.priority}
                </span>
                <span className="notif-time">{formatDate(notif.timestamp)}</span>
              </div>
              <h3>{notif.title}</h3>
              <p className="notif-description">{notif.description}</p>
              <div className="notif-meta">
                <span className="notif-topic">
                  <span className="badge badge-primary">{notif.topic}</span>
                </span>
                {notif.location && (
                  <span className="notif-location">
                    📍 {notif.location}
                  </span>
                )}
                {notif.start_time && (
                  <span className="notif-date">
                    📅 {new Date(notif.start_time * 1000).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Notifications;


