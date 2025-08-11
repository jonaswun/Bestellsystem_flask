import { useState, useEffect } from 'react';
import axios from 'axios';
import './Summary.css';

function Summary() {
    const [salesData, setSalesData] = useState({
        total_revenue: 0,
        total_orders: 0,
        average_order_value: 0,
        max_order_value: 0,
        min_order_value: 0
    });
    const [error, setError] = useState(null);

    const fetchSalesData = async () => {
        try {
            const response = await axios.get('/api/orders/summary');
            setSalesData(response.data);
        } catch (err) {
            setError('Failed to fetch sales data');
            console.error('Error:', err);
        }
    };

    useEffect(() => {
        fetchSalesData();
        const interval = setInterval(fetchSalesData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    return (
        <div className="summary-container">
            <h2>Verkauf Übersicht</h2>
            <div className="summary-grid">
                <div className="summary-card">
                    <h3>Gesamt</h3>
                    <p className="amount">€{salesData.total_revenue.toFixed(2)}</p>
                </div>
                <div className="summary-card">
                    <h3>Anzahl an Bestellungen</h3>
                    <p className="amount">{salesData.total_orders}</p>
                </div>
                <div className="summary-card">
                    <h3>Durchschnittlicher Bestellwert</h3>
                    <p className="amount">€{salesData.average_order_value.toFixed(2)}</p>
                </div>
                <div className="summary-card">
                    <h3>Höchster Bestellwert</h3>
                    <p className="amount">€{salesData.max_order_value.toFixed(2)}</p>
                </div>
                <div className="summary-card">
                    <h3>Niedrigster Bestellwert</h3>
                    <p className="amount">€{salesData.min_order_value.toFixed(2)}</p>
                </div>
            </div>
        </div>
    );
}

export default Summary;