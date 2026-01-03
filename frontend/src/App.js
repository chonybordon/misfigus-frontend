import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import './i18n';
import '@/App.css';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';

import Login from './pages/Login';
import Groups from './pages/Groups';
import GroupHome from './pages/GroupHome';
import Inventory from './pages/Inventory';
import Matches from './pages/Matches';
import Offers from './pages/Offers';
import Chat from './pages/Chat';
import Settings from './pages/Settings';

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

export const AuthContext = React.createContext();

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
          <Route path="/" element={user ? <Navigate to="/groups" /> : <Login />} />
          <Route path="/groups" element={<PrivateRoute><Groups /></PrivateRoute>} />
          <Route path="/groups/:groupId" element={<PrivateRoute><GroupHome /></PrivateRoute>} />
          <Route path="/groups/:groupId/albums/:albumId/inventory" element={<PrivateRoute><Inventory /></PrivateRoute>} />
          <Route path="/groups/:groupId/albums/:albumId/matches" element={<PrivateRoute><Matches /></PrivateRoute>} />
          <Route path="/groups/:groupId/offers" element={<PrivateRoute><Offers /></PrivateRoute>} />
          <Route path="/groups/:groupId/chat/:userId" element={<PrivateRoute><Chat /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
          <Route path="/join/:token" element={<JoinGroup />} />
        </Routes>
        <Toaster position="top-center" richColors />
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

const JoinGroup = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    const joinGroup = async () => {
      try {
        await api.post(`/invites/${token}/accept`);
        toast.success(t('common.success'));
        navigate('/groups');
      } catch (error) {
        toast.error(error.response?.data?.detail || t('common.error'));
        navigate('/');
      }
    };

    if (localStorage.getItem('token')) {
      joinGroup();
    } else {
      navigate('/');
    }
  }, [token, navigate, t]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-2xl font-bold">{t('common.loading')}</div>
    </div>
  );
};

export default App;
