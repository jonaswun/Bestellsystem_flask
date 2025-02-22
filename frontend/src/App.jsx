import { useEffect, useState } from "react";
import axios from "axios";

function App() {
    const [menu, setMenu] = useState({ food: [], drinks: [] });
    const [selectedCategory, setSelectedCategory] = useState("food");
    const [order, setOrder] = useState({});

    // Fetch menu from backend
    useEffect(() => {
        axios.get("http://localhost:5000/menu")
            .then(response => setMenu(response.data))
            .catch(error => console.error("Error fetching menu:", error));
    }, []);

    // Function to increase quantity
    const increaseQuantity = (id) => {
        setOrder(prev => ({ ...prev, [id]: (prev[id] || 0) + 1 }));
    };

    // Function to decrease quantity
    const decreaseQuantity = (id) => {
        setOrder(prev => {
            const updated = { ...prev };
            if (updated[id] > 0) updated[id] -= 1;
            return updated;
        });
    };

    // Place order
    const placeOrder = () => {
        const orderedItems = Object.entries(order)
            .filter(([_, quantity]) => quantity > 0)
            .map(([id, quantity]) => ({
                id: parseInt(id),
                name: menu[selectedCategory].find(item => item.id === parseInt(id)).name,
                quantity
            }));

        axios.post("http://localhost:5000/order", { order: orderedItems })
            .then(response => alert(response.data.message))
            .catch(error => console.error("Order failed:", error));
    };

    return (
        <div>
            <h1>Menu</h1>

            {/* Category Selection */}
            <div>
                <button onClick={() => setSelectedCategory("food")}>Food</button>
                <button onClick={() => setSelectedCategory("drinks")}>Drinks</button>
            </div>

            {/* Display menu items */}
            <div>
                {menu[selectedCategory].map(item => (
                    <div key={item.id} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <button onClick={() => decreaseQuantity(item.id)}>-</button>
                        <span>{order[item.id] || 0}</span>
                        <button onClick={() => increaseQuantity(item.id)}>+</button>
                        <span>{item.name} - ${item.price.toFixed(2)}</span>
                    </div>
                ))}
            </div>

            <button onClick={placeOrder}>Place Order</button>
        </div>
    );
}

export default App;
