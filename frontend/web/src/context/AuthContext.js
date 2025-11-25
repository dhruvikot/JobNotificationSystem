import React, { createContext, useState, useContext, useEffect } from 'react';
import websocketService from '../services/websocketService';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load token and user from localStorage on mount
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      const userData = JSON.parse(savedUser);
      setToken(savedToken);
      setUser(userData);
      
      // Connect WebSocket for real-time notifications
      if (userData.user_id) {
        console.log('[Auth] Connecting WebSocket for user:', userData.user_id);
        websocketService.connect(userData.user_id);
      }
    }
    
    setLoading(false);
  }, []);

  const login = (token, user) => {
    setToken(token);
    setUser(user);
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    
    // Connect WebSocket for real-time notifications
    if (user.user_id) {
      console.log('[Auth] Connecting WebSocket after login');
      websocketService.connect(user.user_id);
      
      // Request notification permission
      websocketService.requestNotificationPermission();
    }
  };

  const logout = () => {
    // Disconnect WebSocket
    console.log('[Auth] Disconnecting WebSocket on logout');
    websocketService.disconnect();
    
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const value = {
    token,
    user,
    login,
    logout,
    loading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


