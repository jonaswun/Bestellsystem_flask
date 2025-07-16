"""Python Implementation for the Printer Setup"""
# Patch for missing DeviceNotFoundError
from escpos.exceptions import Error

class DeviceNotFoundError(Error):
    pass

import escpos.exceptions
escpos.exceptions.DeviceNotFoundError = DeviceNotFoundError

from escpos.printer import Network

class Printer:
    """
    Printer Class which enables printing of Order Data on a EPSON order printer
    """

    def __init__(self, ip_address:str, logo_path:str=None) -> None:
        self.printer_handle = Network(ip_address, profile='TM-T20II')
        assert self.printer_handle.is_online()
        self.logo_path = logo_path


    def is_available(self) -> bool:
        """
        Check if the printer is available and can accept print jobs.
        Returns True if printer is online and reachable.
        """
        try:
            # Try to create a test connection
            test_printer = Network(self.printer_handle.host, self.printer_handle.port, timeout=5)
            test_printer.open()
            test_printer.close()
            return True
        except:
            return False
    
    def print_logo(self, image_path:str) -> None:
        """
        Prints the given logo
        Use a .png format (others are possible to)
        Recommended image height is around 250px

        Parameters
            image_path:str      Path of the Image
        """
        self.printer_handle.image(image_path, impl='graphics', center=True)

    def print_items(self, items):
        self.printer_handle.set(align='left', bold=False, double_height=False)
        self.printer_handle.textln("")
        total_order_price = 0
        for item in items:
            total_item_price = item['price'] * item['quantity']
            total_order_price = total_order_price + total_item_price
            self.printer_handle.textln("{:<20} {:>7.2f}€".format(item['name'], total_item_price))
            if item['quantity'] > 1:
                self.printer_handle.textln("{:>10}x {:>7.2f}€".format(item['quantity'], item['price']))

        self.printer_handle.textln(f'Gesamt: {total_order_price:>20.2f}€')

    def print_order(self, table_number:int, items, comment:str=None):
        if items == []:
            return
        else:
            # print(f'Nr: {table_number} \t Items: {items}')
            return
            if self.logo_path is not None:
                self.print_logo(self.logo_path)
            self.printer_handle.textln(f'Tisch Nr. {table_number}')
            self.printer_handle.textln()
            self.print_items(items)
            if comment != '':
                self.printer_handle.textln()
                self.printer_handle.textln(f'Kommentar:\n{comment}')
            self.printer_handle.cut()

    def __del__(self) -> None:
        pass
