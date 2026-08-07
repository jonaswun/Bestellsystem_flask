"""
Printer Health Checker & Monitor

Cyclically checks printer connectivity for both food and drink printers.
Supports testing real hardware over TCP port 9100.
"""
import time
import socket
import logging
import argparse
from typing import Dict, Any
from config import Config

# No module-level basicConfig() here: when imported by the Flask app or tests
# this module must use the centrally configured root logger (see
# utils.logging_config.setup_logging). Standalone CLI usage configures
# logging itself in main() below.
logger = logging.getLogger("PrinterHealthChecker")


def check_printer_socket(ip: str, port: int = 9100, timeout: float = 1.5) -> Dict[str, Any]:
    """
    Performs a lightweight TCP connection probe to a printer.

    Returns dict with reachable status, response latency (ms), and error message if any.
    """
    start_time = time.perf_counter()
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "reachable": True,
                "latency_ms": latency_ms,
                "error": None
            }
    except socket.timeout:
        return {
            "reachable": False,
            "latency_ms": None,
            "error": "Timeout (no response within 1.5s)"
        }
    except OSError as e:
        return {
            "reachable": False,
            "latency_ms": None,
            "error": str(e)
        }


class PrinterHealthMonitor:
    """Monitors configured printers in a loop and logs status changes."""

    def __init__(self, food_ip: str = None, drinks_ip: str = None):
        self.food_ip = food_ip or Config.FOOD_PRINTER_IP
        self.drinks_ip = drinks_ip or Config.DRINKS_PRINTER_IP
        self.last_state = {
            "food": None,
            "drinks": None
        }

    def check_all(self) -> Dict[str, Any]:
        """Check both printers and return current health status dict."""
        food_res = check_printer_socket(self.food_ip)
        drinks_res = check_printer_socket(self.drinks_ip)

        current = {
            "food_printer": {
                "ip": self.food_ip,
                **food_res
            },
            "drinks_printer": {
                "ip": self.drinks_ip,
                **drinks_res
            }
        }

        # Log status changes
        if self.last_state["food"] != food_res["reachable"]:
            status_str = "ONLINE 🟢" if food_res["reachable"] else "OFFLINE 🔴"
            logger.info(f"Speisen-Drucker ({self.food_ip}) status changed -> {status_str} ({food_res['latency_ms'] or food_res['error']})")
            self.last_state["food"] = food_res["reachable"]

        if self.last_state["drinks"] != drinks_res["reachable"]:
            status_str = "ONLINE 🟢" if drinks_res["reachable"] else "OFFLINE 🔴"
            logger.info(f"Getränke-Drucker ({self.drinks_ip}) status changed -> {status_str} ({drinks_res['latency_ms'] or drinks_res['error']})")
            self.last_state["drinks"] = drinks_res["reachable"]

        return current

    def run_loop(self, interval_seconds: float = 10.0, max_ticks: int = None):
        """Runs the monitoring loop every interval_seconds."""
        logger.info(f"Starting Printer Health Monitor (Interval: {interval_seconds}s)")
        logger.info(f"Monitoring Food Printer IP: {self.food_ip}")
        logger.info(f"Monitoring Drinks Printer IP: {self.drinks_ip}")

        tick = 0
        try:
            while max_ticks is None or tick < max_ticks:
                status = self.check_all()
                food_st = "🟢 OK" if status["food_printer"]["reachable"] else "🔴 FAIL"
                drinks_st = "🟢 OK" if status["drinks_printer"]["reachable"] else "🔴 FAIL"
                
                food_lat = f"{status['food_printer']['latency_ms']}ms" if status["food_printer"]["reachable"] else status["food_printer"]["error"]
                drinks_lat = f"{status['drinks_printer']['latency_ms']}ms" if status["drinks_printer"]["reachable"] else status["drinks_printer"]["error"]

                logger.info(f"[Tick #{tick+1}] Speisen: {food_st} ({food_lat}) | Getränke: {drinks_st} ({drinks_lat})")
                
                tick += 1
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Printer Health Monitor stopped by user.")


def main():
    from utils.logging_config import setup_logging
    setup_logging(Config.LOG_LEVEL, Config.LOG_DIR)

    parser = argparse.ArgumentParser(description="Cyclic Printer Health Checker for Real Hardware")
    parser.add_argument("--interval", type=float, default=10.0, help="Check interval in seconds (default: 10)")
    parser.add_argument("--food-ip", type=str, default=None, help="Override Food Printer IP")
    parser.add_argument("--drinks-ip", type=str, default=None, help="Override Drinks Printer IP")
    parser.add_argument("--ticks", type=int, default=None, help="Max check ticks (default: infinite)")
    args = parser.parse_args()

    monitor = PrinterHealthMonitor(food_ip=args.food_ip, drinks_ip=args.drinks_ip)
    monitor.run_loop(interval_seconds=args.interval, max_ticks=args.ticks)


if __name__ == "__main__":
    main()
