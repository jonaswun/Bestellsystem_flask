import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Check authentication status on app load
    useEffect(() => {
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/auth/check', {
                withCredentials: true
            });
            
            if (response.data.authenticated) {
                setUser(response.data.user);
            } else {
                setUser(null);
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password) => {
        try {
            setError(null);
            const response = await axios.post('/api/auth/login', {
                username,
                password
            }, {
                withCredentials: true
            });
            
            setUser(response.data.user);
            return { success: true, user: response.data.user };
        } catch (error) {
            const errorMessage = error.response?.data?.error || 'Login failed';
            setError(errorMessage);
            return { success: false, error: errorMessage };
        }
    };

    const logout = async () => {
        try {
            await axios.post('/api/auth/logout', {}, {
                withCredentials: true
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setUser(null);
        }
    };

    const register = async (username, password, email = '') => {
        try {
            setError(null);
            const response = await axios.post('/api/auth/register', {
                username,
                password,
                email
            }, {
                withCredentials: true
            });
            
            return { success: true, message: 'Registration successful' };
        } catch (error) {
            const errorMessage = error.response?.data?.error || 'Registration failed';
            setError(errorMessage);
            return { success: false, error: errorMessage };
        }
    };

    const value = {
        user,
        loading,
        error,
        login,
        logout,
        register,
        checkAuthStatus,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        isStaff: user?.role && ['staff', 'manager', 'admin'].includes(user.role),
        isCustomer: user?.role === 'customer'
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}
