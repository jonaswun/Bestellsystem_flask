import { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import axios from 'axios';
import './UserManagement.css';

function UserManagement({ onClose }) {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { user } = useAuth();

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/auth/users', {
                withCredentials: true
            });
            setUsers(response.data.users);
        } catch (error) {
            setError(error.response?.data?.error || 'Failed to fetch users');
        } finally {
            setLoading(false);
        }
    };

    const getRoleColor = (role) => {
        const colors = {
            'customer': '#2196F3',
            'staff': '#9C27B0',
            'manager': '#FF9800',
            'admin': '#F44336'
        };
        return colors[role] || '#757575';
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Never';
        return new Date(dateString).toLocaleDateString();
    };

    if (!user || user.role !== 'admin') {
        return (
            <div className="management-overlay">
                <div className="management-modal">
                    <div className="error-message">
                        Access denied. Admin privileges required.
                    </div>
                    <button onClick={onClose}>Close</button>
                </div>
            </div>
        );
    }

    return (
        <div className="management-overlay">
            <div className="management-modal">
                <div className="management-header">
                    <h2>User Management</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="management-content">
                    {loading ? (
                        <div className="loading">Loading users...</div>
                    ) : error ? (
                        <div className="error-message">{error}</div>
                    ) : (
                        <div className="users-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Username</th>
                                        <th>Email</th>
                                        <th>Role</th>
                                        <th>Created</th>
                                        <th>Last Login</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.map(userItem => (
                                        <tr key={userItem.id}>
                                            <td>{userItem.id}</td>
                                            <td>
                                                <strong>{userItem.username}</strong>
                                                {userItem.id === user.id && (
                                                    <span className="current-user"> (You)</span>
                                                )}
                                            </td>
                                            <td>{userItem.email || 'N/A'}</td>
                                            <td>
                                                <span 
                                                    className="role-badge"
                                                    style={{ 
                                                        backgroundColor: getRoleColor(userItem.role),
                                                        color: 'white'
                                                    }}
                                                >
                                                    {userItem.role}
                                                </span>
                                            </td>
                                            <td>{formatDate(userItem.created_at)}</td>
                                            <td>{formatDate(userItem.last_login)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                <div className="management-footer">
                    <p>Total Users: {users.length}</p>
                </div>
            </div>
        </div>
    );
}

export default UserManagement;
