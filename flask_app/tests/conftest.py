"""Shared fixtures for the order persistence/dashboard test suite."""
from unittest.mock import patch

import pytest

from config import Config
from services.order_logger import OrderLogger


@pytest.fixture
def db_path(tmp_path):
    """Path to a fresh, temporary SQLite file — never touches the real app DB."""
    return str(tmp_path / "test_orders.db")


@pytest.fixture
def order_logger(db_path):
    """A single OrderLogger bound to the temp DB."""
    return OrderLogger(db_path)


@pytest.fixture
def order_service_factory(db_path):
    """
    Factory for creating OrderService instances against the same temp DB, with
    the printer layer mocked out (always available, always prints successfully).

    Calling the factory more than once simulates an app restart: each instance
    is a brand-new OrderService (no shared in-memory state) pointed at the same
    on-disk DB, so it lets tests assert that dashboard state survives a restart.
    """
    with patch("services.printer_service.PrinterService.__init__", return_value=None), \
         patch("services.printer_service.PrinterService.are_printers_available", return_value=True), \
         patch("services.printer_service.PrinterService.print_order", return_value=True), \
         patch.object(Config, "DATABASE_PATH", db_path):
        from services.order_service import OrderService

        def make():
            return OrderService()

        yield make
