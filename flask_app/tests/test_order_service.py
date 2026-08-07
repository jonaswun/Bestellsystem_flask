"""
Integration tests for OrderService's order lifecycle and dashboard state.

These exercise process_order -> background print worker -> get_dashboard_orders
-> complete_order end-to-end against a real (temp file) SQLite DB, with only the
printer hardware layer mocked out. They also codify the "restart" regression
scenario that was previously verified manually: a completed order must not
reappear on the dashboard when a fresh OrderService instance is created.
"""
import time

from models import Order, OrderItem


def wait_until(condition, timeout=2.0, interval=0.05):
    """Poll `condition()` until it returns truthy or the timeout elapses."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return False


def make_order(table_number=7, item_type="food"):
    return Order(
        table_number=table_number,
        items=[OrderItem(name="Burger", price=8.5, quantity=2, type=item_type, id=1)],
        comment="no onions",
    )


def test_process_order_persists_and_gets_printed(order_service_factory):
    service = order_service_factory()

    order_id = service.process_order(make_order())

    assert order_id is not None
    assert wait_until(
        lambda: service.order_logger.get_order(order_id)["order"]["status"] == "printed"
    )


def test_dashboard_shows_active_order(order_service_factory):
    service = order_service_factory()
    order_id = service.process_order(make_order())

    dashboard = service.get_dashboard_orders({"key": "type", "value": "food"})

    assert order_id in [o["id"] for o in dashboard]


def test_complete_order_removes_it_from_dashboard(order_service_factory):
    service = order_service_factory()
    order_id = service.process_order(make_order())
    wait_until(lambda: service.order_logger.get_order(order_id)["order"]["status"] == "printed")

    completed = service.complete_order(order_id)
    dashboard = service.get_dashboard_orders({"key": "type", "value": "food"})

    assert completed is True
    assert order_id not in [o["id"] for o in dashboard]


def test_complete_order_returns_false_for_unknown_id(order_service_factory):
    service = order_service_factory()

    assert service.complete_order(9999) is False


def test_dashboard_state_survives_simulated_restart(order_service_factory):
    """Regression test for the original bug: completing an order used to only
    update an in-memory list, so restarting the app (new OrderService instance)
    would resurrect completed orders as pending/active again."""
    service = order_service_factory()
    order_id = service.process_order(make_order())
    wait_until(lambda: service.order_logger.get_order(order_id)["order"]["status"] == "printed")
    service.complete_order(order_id)

    restarted_service = order_service_factory()
    dashboard = restarted_service.get_dashboard_orders({"key": "type", "value": "food"})

    assert order_id not in [o["id"] for o in dashboard]
