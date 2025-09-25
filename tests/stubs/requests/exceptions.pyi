from __future__ import annotations


class RequestException(Exception):
    ...


class Timeout(RequestException):
    ...


__all__ = ["RequestException", "Timeout"]
