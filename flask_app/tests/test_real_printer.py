"""
Pytest Suite for Real Hardware & Printer Connectivity Testing
"""
import pytest
import time
from config import Config
from services.Printer import Printer
from services.printer_service import PrinterService
from utils.printer_health_checker import check_printer_socket, PrinterHealthMonitor
from models import Order, OrderItem


def test_food_printer_socket_probe():
    """Test TCP socket connection to real food printer IP."""
    food_ip = Config.FOOD_PRINTER_IP
    res = check_printer_socket(food_ip, port=9100, timeout=2.0)
    print(f"\n[Speisen-Drucker Probe {food_ip}] Reachable: {res['reachable']}, Latency: {res['latency_ms']}ms, Error: {res['error']}")
    # Asserting response structure
    assert "reachable" in res
    assert "error" in res


def test_drinks_printer_socket_probe():
    """Test TCP socket connection to real drinks printer IP."""
    drinks_ip = Config.DRINKS_PRINTER_IP
    res = check_printer_socket(drinks_ip, port=9100, timeout=2.0)
    print(f"\n[Getränke-Drucker Probe {drinks_ip}] Reachable: {res['reachable']}, Latency: {res['latency_ms']}ms, Error: {res['error']}")
    assert "reachable" in res
    assert "error" in res


def test_health_monitor_check_all():
    """Test PrinterHealthMonitor check_all method."""
    monitor = PrinterHealthMonitor()
    status = monitor.check_all()
    
    assert "food_printer" in status
    assert "drinks_printer" in status
    assert "ip" in status["food_printer"]
    assert "reachable" in status["food_printer"]


def test_printer_service_availability():
    """Test PrinterService.are_printers_available() logic."""
    service = PrinterService()
    avail = service.are_printers_available()
    status = service.get_printer_status()
    print(f"\n[PrinterService Status] Overall Available: {avail}")
    print(f"[PrinterService Details] {status}")
    assert isinstance(avail, bool)


# @pytest.mark.skip(reason="Manual test run only: Sends an actual test ticket to the real physical printer")
def test_real_printer_physical_print():
    """
    Sends a test print ticket to the real printer if physically connected.
    Remove @pytest.mark.skip or run with pytest -k test_real_printer_physical_print to execute.
    """
    food_ip = Config.FOOD_PRINTER_IP
    printer = Printer(ip_address=food_ip, logo_path=None)

    assert printer.is_available(), f"Printer at {food_ip} is not reachable for test print"

    for i in range(0, 100):
        test_order = Order(
            table_number=999,
            id=i,
            items=[
                OrderItem(name="SYSTEM-TEST-FOOD", price=0.0, quantity=1, type="food", id=1),
                OrderItem(name="SYSTEM-TEST-DRINK", price=0.0, quantity=1, type="drink", id=i)
            ],
            comment="Drucker-Verbindungstest i.O."
        )


        success = printer.print_order(test_order, test_order.food_items)
        time.sleep(0.1)
        assert success is True, "Physical test print failed"




if __name__ == "__main__":
    test_real_printer_physical_print()