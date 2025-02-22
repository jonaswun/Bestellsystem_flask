import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

const OrderSummary = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { orderedItems = [] } = location.state || {};

    // State to track selected items for payment
    const [selectedItems, setSelectedItems] = useState(
        orderedItems.reduce((acc, item) => ({ ...acc, [item.id]: 0 }), {})
    );

    // Increase selected quantity
    const increaseSelection = (id) => {
        setSelectedItems(prev => ({ ...prev, [id]: prev[id] + 1 }));
    };

    // Decrease selected quantity
    const decreaseSelection = (id) => {
        setSelectedItems(prev => ({
            ...prev,
            [id]: prev[id] > 0 ? prev[id] - 1 : 0
        }));
    };

    // Select all items
    const selectAll = () => {
        setSelectedItems(orderedItems.reduce((acc, item) => ({
            ...acc,
            [item.id]: item.quantity
        }), {}));
    };

    // Calculate total cost of selected items
    const totalSelectedCost = orderedItems.reduce((sum, item) => {
        return sum + (selectedItems[item.id] || 0) * item.price;
    }, 0);

    return (
        <div>
            <h2>Zusammenfassung</h2>
            <ul>
                {orderedItems.map(item => (
                    <li key={item.id} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <button onClick={() => decreaseSelection(item.id)}>-</button>
                        <span>{selectedItems[item.id] || 0} / {item.quantity}</span>
                        <button onClick={() => increaseSelection(item.id)}>+</button>
                        <span>{item.name} - ${item.price.toFixed(2)}</span>
                    </li>
                ))}
            </ul>

            <button onClick={selectAll}>Alles auswählen</button>

            <h3>Gesamt: ${totalSelectedCost.toFixed(2)}</h3>

            <button onClick={() => navigate("/")}>Zurück</button>
        </div>
    );
};

export default OrderSummary;
