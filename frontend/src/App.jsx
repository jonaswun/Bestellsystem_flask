import { useEffect, useState } from "react";
import axios from "axios";
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import OrderSummary from "./OrderSummary";
import Dashboard from "./components/Dashboard";
import Summary from "./components/Summary";
import InstallPrompt from "./components/InstallPrompt";
import FullscreenToggle from "./components/FullscreenToggle";

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
    const location = useLocation();
    const navigate = useNavigate();

    const restoredState = location.state || {};
    const [menu, setMenu] = useState({ Bier: [], drinks: [] });
    const [selectedCategory, setSelectedCategory] = useState("Bier");
    const [order, setOrder] = useState(restoredState.orderState || {});
    const [comment, setComment] = useState(restoredState.comment || "");
    const [tableNumber, setTableNumber] = useState(restoredState.tableNumber || "");

    // Fetch menu from backend
    useEffect(() => {
        axios.get('/api/menu')
            .then(response => {
                setMenu(response.data);
                // Ensure default selected category is valid
                const categories = Object.keys(response.data);
                if (categories.length > 0 && !categories.includes(selectedCategory)) {
                    setSelectedCategory(categories[0]);
                }
            })
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

    // Navigate to order summary with draft state (no HTTP POST yet)
    const goToSummary = () => {
        const orderedItems = Object.entries(order)
            .filter(([_, quantity]) => quantity > 0)
            .map(([id, quantity]) => {
                const item = findItemById(menu, id);
                return item ? { id: item.id, name: item.name, quantity, price: item.price, type: item.type } : null;
            })
            .filter(Boolean);

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

        // Navigate to summary without printing/saving yet
        navigate("/order-summary", {
            state: {
                orderedItems,
                totalCost,
                comment,
                tableNumber,
                orderState: order
            }
        });
    };

    return (
        <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <div className="category-buttons" style={{ flex: 1 }}>
                    {Object.keys(menu).map((category) => (
                        <button
                            key={category}
                            onClick={() => setSelectedCategory(category)}
                            style={{
                                fontWeight: selectedCategory === category ? "bold" : "normal",
                                backgroundColor: selectedCategory === category ? "#062c55ff" : "#2157a5",
                                color: "white",
                                fontSize: "14px",
                            }}
                        >
                            {category.charAt(0).toUpperCase() + category.slice(1)}
                        </button>
                    ))}
                </div>
                <FullscreenToggle />
            </div>

            <div>
                {(menu[selectedCategory] || []).map(item => (
                    <div key={item.id} className="menu-item">
                        <div style={{ display: "flex", alignItems: "center", gap: "20px", fontSize: "14px"}}>
                            <button onClick={() => decreaseQuantity(item.id)}>-</button>
                            <span>{order[item.id] || 0}</span>
                            <button onClick={() => increaseQuantity(item.id)}>+</button>
                            <span>{item.name} - {item.price.toFixed(2)}€</span>
                        </div>
                    </div>
                ))}
            </div>

            <div style={{ marginTop: "15px" }}>
                <label htmlFor="comment">Kommentar zur Bestellung:</label><br />
                <textarea
                    id="comment"
                    rows="2"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    style={{ fontSize: "14px" }}
                    placeholder="Optionaler Kommentar, z.B. Sonderwünsche..."
                />
            </div>

            <div style={{ marginTop: "15px" }}>
                <label htmlFor="tableNumber">Tischnummer:</label><br />
                <input
                    id="tableNumber"
                    type="number"
                    value={tableNumber}
                    onChange={(e) => {
                        const value = parseInt(e.target.value);
                        if (isNaN(value) || value <= 999) {
                            setTableNumber(e.target.value);
                        }
                    }}
                    placeholder="z.B. 5"
                    min="1"
                    max="999"
                />
            </div>

            <div style={{ marginTop: "5px" }}>
                <button
                    onClick={goToSummary}
                    style={{
                        padding: "12px 24px",
                        fontSize: "16px",
                        fontWeight: "bold",
                        backgroundColor: "#2e7d32",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    }}
                >
                    Zur Abrechnung / Vorschau ➔
                </button>
            </div>
        </div>
    );
}


function App() {
    return (
        <Router>
            <InstallPrompt />
            <Routes>
                <Route path="/" element={<MenuPage />} />
                <Route path="/order-summary" element={<OrderSummary />} />
                <Route path="/dashboard/food" element={<Dashboard type="food" />} />
                <Route path="/dashboard/drinks" element={<Dashboard type="drink" />} />
                <Route path="/summary" element={<Summary />} />
            </Routes>
        </Router>
    );
}

export default App;
