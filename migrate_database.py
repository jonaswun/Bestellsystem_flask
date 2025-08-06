#!/usr/bin/env python3
"""
Database migration script to add user authentication tables and update existing schema.
Run this script to migrate your existing database to support user authentication.
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path):
    """
    Migrate the database to add user authentication support
    """
    print(f"Migrating database: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("1. Creating users table...")
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
            
            print("2. Creating user_sessions table...")
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
            
            print("3. Adding user columns to orders table...")
            # Check if user columns already exist
            cursor.execute("PRAGMA table_info(orders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                cursor.execute('ALTER TABLE orders ADD COLUMN user_id INTEGER')
                print("   - Added user_id column")
            
            if 'username' not in columns:
                cursor.execute('ALTER TABLE orders ADD COLUMN username TEXT')
                print("   - Added username column")
            
            if 'user_role' not in columns:
                cursor.execute('ALTER TABLE orders ADD COLUMN user_role TEXT')
                print("   - Added user_role column")
            
            print("4. Creating indexes...")
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users (username)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users (email)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_orders_user_id 
                ON orders (user_id)
            ''')
            
            print("5. Creating default admin user...")
            # Check if admin user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            admin_exists = cursor.fetchone()[0] > 0
            
            if not admin_exists:
                from werkzeug.security import generate_password_hash
                admin_password = generate_password_hash('admin123')
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                ''', ('admin', 'admin@restaurant.local', admin_password, 'admin'))
                print("   - Created admin user (username: admin, password: admin123)")
                print("   - ⚠️  CHANGE THE DEFAULT PASSWORD IMMEDIATELY!")
            else:
                print("   - Admin user already exists, skipping...")
            
            conn.commit()
            print("\n✅ Database migration completed successfully!")
            print("\nDefault admin credentials:")
            print("Username: admin")
            print("Password: admin123")
            print("⚠️  Please change the default password immediately!")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure Werkzeug is installed: pip install Werkzeug")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main migration script"""
    print("🔄 Database Migration Script")
    print("=" * 40)
    
    # Find database files
    db_paths = []
    
    # Check common database locations
    common_paths = [
        "orders.db",
        "flask_app/orders.db",
        "data/orders.db",
        "flask_app/data/orders.db"
    ]
    
    for path in common_paths:
        if Path(path).exists():
            db_paths.append(path)
    
    if not db_paths:
        print("❌ No database files found!")
        print("Please ensure your orders.db file exists in one of these locations:")
        for path in common_paths:
            print(f"   - {path}")
        sys.exit(1)
    
    # Migrate each database found
    for db_path in db_paths:
        migrate_database(db_path)
        print()
    
    print("🎉 Migration complete! You can now use the authentication features.")

if __name__ == "__main__":
    main()
