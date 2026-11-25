import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const API_URL = import.meta.env.VITE_API_URL || '/api';

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(localStorage.getItem('username') || null);
  const [role, setRole] = useState(localStorage.getItem('role') || null);
  const [loading, setLoading] = useState(true);

  const logout = () => {
    setToken(null);
    setUser(null);
    setRole(null);
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    delete axios.defaults.headers.common['Authorization'];
  };

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
    setLoading(false);
  }, [token]);

  // Set up 401 interceptor to auto-clear expired sessions
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
          logout();
        }
        return Promise.reject(error);
      }
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  const login = async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    try {
      const response = await axios.post(`${API_URL}/auth/login`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      const { access_token, role: userRole } = response.data;
      
      setToken(access_token);
      setUser(username);
      setRole(userRole);
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('username', username);
      localStorage.setItem('role', userRole);
      
      return { success: true };
    } catch (error) {
      console.error("Login failed", error);
      const detail = error.response?.data?.detail || "Authentication failed";
      return { success: false, error: detail };
    }
  };

  const register = async (username, password, selectedRole = "Analyst") => {
    try {
      await axios.post(`${API_URL}/auth/register`, {
        username,
        password,
        role: selectedRole
      });
      return { success: true };
    } catch (error) {
      console.error("Registration failed", error);
      const detail = error.response?.data?.detail || "Registration failed";
      return { success: false, error: detail };
    }
  };

  const val = {
    token,
    user,
    role,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!token
  };

  return (
    <AuthContext.Provider value={val}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const parseUTC = (dtStr) => {
  if (!dtStr) return new Date();
  let cleanStr = dtStr.toString().trim();
  if (!cleanStr.endsWith('Z') && !cleanStr.includes('+') && !cleanStr.includes('T') && cleanStr.includes(' ')) {
    cleanStr = cleanStr.replace(' ', 'T');
  }
  if (!cleanStr.endsWith('Z') && !cleanStr.includes('+')) {
    cleanStr = cleanStr + 'Z';
  }
  return new Date(cleanStr);
};

export const useAuth = () => useContext(AuthContext);
