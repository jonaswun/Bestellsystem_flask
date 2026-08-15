"""
Unit tests for OrderLogger — the SQLite persistence layer.

Covers order save/retrieve, status transitions, the get_unprocessed_orders()/
get_pending_orders() dashboard queries, and the restart-durability regression
that motivated moving dashboard state from memory into the database.
"""
from models import Order, OrderItem


def make_order(table_number=1, item_type="food"):
    return Order(
        table_number=table_number,
        items=[OrderItem(name="Burger", price=8.5, quantity=2, type=item_type, id=1)],
        comment="no onions",
    )


def test_save_and_get_order(order_logger):
    order_id = order_logger.save_order(make_order())

    result = order_logger.get_order(order_id)

    assert result is not None
    assert result["order"]["table_number"] == 1
    assert result["order"]["status"] == "pending"
    assert len(result["items"]) == 1
    assert result["items"][0]["item_name"] == "Burger"


def test_get_pending_orders_only_returns_pending(order_logger):
    pending_id = order_logger.save_order(make_order())
    printed_id = order_logger.save_order(make_order())
    order_logger.update_order_status(printed_id, "printed")

    pending = order_logger.get_pending_orders()

    assert [o.id for o in pending] == [pending_id]


def test_get_unprocessed_orders_excludes_completed(order_logger):
    """Completing an order (sets status + both flags) must remove it from the dashboard."""
    open_id = order_logger.save_order(make_order())
    completed_id = order_logger.save_order(make_order())
    order_logger.update_order_status(completed_id, "completed")

    unprocessed = order_logger.get_unprocessed_orders()

    ids = [o.id for o in unprocessed]
    assert open_id in ids
    assert completed_id not in ids


def test_get_unprocessed_orders_filters_by_item_type(order_logger):
    """Food orders must only appear in the food dashboard and vice versa."""
    food_id = order_logger.save_order(make_order(item_type="food"))
    drink_id = order_logger.save_order(make_order(item_type="drink"))

    food_orders = order_logger.get_unprocessed_orders(item_type="food")
    drink_orders = order_logger.get_unprocessed_orders(item_type="drink")

    assert [o.id for o in food_orders] == [food_id]
    assert [o.id for o in drink_orders] == [drink_id]


def test_get_unprocessed_orders_excludes_after_set_processed(order_logger):
    """After set_processed for food, the order must vanish from the food dashboard
    but still appear in the drink dashboard (if it has drink items)."""
    from models import OrderItem
    order = Order(
        table_number=2,
        items=[
            OrderItem(name="Burger", price=8.5, quantity=1, type="food", id=1),
            OrderItem(name="Cola", price=2.5, quantity=1, type="drink", id=2),
        ],
    )
    order_id = order_logger.save_order(order)
    order_logger.update_type_processed_status(order_id, "food")

    food_orders = order_logger.get_unprocessed_orders(item_type="food")
    drink_orders = order_logger.get_unprocessed_orders(item_type="drink")

    assert order_id not in [o.id for o in food_orders]
    assert order_id in [o.id for o in drink_orders]


def test_update_order_status_transitions(order_logger):
    order_id = order_logger.save_order(make_order())

    assert order_logger.update_order_status(order_id, "printed") is True
    assert order_logger.get_order(order_id)["order"]["status"] == "printed"

    assert order_logger.update_order_status(order_id, "completed") is True
    assert order_logger.get_order(order_id)["order"]["status"] == "completed"


def test_update_order_status_returns_false_for_unknown_id(order_logger):
    assert order_logger.update_order_status(9999, "completed") is False


def test_completed_status_persists_across_new_logger_instance(order_logger, db_path):
    """Regression test: completion must survive a process restart (new instance,
    same DB file), which is the bug Phase 1/2 fixed — completion used to only
    live in an in-memory list that was lost on restart."""
    from services.order_logger import OrderLogger

    order_id = order_logger.save_order(make_order())
    order_logger.update_order_status(order_id, "completed")

    restarted_logger = OrderLogger(db_path)

    assert [o.id for o in restarted_logger.get_unprocessed_orders()] == []
    assert restarted_logger.get_order(order_id)["order"]["status"] == "completed"
