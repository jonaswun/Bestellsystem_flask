"""
Unit and regression tests for the printer layer (Printer, PrinterService,
MockPrinter, printer_health_checker), fully mocked — no real printer
connection is available in this environment.
"""
import socket
from unittest.mock import MagicMock, patch

from services.Printer import Printer
from services.printer_service import PrinterService
from services.MockPrinter import MockPrinter
from utils.printer_health_checker import check_printer_socket, PrinterHealthMonitor
from models import Order, OrderItem


def make_order(food=True, drink=True):
    items = []
    if food:
        items.append(OrderItem(name="Burger", price=8.5, quantity=1, type="food", id=1))
    if drink:
        items.append(OrderItem(name="Cola", price=3.0, quantity=2, type="drink", id=2))
    return Order(table_number=5, items=items, comment="")


# ---------------------------------------------------------------------------
# Printer.is_available()
# ---------------------------------------------------------------------------

def test_is_available_true_when_socket_connects():
    printer = Printer(ip_address="10.0.0.1")
    with patch("socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        assert printer.is_available() is True


def test_is_available_false_on_timeout():
    printer = Printer(ip_address="10.0.0.1")
    with patch("socket.create_connection", side_effect=socket.timeout):
        assert printer.is_available() is False


def test_is_available_false_on_os_error():
    printer = Printer(ip_address="10.0.0.1")
    with patch("socket.create_connection", side_effect=OSError("refused")):
        assert printer.is_available() is False


# ---------------------------------------------------------------------------
# Printer.print_order() — regression tests pinning current behavior
# ---------------------------------------------------------------------------

def test_print_order_uses_testing_branch_and_never_cuts():
    """Regression test: `testing` is hardcoded True in Printer.print_order, so
    it always takes the debug branch and never calls print_items()/cut(). If
    that hardcoding is intentionally removed, this test must be updated."""
    printer = Printer(ip_address="10.0.0.1")
    order = make_order()

    with patch("services.Printer.Network") as MockNetwork:
        mock_net = MockNetwork.return_value
        success = printer.print_order(order, order.food_items)

    assert success is True
    mock_net.open.assert_called_once()
    mock_net.close.assert_called_once()
    mock_net.cut.assert_not_called()


def test_print_order_with_no_items_returns_none():
    """Regression test documenting current behavior: an empty item list makes
    print_order return None rather than False."""
    printer = Printer(ip_address="10.0.0.1")
    order = make_order(food=False, drink=False)

    with patch("services.Printer.Network"):
        result = printer.print_order(order, [])

    assert result is None


# ---------------------------------------------------------------------------
# PrinterService
# ---------------------------------------------------------------------------

def make_service(mock=False):
    service = PrinterService.__new__(PrinterService)
    service.config = {"mock": mock}
    service.printer_food = MagicMock(is_available=MagicMock(return_value=True))
    service.printer_drinks = MagicMock(is_available=MagicMock(return_value=True))
    return service


def test_are_printers_available_requires_both():
    service = make_service()
    service.printer_drinks.is_available.return_value = False

    assert service.are_printers_available() is False

    service.printer_drinks.is_available.return_value = True
    assert service.are_printers_available() is True


def test_print_order_routes_items_to_correct_printers():
    service = make_service()
    order = make_order(food=True, drink=True)

    assert service.print_order(order) is True
    service.printer_food.print_order.assert_called_once_with(order, order.food_items)
    service.printer_drinks.print_order.assert_called_once_with(order, order.drink_items)


def test_print_order_skips_printer_with_no_matching_items():
    service = make_service()
    order = make_order(food=True, drink=False)

    service.print_order(order)

    service.printer_food.print_order.assert_called_once()
    service.printer_drinks.print_order.assert_not_called()


def test_print_order_returns_false_on_exception():
    service = make_service()
    service.printer_food.print_order.side_effect = RuntimeError("boom")

    assert service.print_order(make_order()) is False


def test_get_printer_status_reports_mock_type():
    service = make_service(mock=True)

    status = service.get_printer_status()

    assert status["food_printer"]["type"] == "mock"
    assert status["drinks_printer"]["type"] == "mock"


# ---------------------------------------------------------------------------
# MockPrinter
# ---------------------------------------------------------------------------

def test_mock_printer_is_always_available_and_noop():
    mock_printer = MockPrinter()

    assert mock_printer.is_available() is True
    mock_printer.print_logo("logo.png")
    mock_printer.print_items()
    mock_printer.print_order()


# ---------------------------------------------------------------------------
# printer_health_checker
# ---------------------------------------------------------------------------

def test_check_printer_socket_reachable():
    with patch("socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        res = check_printer_socket("10.0.0.1")

    assert res["reachable"] is True
    assert res["error"] is None


def test_check_printer_socket_timeout():
    with patch("socket.create_connection", side_effect=socket.timeout):
        res = check_printer_socket("10.0.0.1")

    assert res["reachable"] is False
    assert "Timeout" in res["error"]


def test_check_printer_socket_os_error():
    with patch("socket.create_connection", side_effect=OSError("Connection refused")):
        res = check_printer_socket("10.0.0.1")

    assert res["reachable"] is False
    assert res["error"] == "Connection refused"


def test_health_monitor_logs_only_on_status_change(caplog):
    monitor = PrinterHealthMonitor(food_ip="10.0.0.1", drinks_ip="10.0.0.2")
    caplog.set_level("INFO")

    with patch("utils.printer_health_checker.check_printer_socket") as mock_check:
        mock_check.return_value = {"reachable": True, "latency_ms": 1.0, "error": None}
        monitor.check_all()
        monitor.check_all()  # same status again -> must not log a second time

    change_logs = [r for r in caplog.records if "status changed" in r.message]
    assert len(change_logs) == 2  # one for food, one for drinks, only on first call
