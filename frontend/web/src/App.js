import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Subscriptions from './pages/Subscriptions';
import Events from './pages/Events';
import CreateEvent from './pages/CreateEvent';
import Notifications from './pages/Notifications';
import AdminPanel from './pages/AdminPanel';

// Auth context
import { AuthProvider, useAuth } from './context/AuthContext';

// Protected route wrapper
function ProtectedRoute({ children }) {
  const { token } = useAuth();
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function AppContent() {
  const { token } = useAuth();
  
  return (
    <div className="App">
      {token && <Navbar />}
      <Routes>
        <Route path="/login" element={token ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/register" element={token ? <Navigate to="/dashboard" /> : <Register />} />
        
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/subscriptions" element={<ProtectedRoute><Subscriptions /></ProtectedRoute>} />
        <Route path="/events" element={<ProtectedRoute><Events /></ProtectedRoute>} />
        <Route path="/events/create" element={<ProtectedRoute><CreateEvent /></ProtectedRoute>} />
        <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><AdminPanel /></ProtectedRoute>} />
        
        <Route path="/" element={<Navigate to={token ? "/dashboard" : "/login"} replace />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;


