import logging

log = logging.getLogger(__name__)


class MockPrinter:
    def __init__(self, *args, **kwargs):
        pass

    def print_logo(self, *args, **kwargs):
        log.info("Mock: Printing logo")

    def print_items(self, *args, **kwargs):
        log.info("Mock: Printing items")

    def print_order(self, *args, **kwargs):
        log.info("Mock: Printing order")

    def is_available(self) -> bool:
        """
        Mock method to simulate printer availability.
        Always returns True for testing purposes.
        """
        return True