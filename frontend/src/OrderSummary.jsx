import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

const OrderSummary = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { orderedItems = [] } = location.state || {};

    const [items, setItems] = useState(orderedItems);
    const [selectedItems, setSelectedItems] = useState(
        items.reduce((acc, item) => ({ ...acc, [item.id]: 0 }), {})
    );

    const increaseSelection = (id) => {
        setSelectedItems(prev => {
            const currentItem = items.find(item => item.id === id);
            if (currentItem) {
                const currentQuantity = prev[id];
                const maxQuantity = currentItem.quantity;
                if (currentQuantity < maxQuantity) {
                    return { ...prev, [id]: currentQuantity + 1 };
                }
            }
            return prev;
        });
    };

    const decreaseSelection = (id) => {
        setSelectedItems(prev => ({
            ...prev,
            [id]: prev[id] > 0 ? prev[id] - 1 : 0
        }));
    };

    const selectAll = () => {
        setSelectedItems(items.reduce((acc, item) => ({
            ...acc,
            [item.id]: item.quantity
        }), {}));
    };

    const totalSelectedCost = items.reduce((sum, item) => {
        return sum + (selectedItems[item.id] || 0) * item.price;
    }, 0);

    const handleCheckout = () => {
        // Update items first
        const updatedItems = items.map(item => {
            const selectedQuantity = selectedItems[item.id] || 0;
            return {
                ...item,
                quantity: item.quantity - selectedQuantity
            };
        });

        // Set the updated items
        setItems(updatedItems);

        // Reset selected items
        setSelectedItems(
            Object.keys(selectedItems).reduce((acc, id) => ({ ...acc, [id]: 0 }), {})
        );

        // Check if all quantities are zero
        const allZero = updatedItems.every(item => item.quantity === 0);
        
        // Navigate to main page if all quantities are zero
        if (allZero) {
            navigate('/');
        }
    };

    return (
        <div>
            <h2>Zusammenfassung</h2>
            <div>
                <ul style={{ padding: 0, listStyle: "none" }}>
                    {items.map(item => (
                        <li key={item.id} className="menu-item">
                            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                                <button onClick={() => decreaseSelection(item.id)}>-</button>
                                <span>{selectedItems[item.id] || 0} / {item.quantity}</span>
                                <button onClick={() => increaseSelection(item.id)}>+</button>
                                <span>{item.name} - {item.price.toFixed(2)}€</span>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>

            <button onClick={selectAll}>Alles auswählen</button>

            <h3>Gesamt: {totalSelectedCost.toFixed(2)}€</h3>

            <button onClick={handleCheckout}>Abrechnen</button>
            <button onClick={() => navigate("/")}>Zurück</button>
        </div>
    );
};

export default OrderSummary;
