import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import i18n from './i18n';
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
import Onboarding from './pages/Onboarding';
import { Exchanges, ExchangeDetail } from './pages/Exchanges';
import ExchangeChat from './pages/ExchangeChat';
import { TermsView, TermsAcceptance } from './pages/Terms';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Default language fallback
const DEFAULT_LANGUAGE = 'en';

// Helper to safely get language with fallback
const getSafeLanguage = (lang) => {
  const supportedLanguages = ['es', 'en', 'pt', 'fr', 'de', 'it'];
  if (lang && supportedLanguages.includes(lang)) {
    return lang;
  }
  return DEFAULT_LANGUAGE;
};

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

// Private route that checks for onboarding completion
const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
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
      // Check user profile for onboarding_completed
      const userResponse = await api.get('/auth/me');
      const userData = userResponse.data;
      
      // Update cached user data
      localStorage.setItem('user', JSON.stringify(userData));
      
      // Update language from server if available
      const userLang = getSafeLanguage(userData.language);
      if (i18n.language !== userLang) {
        i18n.changeLanguage(userLang);
      }
      
      // Check if onboarding is needed
      if (!userData.onboarding_completed) {
        setNeedsOnboarding(true);
        setCheckingStatus(false);
        return;
      }
      
      // User is fully onboarded
      setNeedsOnboarding(false);
    } catch (error) {
      console.error('Failed to check status:', error);
      setNeedsOnboarding(false);
    } finally {
      setCheckingStatus(false);
    }
  };
  
  const handleOnboardingComplete = (updatedUser) => {
    // User has completed onboarding
    setNeedsOnboarding(false);
  };
  
  if (!token) return <Navigate to="/" />;
  
  if (checkingStatus) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="text-4xl font-black text-primary mb-2">MisFigus</div>
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </div>
    );
  }
  
  // Show onboarding if not completed
  if (needsOnboarding) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }
  
  return children;
};

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [languageReady, setLanguageReady] = useState(false);

  // Initialize language on app startup
  useEffect(() => {
    const initializeApp = async () => {
      try {
        const token = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        
        if (token && storedUser) {
          try {
            const userData = JSON.parse(storedUser);
            setUser(userData);
            
            // Load user's saved language preference with fallback
            const userLang = getSafeLanguage(userData.language);
            await i18n.changeLanguage(userLang);
          } catch (parseError) {
            // Invalid stored user data, clear it
            localStorage.removeItem('user');
            await i18n.changeLanguage(DEFAULT_LANGUAGE);
          }
        } else {
          // No user, use default language
          await i18n.changeLanguage(DEFAULT_LANGUAGE);
        }
      } catch (error) {
        console.error('Failed to initialize app:', error);
        // Ensure we always have a language set
        await i18n.changeLanguage(DEFAULT_LANGUAGE);
      } finally {
        setLanguageReady(true);
        setLoading(false);
      }
    };
    
    initializeApp();
  }, []);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    
    // Set language from user data with fallback
    const userLang = getSafeLanguage(userData.language);
    i18n.changeLanguage(userLang);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    // Reset to default language on logout
    i18n.changeLanguage(DEFAULT_LANGUAGE);
  };

  // Show loading screen until language is ready
  if (loading || !languageReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="text-4xl font-black text-primary mb-2">MisFigus</div>
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout }}>
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
