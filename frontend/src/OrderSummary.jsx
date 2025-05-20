import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

const OrderSummary = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { orderedItems = [] } = location.state || {};

    const [items, setItems] = useState(orderedItems);


    // State to track selected items for payment
    const [selectedItems, setSelectedItems] = useState(
        items.reduce((acc, item) => ({ ...acc, [item.id]: 0 }), {})
    );

    // Increase selected quantity
    const increaseSelection = (id) => {
        setSelectedItems(prev => {
            const currentItem = items.find(item => item.id === id);
            if (currentItem) {
                const currentQuantity = prev[id];
                const maxQuantity = currentItem.quantity; // Max quantity of item

                if (currentQuantity < maxQuantity) {
                    return { ...prev, [id]: currentQuantity + 1 };
                }
            }
            return prev;
        });
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
        setSelectedItems(items.reduce((acc, item) => ({
            ...acc,
            [item.id]: item.quantity
        }), {}));
    };

    // Calculate total cost of selected items
    const totalSelectedCost = items.reduce((sum, item) => {
        return sum + (selectedItems[item.id] || 0) * item.price;
    }, 0);

    // Handle "Abrechnen" (Checkout) by reducing the available quantities of the ordered items
    const handleCheckout = () => {
        setItems(prevItems => 
          prevItems.map(item => {
            const selectedQuantity = selectedItems[item.id] || 0;
            return {
              ...item,
              quantity: item.quantity - selectedQuantity
            };
          })
        );

        // Reset selected items
        setSelectedItems(prev => 
          Object.keys(prev).reduce((acc, id) => ({ ...acc, [id]: 0 }), {})
        );
      };
    return (
        <div>
            <h2>Zusammenfassung</h2>
            <ul>
                {items.map(item => (
                    <li key={item.id} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <button onClick={() => decreaseSelection(item.id)}>-</button>
                        <span>{selectedItems[item.id] || 0} / {item.quantity}</span>
                        <button onClick={() => increaseSelection(item.id)}>+</button>
                        <span>{item.name} - {item.price.toFixed(2)}€</span>
                    </li>
                ))}
            </ul>

            <button onClick={selectAll}>Alles auswählen</button>

            <h3>Gesamt: ${totalSelectedCost.toFixed(2)}</h3>

            <button onClick={handleCheckout}>Abrechnen</button>
            <button onClick={() => navigate("/")}>Zurück</button>
        </div>
    );
};

export default OrderSummary;
