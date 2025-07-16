class DeviceNotFoundError(Error):
    """Device was not found.

    The device seems to be not accessible.
    The return code for this exception is `90`.

    inheritance:

    .. inheritance-diagram:: escpos.exceptions.Error
        :parts: 1

    """

    def __init__(self, msg: str = "") -> None:
        """Initialize DeviceNotFoundError object."""
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 90

    def __str__(self) -> str:
        """Return string representation of DeviceNotFoundError."""
        return f"Device not found ({self.msg})"