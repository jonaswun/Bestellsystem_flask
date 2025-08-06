"""
File utilities for the ordering system.
"""
import csv
import os
from datetime import datetime


def save_order_csv(data, csv_path, user_info=None):
    """
    Save order data to CSV file as a backup
    
    Args:
        data (dict): Order data
        csv_path (str): Path to CSV file
        user_info (dict): User information including user_id, username, role
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'timestamp', 'table_number', 'user_id', 'username', 'user_role', 
            'comment', 'total_price', 'items'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        # Calculate total price
        total_price = sum(
            item.get('price', 0) * item.get('quantity', 1) 
            for item in data.get('orderedItems', [])
        )
        
        # Format items as string
        items_str = '; '.join([
            f"{item.get('name', 'Unknown')} (x{item.get('quantity', 1)}) - ${item.get('price', 0):.2f}"
            for item in data.get('orderedItems', [])
        ])
        
        # Extract user information
        user_id = user_info.get('user_id') if user_info else None
        username = user_info.get('username') if user_info else None
        user_role = user_info.get('role') if user_info else None
        
        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'table_number': data.get('tableNumber'),
            'user_id': user_id,
            'username': username,
            'user_role': user_role,
            'comment': data.get('comment', ''),
            'total_price': total_price,
            'items': items_str
        })