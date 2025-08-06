import { useState } from 'react';
import { useAuth } from './AuthContext';
import './UserProfile.css';

function UserProfile({ onClose }) {
    const { user, logout } = useAuth();
    const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

    const handleLogout = async () => {
        await logout();
        onClose();
    };

    const getRoleDisplay = (role) => {
        const roles = {
            'customer': 'Customer',
            'staff': 'Staff',
            'manager': 'Manager',
            'admin': 'Administrator'
        };
        return roles[role] || role;
    };

    const getRoleBadgeClass = (role) => {
        const classes = {
            'customer': 'badge-customer',
            'staff': 'badge-staff',
            'manager': 'badge-manager',
            'admin': 'badge-admin'
        };
        return classes[role] || 'badge-default';
    };

    return (
        <div className="profile-overlay">
            <div className="profile-modal">
                <div className="profile-header">
                    <h2>User Profile</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>
                
                <div className="profile-content">
                    <div className="user-info">
                        <div className="avatar">
                            {user.username.charAt(0).toUpperCase()}
                        </div>
                        
                        <div className="user-details">
                            <h3>{user.username}</h3>
                            <p className="user-email">{user.email || 'No email set'}</p>
                            <span className={`role-badge ${getRoleBadgeClass(user.role)}`}>
                                {getRoleDisplay(user.role)}
                            </span>
                        </div>
                    </div>
                    
                    <div className="profile-stats">
                        <div className="stat-item">
                            <span className="stat-label">User ID</span>
                            <span className="stat-value">#{user.id}</span>
                        </div>
                        
                        {user.created_at && (
                            <div className="stat-item">
                                <span className="stat-label">Member since</span>
                                <span className="stat-value">
                                    {new Date(user.created_at).toLocaleDateString()}
                                </span>
                            </div>
                        )}
                        
                        {user.last_login && (
                            <div className="stat-item">
                                <span className="stat-label">Last login</span>
                                <span className="stat-value">
                                    {new Date(user.last_login).toLocaleString()}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
                
                <div className="profile-actions">
                    {!showLogoutConfirm ? (
                        <button 
                            className="logout-btn"
                            onClick={() => setShowLogoutConfirm(true)}
                        >
                            Logout
                        </button>
                    ) : (
                        <div className="logout-confirm">
                            <p>Are you sure you want to logout?</p>
                            <div className="confirm-buttons">
                                <button 
                                    className="logout-btn confirm"
                                    onClick={handleLogout}
                                >
                                    Yes, Logout
                                </button>
                                <button 
                                    className="cancel-btn"
                                    onClick={() => setShowLogoutConfirm(false)}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default UserProfile;
