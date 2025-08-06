# User Authentication System

This document describes the user authentication system added to the Rucksackberger ordering system.

## Features

### Backend Authentication
- **User Registration & Login**: Secure password hashing using Werkzeug
- **Session Management**: Flask sessions with secure cookies
- **Role-Based Access Control**: Customer, Staff, Manager, Admin roles
- **User Management**: Admin interface for managing users
- **Order Attribution**: Orders are now linked to users for better tracking
- **Enhanced Analytics**: User-based analytics and reporting

### Frontend Authentication
- **Login/Register Form**: Modern, responsive design
- **Authentication Context**: React context for managing user state
- **User Profile**: View user information and logout functionality
- **Protected Routes**: Authentication required for placing orders
- **User Management**: Admin interface for viewing users

## User Roles

1. **Customer** (Default)
   - Place orders
   - View own order history
   - View own statistics

2. **Staff**
   - All customer permissions
   - Update order status
   - View all orders
   - Access basic analytics

3. **Manager**
   - All staff permissions
   - Advanced analytics
   - User activity monitoring

4. **Admin**
   - All manager permissions
   - User management
   - System configuration

## Database Schema Updates

### New Tables
- `users`: Store user accounts and authentication data
- `user_sessions`: Track user login sessions

### Updated Tables
- `orders`: Added user tracking fields (user_id, username, user_role)

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/check` - Check authentication status
- `GET /api/auth/profile` - Get user profile
- `GET /api/auth/users` - Get all users (admin only)

### Enhanced Order Endpoints
- All order endpoints now require authentication
- Orders are automatically attributed to the logged-in user
- Role-based access control for viewing/managing orders

### Enhanced Analytics
- `GET /api/analytics/user-activity` - User activity stats (staff+)
- `GET /api/analytics/my-orders` - Personal order statistics

## Default Admin Account

A default admin account is created automatically:
- **Username**: `admin`
- **Password**: `admin123`
- **⚠️ IMPORTANT**: Change this password immediately in production!

## Security Features

- Password hashing with Werkzeug's secure methods
- Session-based authentication with secure cookies
- CORS configuration for frontend integration
- Role-based access control on all endpoints
- Input validation and error handling

## Usage

### For Customers
1. Register a new account or login
2. Browse the menu and place orders
3. View your order history and statistics

### For Staff/Management
1. Login with staff/manager/admin credentials
2. Access order management features
3. View analytics and user activity
4. Update order statuses

### For Administrators
1. Login with admin credentials
2. Access user management interface
3. View system-wide analytics
4. Manage user roles and permissions

## Configuration

### Session Configuration
- Sessions are configured in `flask_app/main.py`
- Cookie settings can be adjusted in the configuration

### CORS Configuration
- Configured to allow credentials
- Frontend origins are whitelisted

## File Structure

```
flask_app/
├── routes/
│   └── auth_routes.py          # Authentication endpoints
├── services/
│   └── auth_service.py         # Authentication business logic
└── main.py                     # Updated with session config

frontend/src/
├── AuthContext.jsx             # React authentication context
├── LoginForm.jsx               # Login/register component
├── UserProfile.jsx             # User profile component
├── UserManagement.jsx          # Admin user management
└── App.jsx                     # Updated with auth integration
```

## Development Notes

- All new features are backward compatible
- Existing orders without user attribution still work
- Frontend gracefully handles authentication states
- Error handling provides clear feedback to users

## Future Enhancements

Potential future improvements:
- Password reset functionality
- Email verification
- Two-factor authentication
- OAuth integration (Google, Facebook, etc.)
- Advanced user permissions
- User preferences and settings
