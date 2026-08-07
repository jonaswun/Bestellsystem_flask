"""
Unit tests for OrderLogger — the SQLite persistence layer.

Covers order save/retrieve, status transitions, the get_active_orders()/
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


def test_get_active_orders_excludes_completed(order_logger):
    open_id = order_logger.save_order(make_order())
    completed_id = order_logger.save_order(make_order())
    order_logger.update_order_status(completed_id, "completed")

    active = order_logger.get_active_orders()

    assert [o.id for o in active] == [open_id]


def test_get_active_orders_filters_by_item_type(order_logger):
    food_id = order_logger.save_order(make_order(item_type="food"))
    drink_id = order_logger.save_order(make_order(item_type="drink"))

    food_orders = order_logger.get_active_orders(item_type="food")
    drink_orders = order_logger.get_active_orders(item_type="drink")

    assert [o.id for o in food_orders] == [food_id]
    assert [o.id for o in drink_orders] == [drink_id]


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

    assert [o.id for o in restarted_logger.get_active_orders()] == []
    assert restarted_logger.get_order(order_id)["order"]["status"] == "completed"
