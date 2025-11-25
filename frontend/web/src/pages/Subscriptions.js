import React, { useEffect, useState } from 'react';
import { subscriptionsAPI } from '../api/api';
import './Subscriptions.css';

function Subscriptions() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [selectedChannels, setSelectedChannels] = useState(['app']);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [subsRes, topicsRes] = await Promise.all([
        subscriptionsAPI.getSubscriptions(),
        subscriptionsAPI.getTopics()
      ]);

      setSubscriptions(subsRes.data.subscriptions || []);
      setTopics(topicsRes.data.topics || []);
    } catch (err) {
      console.error('Error loading subscriptions:', err);
      setError('Failed to load subscriptions');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSubscription = async () => {
    if (!selectedTopic) {
      setError('Please select a topic');
      return;
    }

    try {
      await subscriptionsAPI.createSubscription({
        topic: selectedTopic,
        channels: selectedChannels
      });

      setShowAddModal(false);
      setSelectedTopic('');
      setSelectedChannels(['app']);
      setError('');
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to add subscription');
    }
  };

  const handleDeleteSubscription = async (topic) => {
    if (!window.confirm('Are you sure you want to unsubscribe?')) return;

    try {
      await subscriptionsAPI.deleteSubscription(topic);
      loadData();
    } catch (err) {
      setError('Failed to delete subscription');
    }
  };

  const toggleChannel = (channel) => {
    if (selectedChannels.includes(channel)) {
      setSelectedChannels(selectedChannels.filter(c => c !== channel));
    } else {
      setSelectedChannels([...selectedChannels, channel]);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading subscriptions...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1>My Subscriptions</h1>
        <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
          + Add Subscription
        </button>
      </div>

      {subscriptions.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <h2>No subscriptions yet</h2>
            <p>Start by adding your first subscription to receive notifications about events you care about.</p>
          </div>
        </div>
      ) : (
        <div className="subscriptions-grid">
          {subscriptions.map((sub) => (
            <div key={sub.topic} className="subscription-card">
              <div className="subscription-header">
                <span className="badge badge-primary">{sub.topic}</span>
              </div>
              <div className="subscription-channels">
                {sub.channels.map((channel) => (
                  <span key={channel} className="channel-badge">
                    {channel === 'app' ? '📱' : channel === 'email' ? '📧' : '📞'} {channel}
                  </span>
                ))}
              </div>
              <button
                onClick={() => handleDeleteSubscription(sub.topic)}
                className="btn btn-danger btn-sm"
              >
                Unsubscribe
              </button>
            </div>
          ))}
        </div>
      )}

      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add Subscription</h2>
            
            <div className="form-group">
              <label>Select Topic</label>
              <select value={selectedTopic} onChange={(e) => setSelectedTopic(e.target.value)}>
                <option value="">Choose a topic...</option>
                {topics.map((topic) => (
                  <option key={topic.topic} value={topic.topic}>
                    {topic.name} ({topic.topic})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Notification Channels</label>
              <div className="channels-select">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedChannels.includes('app')}
                    onChange={() => toggleChannel('app')}
                  />
                  📱 In-App
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedChannels.includes('email')}
                    onChange={() => toggleChannel('email')}
                  />
                  📧 Email
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedChannels.includes('sms')}
                    onChange={() => toggleChannel('sms')}
                  />
                  📞 SMS
                </label>
              </div>
            </div>

            {error && <div className="error">{error}</div>}

            <div className="modal-actions">
              <button onClick={() => setShowAddModal(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={handleAddSubscription} className="btn btn-primary">
                Add Subscription
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Subscriptions;


