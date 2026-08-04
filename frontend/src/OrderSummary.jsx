import { useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import axios from "axios";

const OrderSummary = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const {
        orderedItems = [],
        totalCost = 0,
        comment = "",
        tableNumber = "",
        orderState = {}
    } = location.state || {};

    const [isSubmitted, setIsSubmitted] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [items, setItems] = useState(orderedItems);
    const [printerStatus, setPrinterStatus] = useState(null);
    const [selectedItems, setSelectedItems] = useState(
        orderedItems.reduce((acc, item) => ({ ...acc, [item.id]: 0 }), {})
    );

    // Fetch printer status
    const fetchPrinterStatus = async () => {
        try {
            const response = await axios.get('/api/printer/status');
            setPrinterStatus(response.data.printer_status);
        } catch (error) {
            console.error("Fehler beim Abrufen des Druckerstatus:", error);
        }
    };

    useEffect(() => {
        fetchPrinterStatus();
        const interval = setInterval(fetchPrinterStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    // Send order to backend and trigger printer queue
    const handleSendOrder = async () => {
        setIsSubmitting(true);
        const currentTotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

        try {
            const response = await fetch('/api/order', {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    orderedItems: items,
                    totalCost: currentTotal,
                    comment,
                    tableNumber
                }),
            });

            if (!response.ok) {
                throw new Error("Fehler beim Senden der Bestellung");
            }

            const data = await response.json();
            console.log("Order response:", data);
            setIsSubmitted(true);
        } catch (error) {
            console.error("Error placing order:", error);
            alert("Fehler beim Abschicken der Bestellung an den Drucker.");
        } finally {
            setIsSubmitting(false);
        }
    };

    // Return to menu page to edit order
    const handleEditOrder = () => {
        navigate("/", {
            state: {
                tableNumber,
                comment,
                orderState
            }
        });
    };

    // Cancel order completely
    const handleCancelOrder = () => {
        if (window.confirm("Bestellung wirklich abbrechen und verworfen?")) {
            navigate("/");
        }
    };

    // Checkout selection helpers
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
        const updatedItems = items.map(item => {
            const selectedQuantity = selectedItems[item.id] || 0;
            return {
                ...item,
                quantity: item.quantity - selectedQuantity
            };
        });

        setItems(updatedItems);
        setSelectedItems(
            Object.keys(selectedItems).reduce((acc, id) => ({ ...acc, [id]: 0 }), {})
        );

        const allZero = updatedItems.every(item => item.quantity === 0);
        if (allZero) {
            navigate('/');
        }
    };

    return (
        <div style={{ maxWidth: "600px", margin: "0 auto", padding: "16px" }}>
            {/* Header with Printer Status */}
            <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderBottom: "2px solid #ccc",
                paddingBottom: "12px",
                marginBottom: "16px"
            }}>
                <h2 style={{ margin: 0 }}>
                    {isSubmitted ? `Abrechnung — Tisch ${tableNumber}` : `Bestellung prüfen — Tisch ${tableNumber}`}
                </h2>
                
                {printerStatus && (
                    <div style={{ display: "flex", gap: "10px", fontSize: "14px" }}>
                        <span title={printerStatus.food_printer?.available ? "Küche: Bereit" : "Küche: Offline"}>
                            {printerStatus.food_printer?.available ? "🟢" : "🔴"} Küche
                        </span>
                        <span title={printerStatus.drinks_printer?.available ? "Theke: Bereit" : "Theke: Offline"}>
                            {printerStatus.drinks_printer?.available ? "🟢" : "🔴"} Theke
                        </span>
                    </div>
                )}
            </div>

            {/* If not submitted yet: Draft overview & Confirm/Print */}
            {!isSubmitted ? (
                <div>
                    <div style={{ backgroundColor: "#f5f5f5", padding: "12px", borderRadius: "8px", marginBottom: "16px" }}>
                        <p style={{ margin: "4px 0" }}><strong>Tischnummer:</strong> {tableNumber}</p>
                        {comment && <p style={{ margin: "4px 0" }}><strong>Kommentar:</strong> {comment}</p>}
                    </div>

                    <h3>Positionen:</h3>
                    <ul style={{ padding: 0, listStyle: "none" }}>
                        {items.map(item => (
                            <li key={item.id} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #eee" }}>
                                <span>{item.quantity}x {item.name} ({item.type === 'food' ? 'Küche' : 'Bar'})</span>
                                <strong>{(item.price * item.quantity).toFixed(2)}€</strong>
                            </li>
                        ))}
                    </ul>

                    <h3 style={{ textAlign: "right", marginTop: "16px" }}>
                        Gesamtbetrag: {items.reduce((sum, item) => sum + item.price * item.quantity, 0).toFixed(2)}€
                    </h3>

                    {/* Action buttons before print */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "24px" }}>
                        <button
                            onClick={handleSendOrder}
                            disabled={isSubmitting}
                            style={{
                                padding: "14px",
                                fontSize: "16px",
                                fontWeight: "bold",
                                backgroundColor: "#2e7d32",
                                color: "white",
                                border: "none",
                                borderRadius: "6px",
                                cursor: isSubmitting ? "not-allowed" : "pointer"
                            }}
                        >
                            {isSubmitting ? "Wird an Drucker gesendet..." : "🖨️ Abschicken & Drucken"}
                        </button>

                        <div style={{ display: "flex", gap: "10px" }}>
                            <button
                                onClick={handleEditOrder}
                                style={{
                                    flex: 1,
                                    padding: "10px",
                                    fontSize: "14px",
                                    backgroundColor: "#1976d2",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "6px",
                                    cursor: "pointer"
                                }}
                            >
                                ✏️ Bearbeiten / Zurück
                            </button>

                            <button
                                onClick={handleCancelOrder}
                                style={{
                                    flex: 1,
                                    padding: "10px",
                                    fontSize: "14px",
                                    backgroundColor: "#d32f2f",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "6px",
                                    cursor: "pointer"
                                }}
                            >
                                🗑️ Stornieren
                            </button>
                        </div>
                    </div>
                </div>
            ) : (
                /* Settlement / Item Splitting view after submission */
                <div>
                    <div style={{ backgroundColor: "#e8f5e9", color: "#2e7d32", padding: "10px", borderRadius: "6px", marginBottom: "16px" }}>
                        ✅ Bestellung gedruckt & an Küche/Bar übermittelt. Positionen jetzt abrechnen:
                    </div>

                    <ul style={{ padding: 0, listStyle: "none" }}>
                        {items
                            .filter(item => item.quantity > 0)
                            .map(item => (
                                <li key={item.id} className="menu-item" style={{ marginBottom: "8px" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                                        <button onClick={() => decreaseSelection(item.id)}>-</button>
                                        <span>{selectedItems[item.id] || 0} / {item.quantity}</span>
                                        <button onClick={() => increaseSelection(item.id)}>+</button>
                                        <span>{item.name} - {item.price.toFixed(2)}€</span>
                                    </div>
                                </li>
                            ))}
                    </ul>

                    <div style={{ display: "flex", gap: "10px", margin: "16px 0" }}>
                        <button onClick={selectAll}>Alles auswählen</button>
                    </div>

                    <h3>Ausgewählt: {totalSelectedCost.toFixed(2)}€</h3>

                    <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
                        <button
                            onClick={handleCheckout}
                            disabled={totalSelectedCost === 0}
                            style={{
                                padding: "12px 20px",
                                fontSize: "16px",
                                backgroundColor: totalSelectedCost > 0 ? "#2e7d32" : "#ccc",
                                color: "white",
                                border: "none",
                                borderRadius: "6px",
                                cursor: totalSelectedCost > 0 ? "pointer" : "not-allowed"
                            }}
                        >
                            Positionen abrechnen ({totalSelectedCost.toFixed(2)}€)
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default OrderSummary;
