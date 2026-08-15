"""
Order and OrderItem dataclasses for structured order data management.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


@dataclass
class OrderItem:
    """Represents an item in an order"""
    name: str
    price: float
    quantity: int = 1
    type: str = "food"  # "food" or "drink"
    id: Optional[int] = None

    def __post_init__(self):
        self.price = float(self.price)
        self.quantity = int(self.quantity)

    @property
    def total_price(self) -> float:
        return round(self.price * self.quantity, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
            "type": self.type,
            "total_price": self.total_price,
        }

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], "OrderItem"]) -> "OrderItem":
        if isinstance(data, cls):
            return data
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            price=float(data.get("price", 0.0)),
            quantity=int(data.get("quantity", 1)),
            type=data.get("type", "food"),
        )

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        if key == "total_price":
            return self.total_price
        raise KeyError(f"OrderItem has no attribute '{key}'")

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class Order:
    """Represents a complete order with table number, items, comment, and status"""
    table_number: int
    items: List[OrderItem] = field(default_factory=list)
    comment: str = ""
    timestamp: Optional[int] = None
    id: Optional[int] = None
    status: str = "pending"
    food_processed: bool = False
    drink_processed: bool = False
    created_at: Optional[str] = None
    user_agent: Optional[str] = None

    def __post_init__(self):
        try:
            self.table_number = int(self.table_number)
        except (ValueError, TypeError):
            self.table_number = 0

        # Convert dict items to OrderItem dataclass instances if needed
        self.items = [
            item if isinstance(item, OrderItem) else OrderItem.from_dict(item)
            for item in self.items
        ]

        if self.timestamp is None:
            self.timestamp = int(datetime.now().timestamp())

    @property
    def total_price(self) -> float:
        return round(sum(item.total_price for item in self.items), 2)

    @property
    def food_items(self) -> List[OrderItem]:
        return [item for item in self.items if item.type == "food"]

    @property
    def drink_items(self) -> List[OrderItem]:
        return [item for item in self.items if item.type == "drink"]

    def has_item_type(self, item_type: str) -> bool:
        return any(item.type == item_type for item in self.items)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Order to dict for JSON responses & database methods"""
        return {
            "id": self.id,
            "order_id": self.id,
            "tableNumber": str(self.table_number),
            "table_number": self.table_number,
            "orderedItems": [item.to_dict() for item in self.items],
            "items": [item.to_dict() for item in self.items],
            "comment": self.comment,
            "timestamp": self.timestamp,
            "totalCost": self.total_price,
            "total_price": self.total_price,
            "status": self.status,
            "food_processed": self.food_processed,
            "drink_processed": self.drink_processed,
            "created_at": self.created_at,
            "user_agent": self.user_agent,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        raw_items = data.get("orderedItems") or data.get("items") or []
        items = [
            item if isinstance(item, OrderItem) else OrderItem.from_dict(item)
            for item in raw_items
        ]

        table_num = data.get("tableNumber") or data.get("table_number") or 0

        return cls(
            id=data.get("id") or data.get("order_id"),
            table_number=table_num,
            items=items,
            comment=data.get("comment", ""),
            timestamp=data.get("timestamp"),
            status=data.get("status", "pending"),
            food_processed=bool(data.get("food_processed", False)),
            drink_processed=bool(data.get("drink_processed", False)),
            created_at=data.get("created_at"),
            user_agent=data.get("user_agent"),
        )

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access for backwards compatibility"""
        if hasattr(self, key):
            return getattr(self, key)
        mapping = {
            "tableNumber": self.table_number,
            "orderedItems": [item.to_dict() for item in self.items],
            "totalCost": self.total_price,
            "total_price": self.total_price,
        }
        if key in mapping:
            return mapping[key]
        raise KeyError(f"Order has no attribute '{key}'")

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default
