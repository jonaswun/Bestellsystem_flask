class MockPrinter:
    def __init__(self, *args, **kwargs):
        pass

    def print_logo(self, *args, **kwargs):
        print("Mock: Printing logo")

    def print_items(self, *args, **kwargs):
        print("Mock: Printing items")

    def print_order(self, *args, **kwargs):
        print("Mock: Printing order")

    def is_available(self) -> bool:
        """
        Mock method to simulate printer availability.
        Always returns True for testing purposes.
        """
        return True