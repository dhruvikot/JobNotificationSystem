import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { eventsAPI } from '../api/api';
import './CreateEvent.css';

function CreateEvent() {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    topic: '',
    start_time: '',
    end_time: '',
    location: '',
    level: '',
    media_url: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      // Convert date strings to Unix timestamps
      const startTimestamp = new Date(formData.start_time).getTime() / 1000;
      const endTimestamp = formData.end_time 
        ? new Date(formData.end_time).getTime() / 1000 
        : startTimestamp + 3600;

      const eventData = {
        ...formData,
        start_time: startTimestamp,
        end_time: endTimestamp
      };

      const response = await eventsAPI.createEvent(eventData);
      const eventId = response.data.event_id;

      setSuccess('Event created successfully!');
      
      // Ask if they want to publish immediately
      if (window.confirm('Event created! Do you want to publish it now?')) {
        await eventsAPI.publishEvent(eventId);
        setSuccess('Event created and published successfully!');
      }

      setTimeout(() => {
        navigate('/events');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>Create New Event</h1>
      </div>

      <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Event Title *</label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="AI/ML Hackathon 2024"
            />
          </div>

          <div className="form-group">
            <label>Description *</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              required
              rows="4"
              placeholder="Describe your event..."
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Topic *</label>
              <select name="topic" value={formData.topic} onChange={handleChange} required>
                <option value="">Select a topic...</option>
                <optgroup label="Hackathons">
                  <option value="hackathon.aiml">AI/ML Hackathon</option>
                  <option value="hackathon.web">Web Development</option>
                  <option value="hackathon.mobile">Mobile Development</option>
                  <option value="hackathon.blockchain">Blockchain</option>
                </optgroup>
                <optgroup label="Jobs">
                  <option value="jobs.internship">Internship</option>
                  <option value="jobs.fulltime">Full-Time</option>
                  <option value="jobs.swe">Software Engineering</option>
                  <option value="jobs.datascience">Data Science</option>
                </optgroup>
                <optgroup label="Career Fairs">
                  <option value="careerfair.tech">Tech Career Fair</option>
                  <option value="careerfair.business">Business Career Fair</option>
                </optgroup>
                <optgroup label="Workshops">
                  <option value="workshop.technical">Technical Workshop</option>
                  <option value="workshop.leadership">Leadership Workshop</option>
                  <option value="workshop.career">Career Development</option>
                </optgroup>
              </select>
            </div>

            <div className="form-group">
              <label>Level</label>
              <select name="level" value={formData.level} onChange={handleChange}>
                <option value="">Any Level</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Start Date & Time *</label>
              <input
                type="datetime-local"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>End Date & Time</label>
              <input
                type="datetime-local"
                name="end_time"
                value={formData.end_time}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Location</label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="San Francisco, CA or Remote"
            />
          </div>

          <div className="form-group">
            <label>Media URL (Image/Banner)</label>
            <input
              type="url"
              name="media_url"
              value={formData.media_url}
              onChange={handleChange}
              placeholder="https://example.com/banner.jpg"
            />
          </div>

          {error && <div className="error">{error}</div>}
          {success && <div className="success">{success}</div>}

          <div className="form-actions">
            <button
              type="button"
              onClick={() => navigate('/events')}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateEvent;



