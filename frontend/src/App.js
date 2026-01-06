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
import CompleteProfile from './pages/CompleteProfile';
import { Exchanges, ExchangeDetail } from './pages/Exchanges';
import ExchangeChat from './pages/ExchangeChat';
import { TermsView, TermsAcceptance } from './pages/Terms';

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

// Private route that also checks for terms acceptance and profile completion
const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const [needsTerms, setNeedsTerms] = useState(false);
  const [needsProfile, setNeedsProfile] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);
  
  useEffect(() => {
    if (token) {
      checkStatus();
    } else {
      setCheckingStatus(false);
    }
  }, [token]);
  
  const checkStatus = async () => {
    try {
      // Check cached terms status first to avoid repeated API calls
      const cachedTermsVersion = localStorage.getItem('termsAcceptedVersion');
      const currentVersion = '1.0'; // Must match backend CURRENT_TERMS_VERSION
      
      // Check user profile for displayName
      const userResponse = await api.get('/auth/me');
      const userData = userResponse.data;
      
      // Update cached user data
      localStorage.setItem('user', JSON.stringify(userData));
      
      // Check if profile needs completion (no display_name)
      if (!userData.display_name) {
        setNeedsProfile(true);
        setCheckingStatus(false);
        return;
      }
      
      if (cachedTermsVersion === currentVersion) {
        // Already accepted current version
        setNeedsTerms(false);
        setCheckingStatus(false);
        return;
      }
      
      // Check with backend
      const response = await api.get('/user/terms-status');
      const needsAcceptance = response.data.needs_acceptance;
      
      // Cache the result if accepted
      if (!needsAcceptance && response.data.terms_version) {
        localStorage.setItem('termsAcceptedVersion', response.data.terms_version);
      }
      
      setNeedsTerms(needsAcceptance);
    } catch (error) {
      console.error('Failed to check status:', error);
      setNeedsTerms(false);
      setNeedsProfile(false);
    } finally {
      setCheckingStatus(false);
    }
  };
  
  const handleProfileComplete = (updatedUser) => {
    // User has completed their profile
    setNeedsProfile(false);
  };
  
  const handleTermsAccepted = () => {
    // Cache the acceptance
    localStorage.setItem('termsAcceptedVersion', '1.0');
    setNeedsTerms(false);
  };
  
  if (!token) return <Navigate to="/" />;
  
  if (checkingStatus) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">Loading...</div>
      </div>
    );
  }
  
  // Profile completion takes priority over terms
  if (needsProfile) {
    return <CompleteProfile onComplete={handleProfileComplete} />;
  }
  
  if (needsTerms) {
    return <TermsAcceptance onAccepted={handleTermsAccepted} />;
  }
  
  return children;
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
          {/* Album-based inventory/matches/exchanges routes */}
          <Route path="/albums/:albumId/inventory" element={<PrivateRoute><Inventory /></PrivateRoute>} />
          <Route path="/albums/:albumId/matches" element={<PrivateRoute><Matches /></PrivateRoute>} />
          <Route path="/albums/:albumId/exchanges" element={<PrivateRoute><Exchanges /></PrivateRoute>} />
          {/* Exchange routes */}
          <Route path="/exchanges/:exchangeId" element={<PrivateRoute><ExchangeDetail /></PrivateRoute>} />
          <Route path="/exchanges/:exchangeId/chat" element={<PrivateRoute><ExchangeChat /></PrivateRoute>} />
          {/* Settings and Profile */}
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
          {/* Terms */}
          <Route path="/terms" element={<PrivateRoute><TermsView /></PrivateRoute>} />
        </Routes>
        <Toaster position="top-center" richColors />
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
