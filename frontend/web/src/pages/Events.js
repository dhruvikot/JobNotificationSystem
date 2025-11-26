import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { eventsAPI } from '../api/api';
import './Events.css';

function Events() {
  const { user } = useAuth();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    loadEvents();
  }, [filter]);

  const loadEvents = async () => {
    try {
      const params = filter ? { topic: filter } : {};
      const response = await eventsAPI.getEvents(params);
      setEvents(response.data.events || []);
    } catch (err) {
      console.error('Error loading events:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUnpublish = async (eventId) => {
    if (!window.confirm('Are you sure you want to unpublish this event? It will no longer be visible to students.')) {
      return;
    }

    try {
      await eventsAPI.unpublishEvent(eventId);
      alert('Event unpublished successfully!');
      loadEvents(); // Reload events
    } catch (err) {
      console.error('Error unpublishing event:', err);
      alert(err.response?.data?.error || 'Failed to unpublish event');
    }
  };

  const handlePublish = async (eventId) => {
    if (!window.confirm('Are you sure you want to publish this event? All subscribed students will be notified.')) {
      return;
    }

    try {
      await eventsAPI.publishEvent(eventId);
      alert('Event published successfully! Notifications sent to subscribers.');
      loadEvents(); // Reload events
    } catch (err) {
      console.error('Error publishing event:', err);
      alert(err.response?.data?.error || 'Failed to publish event');
    }
  };

  const isOrganizer = user && (user.role === 'organizer' || user.role === 'admin');

  const formatDate = (timestamp) => {
    if (!timestamp) return 'TBD';
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading events...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1>Events</h1>
        <div>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} className="filter-select">
            <option value="">All Categories</option>
            <option value="hackathon.aiml">AI/ML Hackathons</option>
            <option value="hackathon.web">Web Hackathons</option>
            <option value="jobs.internship">Internships</option>
            <option value="jobs.fulltime">Full-Time Jobs</option>
            <option value="careerfair.tech">Tech Career Fairs</option>
            <option value="workshop.technical">Technical Workshops</option>
          </select>
        </div>
      </div>

      {events.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <h2>No events found</h2>
            <p>Check back later for new events!</p>
          </div>
        </div>
      ) : (
        <div className="events-grid">
          {events.map((event) => (
            <div key={event.event_id} className="event-card">
              {event.media_url && (
                <div className="event-image">
                  <img src={event.media_url} alt={event.title} />
                </div>
              )}
              <div className="event-content">
                <div className="event-meta">
                  <span className="badge badge-primary">{event.topic}</span>
                  {event.status === 'published' ? (
                    <span className="badge badge-success">✓ Published</span>
                  ) : (
                    <span className="badge badge-warning">📝 Draft</span>
                  )}
                </div>
                <h3>{event.title}</h3>
                <p className="event-description">{event.description}</p>
                <div className="event-details">
                  <div className="detail-item">
                    <span className="detail-icon">📅</span>
                    <span>{formatDate(event.start_time)}</span>
                  </div>
                  {event.location && (
                    <div className="detail-item">
                      <span className="detail-icon">📍</span>
                      <span>{event.location}</span>
                    </div>
                  )}
                </div>
                {isOrganizer && (
                  <div className="event-actions">
                    {event.status === 'draft' ? (
                      <button 
                        onClick={() => handlePublish(event.event_id)}
                        className="btn btn-primary btn-sm"
                      >
                        📤 Publish Event
                      </button>
                    ) : (
                      <button 
                        onClick={() => handleUnpublish(event.event_id)}
                        className="btn btn-secondary btn-sm"
                      >
                        📥 Unpublish
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Events;
