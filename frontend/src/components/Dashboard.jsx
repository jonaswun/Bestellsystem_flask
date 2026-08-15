import { useState, useEffect } from 'react';
import axios from 'axios';
import './Dashboard.css';
import NavBar from './NavBar';

function Dashboard({ type = 'food' }) {
    const [orders, setOrders] = useState([]);
    const [error, setError] = useState(null);

    const fetchOrders = async () => {
        try {
            // Backend endpoints use 'food' and 'drinks' (plural for drinks)
            const endpointType = type === 'drink' ? 'drinks' : type;
            const response = await axios.get(`/api/orders/dashboard/${endpointType}`);
            // Filter already happens server-side; keep only what matches this dashboard's type
            const processedKey = type === 'drink' ? 'drink_processed' : 'food_processed';
            const validOrders = response.data.orders?.filter(order =>
                order && !order[processedKey]
            ) || [];

            setOrders(validOrders.map(o => ({ ...o, completing: false })));
        } catch (err) {
            setError('Failed to fetch orders');
            console.error('Error:', err);
        }
    };

    const handleComplete = async (order_id) => {
        try {
            // Optimistically mark as completing
            setOrders(prev => prev.map(o => o.id === order_id ? { ...o, completing: true } : o));

            await axios.put('/api/orders/dashboard/set_processed', { order_id, item_type: type });
            // show green check briefly then remove
            setOrders(prev => prev.map(o => o.id === order_id ? { ...o, completed: true, completing: false } : o));
            setTimeout(() => {
                setOrders(prev => prev.filter(o => o.id !== order_id));
            }, 1500);
        } catch (err) {
            setError('Failed to complete order');
            console.error('Error completing order:', err);
            // revert completing state
            setOrders(prev => prev.map(o => o.id === order_id ? { ...o, completing: false } : o));
        }
    };

    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 3000); // Refresh every 3 seconds
        return () => clearInterval(interval);
    }, [type]);

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    const heading = type === 'drink' ? 'Offene Bestellungen Getränke' : 'Offene Bestellungen Essen';

    return (
        <div className="dashboard">
            <NavBar />
            <h1>{heading}</h1>
            <div className="orders-grid">
                {orders.map((order, index) => (
                    <div key={index} className={`order-card ${order.completed ? 'completed' : ''}`}>
                        <h2>Tisch Nr: {order.tableNumber}</h2>
                        <div className="order-items">
                            {order.orderedItems
                                .filter(item => item.type === type)
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
                            Total: {(order.totalCost || order.total_price || 0).toFixed(2)}€
                        </div>

                        {!order.completed && (
                            <button
                                onClick={() => handleComplete(order.id)}
                                className={`complete-button ${order.completing ? 'working' : ''}`}
                                disabled={order.completing}
                            >
                                {order.completing ? '...' : 'Erledigt'}
                            </button>
                        )}

                        {order.completed && (
                            <div className="check-badge">✓</div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Dashboard;