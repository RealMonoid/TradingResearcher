"""Shared errors at the authenticated application boundary."""


class Denied(PermissionError):
    pass


class Conflict(RuntimeError):
    pass
