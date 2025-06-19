import { useEffect, useState } from "react";
import axios from "axios";
import { BrowserRouter as Router, Routes, Route, useNavigate } from "react-router-dom";
import OrderSummary from "./OrderSummary";

function findItemById(menu, id) {
    for (const category of Object.keys(menu)) { // Iterate over "food" and "drinks"
        for (const item of menu[category]) { // Iterate over items in each category
            if (item.id === Number(id)) {
                return item; // Return the found item
            }
        }
    }
    return null; // Return null if item not found
}

function MenuPage() {
    const [menu, setMenu] = useState({ Bier: [], drinks: [] });
    const [selectedCategory, setSelectedCategory] = useState("Bier");
    const [order, setOrder] = useState({});
    const navigate = useNavigate();
    const [comment, setComment] = useState("");
    const [tableNumber, setTableNumber] = useState("");

    // Fetch menu from backend
    useEffect(() => {
        axios.get("http://192.168.0.26:5000/menu")
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

    // Place order and navigate to summary
    const placeOrder = async () => {
        const orderedItems = Object.entries(order)
            .filter(([_, quantity]) => quantity > 0)
            .map(([id, quantity]) => {
                const item = findItemById(menu, id);
                return { id: item.id, name: item.name, quantity, price: item.price };
            });

        const totalCost = orderedItems.reduce((sum, item) => sum + item.price * item.quantity, 0);

        // 🚨 SAFETY CHECKS
        if (tableNumber.trim() === "") {
            alert("Bitte geben Sie eine Tischnummer ein.");
            return;
        }

        if (orderedItems.length === 0) {
            alert("Bitte wählen Sie mindestens ein Produkt aus.");
            return;
        }

        try {
            const response = await fetch("http://192.168.0.26:5000/order", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ orderedItems, totalCost, comment, tableNumber }),
            });

            if (!response.ok) {
                throw new Error("Failed to place order");
            }

            const data = await response.json();
            console.log("Order response:", data);

            navigate("/order-summary", { state: { orderedItems, totalCost, comment, tableNumber } });
        } catch (error) {
            console.error("Error placing order:", error);
            alert("Fehler beim Senden der Bestellung.");
        }
    };

    return (
        <div>
            {/* <img src="/Logos_Rucksackberger_klein.jpg" alt="Banner" className="banner" /> */}
            <h1>Menü</h1>

            <div className="category-buttons">
                {Object.keys(menu).map((category) => (
                    <button
                        key={category}
                        onClick={() => setSelectedCategory(category)}
                        style={{
                            fontWeight: selectedCategory === category ? "bold" : "normal"
                        }}
                    >
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                    </button>
                ))}
            </div>

            <div>
                {menu[selectedCategory].map(item => (
                    <div key={item.id} className="menu-item">
                        <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
                            <button onClick={() => decreaseQuantity(item.id)}>-</button>
                            <span>{order[item.id] || 0}</span>
                            <button onClick={() => increaseQuantity(item.id)}>+</button>
                             <span>{item.name} - {item.price.toFixed(2)}€</span>
                        </div>
                    </div>
                ))}
            </div>

            <div>
                <label htmlFor="comment">Kommentar zur Bestellung:</label><br />
                <textarea
                    id="comment"
                    rows="2"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Optionaler Kommentar, z.B. Sonderwünsche..."
                />
            </div>

            <div>
                <label htmlFor="tableNumber">Tischnummer:</label><br />
                <input
                    id="tableNumber"
                    type="number"
                    value={tableNumber}
                    onChange={(e) => setTableNumber(e.target.value)}
                    placeholder="z.B. 5"
                    min="1"
                />
            </div>

            <div>
                <button onClick={placeOrder}>Bestellen</button>
            </div>
        </div>
    );
}

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<MenuPage />} />
                <Route path="/order-summary" element={<OrderSummary />} />
            </Routes>
        </Router>
    );
}

export default App;
