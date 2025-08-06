import { useState } from 'react';
import axios from 'axios';
import './LoginForm.css';

function LoginForm({ onLoginSuccess }) {
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        email: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleInputChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        // Clear error when user starts typing
        if (error) setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (!isLogin && formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters long');
            setLoading(false);
            return;
        }

        try {
            const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
            const payload = {
                username: formData.username,
                password: formData.password,
                ...((!isLogin && formData.email) && { email: formData.email })
            };

            const response = await axios.post(endpoint, payload, {
                withCredentials: true
            });

            if (isLogin) {
                onLoginSuccess(response.data.user);
            } else {
                // After successful registration, switch to login
                setIsLogin(true);
                setFormData({ username: '', password: '', email: '', confirmPassword: '' });
                setError('Registration successful! Please log in.');
            }
        } catch (error) {
            console.error('Auth error:', error);
            setError(error.response?.data?.error || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    const toggleMode = () => {
        setIsLogin(!isLogin);
        setError('');
        setFormData({ username: '', password: '', email: '', confirmPassword: '' });
    };

    return (
        <div className="login-container">
            <div className="login-form">
                <div className="logo">
                    <h1>Rucksackberger</h1>
                    <p>Order System</p>
                </div>
                
                <form onSubmit={handleSubmit}>
                    <h2>{isLogin ? 'Login' : 'Register'}</h2>
                    
                    {error && <div className="error-message">{error}</div>}
                    
                    <div className="form-group">
                        <input
                            type="text"
                            name="username"
                            placeholder="Username"
                            value={formData.username}
                            onChange={handleInputChange}
                            required
                            disabled={loading}
                        />
                    </div>

                    {!isLogin && (
                        <div className="form-group">
                            <input
                                type="email"
                                name="email"
                                placeholder="Email (optional)"
                                value={formData.email}
                                onChange={handleInputChange}
                                disabled={loading}
                            />
                        </div>
                    )}
                    
                    <div className="form-group">
                        <input
                            type="password"
                            name="password"
                            placeholder="Password"
                            value={formData.password}
                            onChange={handleInputChange}
                            required
                            disabled={loading}
                        />
                    </div>

                    {!isLogin && (
                        <div className="form-group">
                            <input
                                type="password"
                                name="confirmPassword"
                                placeholder="Confirm Password"
                                value={formData.confirmPassword}
                                onChange={handleInputChange}
                                required
                                disabled={loading}
                            />
                        </div>
                    )}
                    
                    <button type="submit" disabled={loading}>
                        {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
                    </button>
                    
                    <div className="toggle-mode">
                        {isLogin ? (
                            <>
                                Don't have an account? 
                                <button type="button" onClick={toggleMode} className="link-button">
                                    Register here
                                </button>
                            </>
                        ) : (
                            <>
                                Already have an account? 
                                <button type="button" onClick={toggleMode} className="link-button">
                                    Login here
                                </button>
                            </>
                        )}
                    </div>
                </form>
            </div>
        </div>
    );
}

export default LoginForm;
