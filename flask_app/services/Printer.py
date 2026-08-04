"""Python Implementation for the Printer Setup"""
# Patch for missing DeviceNotFoundError
from datetime import datetime
# pyrefly: ignore [missing-import]
from escpos.exceptions import Error
import socket
import logging
from models import Order

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
        self.ip_address = ip_address
        # self.printer_handle = Network(ip_address, profile='TM-T20II', timeout=3.0)
        self.logo_path = logo_path       
            
    def is_available(self) -> bool:
        """
        Check if the printer is available and can accept print jobs.
        Returns True if printer is online and reachable.
        """
        try:
            with socket.create_connection((self.ip_address, 9100), 1.0):
                return True
        except (socket.timeout, OSError):
            return False

    def print_logo(self, image_path:str) -> None:
        """
        Prints the given logo
        Use a .png format (others are possible to)
        Recommended image height is around 250px

        Parameters
            image_path:str      Path of the Image
        """
        printer = Network(self.ip_address, profile='TM-T20II', timeout=3.0)
        printer.open()
        printer.image(image_path, impl='graphics', center=True)
        printer.close()

    def print_items(self, printer, items):

        printer.set(align='left', bold=False, double_height=False)
        printer.textln("")
        total_order_price = 0
        for item in items:
            name = item.name if hasattr(item, 'name') else item['name']
            price = item.price if hasattr(item, 'price') else item['price']
            quantity = item.quantity if hasattr(item, 'quantity') else item['quantity']

            total_item_price = price * quantity
            total_order_price += total_item_price
            printer.textln("{:<20} {:>7.2f}€".format(name, total_item_price))
            if quantity > 1:
                printer.textln("{:>10}x {:>7.2f}€".format(quantity, price))

        printer.textln(f'Gesamt: {total_order_price:>20.2f}€')


    def print_order(self, order:Order, items):
        table_number = order.table_number
        id = order.id
        items = items
        comment = order.comment
        timestamp = order.timestamp
        testing = True
        printer = Network(self.ip_address, profile='TM-T20II', timeout=3.0)
        printer.open()


        if items == []:
            return
        elif testing is True:
            print(f"Bestellnummer: {id}")
            print(f"Tisch Nr. {table_number}")
            print(f"Kommentar: {comment}")
            print(f"Bestelldatum: {timestamp}")
            # formatted_time = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            
            printer.textln("{} {} {} {} {} {}".format("ID:", id, "Time:", timestamp, "TABLE:", table_number))
        else:
            if self.logo_path is not None:
                self.print_logo(self.logo_path)
            if timestamp is not None:
                formatted_time = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
                printer.textln(f'Bestelldatum: {formatted_time}')
            printer.textln(f'Tisch Nr. {table_number}')
            printer.textln()
            self.print_items(printer, items)
            if comment != '':
                printer.textln()
                printer.textln(f'Kommentar:\n{comment}')

            printer.cut()
        printer.close()

        return True

    def __del__(self) -> None:
        pass
