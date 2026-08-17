import ipaddress
from urllib.parse import urlparse

from app.core.errors import ApiError


def validate_source_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ApiError(422, "INVALID_SOURCE_URL", "Source URLs must use public HTTPS")
    host = parsed.hostname.casefold()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ApiError(422, "INVALID_SOURCE_URL", "Private source hosts are not allowed")
    try:
        address = ipaddress.ip_address(host)
        if not address.is_global:
            raise ApiError(422, "INVALID_SOURCE_URL", "Private source addresses are not allowed")
    except ValueError:
        pass
    return value
