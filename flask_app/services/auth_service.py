"""
Authentication service for managing user accounts and sessions.
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash


class AuthService:
    """Service for managing user authentication and authorization"""
    
    def __init__(self, db_path='orders.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize authentication tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'customer',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            ''')
            
            # Create user sessions table for tracking login sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users (username)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users (email)
            ''')
            
            conn.commit()
            
            # Create default admin user if none exists
            self._create_default_admin(cursor, conn)
    
    def _create_default_admin(self, cursor, conn):
        """Create a default admin user if no admin exists"""
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            admin_password = generate_password_hash('admin123')  # Change this in production!
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@restaurant.local', admin_password, 'admin'))
            conn.commit()
            print("Default admin user created: username='admin', password='admin123'")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_user(self, username, password, email=None, role='customer'):
        """Create a new user"""
        if not username or not password:
            raise ValueError("Username and password are required")
        
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        password_hash = generate_password_hash(password)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                raise ValueError("Username already exists")
            
            # Check if email already exists (if provided)
            if email:
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    raise ValueError("Email already exists")
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            
            conn.commit()
            return cursor.lastrowid
    
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, password_hash, role, is_active
                FROM users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Update last login
                cursor.execute('''
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (user['id'],))
                conn.commit()
                
                return dict(user)  # Convert Row to dict
            
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users 
                WHERE id = ? AND is_active = 1
            ''', (user_id,))
            
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_user_by_username(self, username):
        """Get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_all_users(self):
        """Get all active users (admin function)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users 
                WHERE is_active = 1
                ORDER BY created_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_user_role(self, user_id, new_role):
        """Update user role (admin function)"""
        valid_roles = ['customer', 'staff', 'manager', 'admin']
        if new_role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET role = ? 
                WHERE id = ?
            ''', (new_role, user_id))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def deactivate_user(self, user_id):
        """Deactivate a user (soft delete)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET is_active = 0 
                WHERE id = ?
            ''', (user_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def change_password(self, user_id, new_password):
        """Change user password"""
        if len(new_password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        password_hash = generate_password_hash(new_password)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET password_hash = ? 
                WHERE id = ?
            ''', (password_hash, user_id))
            conn.commit()
            
            return cursor.rowcount > 0
