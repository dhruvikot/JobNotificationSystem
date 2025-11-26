import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../api/api';
import './AdminPanel.css';

function AdminPanel() {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    phone: '',
    role: 'organizer'
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Redirect if not admin
  if (!user || user.role !== 'admin') {
    return (
      <div className="container">
        <div className="card">
          <h2>Access Denied</h2>
          <p>You must be an administrator to access this page.</p>
        </div>
      </div>
    );
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await authAPI.adminCreateUser(formData);
      
      setMessage({ 
        type: 'success', 
        text: `Successfully created ${formData.role} account for ${formData.name}!` 
      });
      
      // Reset form
      setFormData({
        email: '',
        password: '',
        name: '',
        phone: '',
        role: 'organizer'
      });

      // Show success message for longer
      setTimeout(() => {
        setMessage({ type: '', text: '' });
      }, 5000);
      
    } catch (err) {
      console.error('Error creating user:', err);
      setMessage({ 
        type: 'error', 
        text: err.response?.data?.error || 'Failed to create user. Please try again.' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>Admin Panel</h1>
        <p>Create new user accounts for publishers, students, or administrators</p>
      </div>

      <div className="admin-panel-card">
        <h2>Create New User</h2>
        
        {message.text && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="admin-form">
          <div className="form-group">
            <label htmlFor="name">Full Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="John Doe"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="user@example.com"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password *</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength="6"
              placeholder="Minimum 6 characters"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone (Optional)</label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="+1234567890"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="role">User Role *</label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              required
              className="form-input"
            >
              <option value="organizer">Organizer/Publisher</option>
              <option value="student">Student</option>
              <option value="admin">Administrator</option>
            </select>
            <small className="form-help">
              {formData.role === 'organizer' && '✏️ Can create and publish events'}
              {formData.role === 'student' && '👨‍🎓 Can subscribe to topics and receive notifications'}
              {formData.role === 'admin' && '🔐 Full system access and user management'}
            </small>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Creating User...' : `Create ${formData.role.charAt(0).toUpperCase() + formData.role.slice(1)} Account`}
          </button>
        </form>

        <div className="role-descriptions">
          <h3>Role Descriptions</h3>
          <div className="role-card">
            <h4>📝 Organizer/Publisher</h4>
            <ul>
              <li>Create and manage events</li>
              <li>Publish events to notify subscribers</li>
              <li>View event analytics</li>
              <li>Manage event lifecycle (draft/published)</li>
            </ul>
          </div>
          <div className="role-card">
            <h4>👨‍🎓 Student</h4>
            <ul>
              <li>Browse published events</li>
              <li>Subscribe to topics of interest</li>
              <li>Receive real-time notifications</li>
              <li>View notification history</li>
            </ul>
          </div>
          <div className="role-card">
            <h4>🔐 Administrator</h4>
            <ul>
              <li>Create and manage user accounts</li>
              <li>Full access to all system features</li>
              <li>View system health and metrics</li>
              <li>Manage all events and subscriptions</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminPanel;

