import { useState, useEffect } from 'react';
import axios from 'axios';
import './Dashboard.css';

function Dashboard() {
    const [orders, setOrders] = useState([]);
    const [error, setError] = useState(null);

    const fetchOrders = async () => {
        try {
            const response = await axios.get('/api/orders/dashboard/food');
            console.log('API Response:', response.data); // Debug log

            // Ensure orders exist and filter out completed ones
            const validOrders = response.data.orders?.filter(order =>
                order && order.status !== 'completed'
            ) || [];

            setOrders(validOrders);
        } catch (err) {
            setError('Failed to fetch orders');
            console.error('Error:', err);
        }
    };

    const handleComplete = async (order_timestamp) => {
        try {
            // Send request to mark order as complete
            const response = await axios.put('/api/orders/dashboard/complete', {
                timestamp: order_timestamp  // This matches your backend's expected format
            });
            console.log('Complete response:', response.data); // Debug log

            // Update local state to remove completed order
            setOrders(prevOrders => prevOrders.filter(order => order.timestamp !== order_timestamp));

        } catch (err) {
            setError('Failed to complete order');
            console.error('Error completing order:', err);
        }
    };

    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 3000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    return (
        <div className="dashboard">
            <h1>Offene Bestellungen Essen</h1>
            <div className="orders-grid">
                {orders.map((order, index) => (
                    <div key={index} className="order-card">
                        <h2>Tisch Nr: {order.tableNumber}</h2>
                        <div className="order-items">
                            {order.orderedItems
                                .filter(item => item.type === 'food')
                                .map((item, idx) => (
                                    <div key={idx} className="order-item">
                                        <span>{item.quantity}x {item.name}</span>
                                    </div>
                                ))}
                        </div>
                        {order.comment && (
                            <div className="order-comment">
                                Note: {order.comment}
                            </div>
                        )}
                        <div className="order-total">
                            Total: {order.totalCost.toFixed(2)}€
                        </div>
                        <button
                            onClick={() => handleComplete(order.timestamp)}
                            className="complete-button"
                        >
                            Erledigt
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Dashboard;