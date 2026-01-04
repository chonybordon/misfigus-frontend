import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import './i18n';
import '@/App.css';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';

import Login from './pages/Login';
import Albums from './pages/Albums';
import AlbumHome from './pages/AlbumHome';
import Groups from './pages/Groups';
import GroupHome from './pages/GroupHome';
import Inventory from './pages/Inventory';
import Matches from './pages/Matches';
import Settings from './pages/Settings';
import Profile from './pages/Profile';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export const AuthContext = React.createContext(null);

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/" />;
};

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">Loading...</div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      <BrowserRouter>
        <Routes>
          {/* Default: Album selection is always the home screen */}
          <Route path="/" element={user ? <Navigate to="/albums" /> : <Login />} />
          <Route path="/albums" element={<PrivateRoute><Albums /></PrivateRoute>} />
          <Route path="/albums/:albumId" element={<PrivateRoute><AlbumHome /></PrivateRoute>} />
          {/* Group-based routes */}
          <Route path="/groups" element={<PrivateRoute><Groups /></PrivateRoute>} />
          <Route path="/groups/:groupId" element={<PrivateRoute><GroupHome /></PrivateRoute>} />
          <Route path="/groups/:groupId/inventory" element={<PrivateRoute><Inventory /></PrivateRoute>} />
          <Route path="/groups/:groupId/matches" element={<PrivateRoute><Matches /></PrivateRoute>} />
          {/* Album-based inventory/matches routes */}
          <Route path="/albums/:albumId/inventory" element={<PrivateRoute><Inventory /></PrivateRoute>} />
          <Route path="/albums/:albumId/matches" element={<PrivateRoute><Matches /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
        </Routes>
        <Toaster position="top-center" richColors />
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
