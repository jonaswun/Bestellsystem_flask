"""
Brute-force/concurrency and long-running soak tests for the printer layer.
Everything is mocked — no real printer connection is available here.

Soak tests are opt-in (set RUN_LONG_TESTS=1) so the normal test run stays
fast, mirroring the existing manual-only pattern used for the physical
printer test in test_real_printer.py.
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest

from services.printer_service import PrinterService
from utils.printer_health_checker import PrinterHealthMonitor
from models import Order, OrderItem

longrun = pytest.mark.skipif(
    os.getenv("RUN_LONG_TESTS") != "1",
    reason="Set RUN_LONG_TESTS=1 to run long-running soak tests",
)


def make_order(order_id):
    return Order(
        table_number=order_id % 20 + 1,
        id=order_id,
        items=[OrderItem(name="Item", price=1.0, quantity=1, type="food", id=1)],
    )


def make_service():
    service = PrinterService.__new__(PrinterService)
    service.config = {"mock": True}
    service.printer_food = MagicMock(is_available=MagicMock(return_value=True))
    service.printer_drinks = MagicMock(is_available=MagicMock(return_value=True))
    return service


def test_brute_force_sequential_print_order_calls():
    """Hammer print_order sequentially; nothing should raise and every call
    should succeed."""
    service = make_service()

    results = [service.print_order(make_order(i)) for i in range(2000)]

    assert all(results)
    assert service.printer_food.print_order.call_count == 2000


def test_brute_force_concurrent_print_order_calls():
    """Hammer print_order from many threads at once, mirroring the background
    order-processing thread potentially overlapping with retries."""
    service = make_service()

    with ThreadPoolExecutor(max_workers=32) as pool:
        results = list(pool.map(lambda i: service.print_order(make_order(i)), range(1000)))

    assert all(results)
    assert service.printer_food.print_order.call_count == 1000


def test_brute_force_are_printers_available_under_concurrency():
    service = make_service()

    with ThreadPoolExecutor(max_workers=32) as pool:
        results = list(pool.map(lambda _: service.are_printers_available(), range(1000)))

    assert all(results)


def test_brute_force_health_check_all_high_volume():
    """Repeatedly call check_all() with rapidly flapping reachability; the
    dedup-logging logic must not error or drift under high call volume."""
    monitor = PrinterHealthMonitor(food_ip="10.0.0.1", drinks_ip="10.0.0.2")
    call_count = 0

    def flapping_check(_ip, port=9100, timeout=1.5):
        nonlocal call_count
        call_count += 1
        reachable = call_count % 2 == 0
        return {
            "reachable": reachable,
            "latency_ms": 1.0 if reachable else None,
            "error": None if reachable else "down",
        }

    with patch("utils.printer_health_checker.check_printer_socket", side_effect=flapping_check):
        for _ in range(2000):
            status = monitor.check_all()
            assert "food_printer" in status and "drinks_printer" in status


@longrun
def test_soak_health_monitor_run_loop_many_ticks():
    """Soak test standing in for a long real-world monitoring run: many ticks
    with no sleep delay so the run stays fast and deterministic regardless of
    the tick count (SOAK_TICKS env var, default 20000)."""
    ticks = int(os.getenv("SOAK_TICKS", "20000"))
    monitor = PrinterHealthMonitor(food_ip="10.0.0.1", drinks_ip="10.0.0.2")

    with patch("utils.printer_health_checker.check_printer_socket") as mock_check:
        mock_check.return_value = {"reachable": True, "latency_ms": 1.0, "error": None}
        monitor.run_loop(interval_seconds=0, max_ticks=ticks)

    assert mock_check.call_count == ticks * 2


@longrun
def test_soak_print_order_over_extended_duration():
    """Soak test: print orders continuously for a fixed wall-clock duration
    to catch slow leaks/degradation over sustained use. Duration defaults to
    5s but can be raised for a real long-running pass, e.g.
    SOAK_DURATION_SECONDS=3600."""
    duration = float(os.getenv("SOAK_DURATION_SECONDS", "5"))
    service = make_service()
    deadline = time.time() + duration
    count = 0

    while time.time() < deadline:
        assert service.print_order(make_order(count))
        count += 1
        if count % 5000 == 0:
            print(f"soak progress: {count} orders printed")

    assert count > 0
