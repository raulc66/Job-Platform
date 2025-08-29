import logging
from typing import Any, Dict
from .models import Event

logger = logging.getLogger("analytics")

def _get_client_ip(request) -> str:
    xfwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if xfwd:
        return xfwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")

def log_event(request, name: str, properties: Dict[str, Any] | None = None):
    props = properties or {}
    rid = getattr(request, "request_id", "") or request.META.get("HTTP_X_REQUEST_ID", "")
    ua = request.META.get("HTTP_USER_AGENT", "")
    Event.objects.create(
        name=name,
        user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
        path=getattr(request, "path", "") or "",
        ip=_get_client_ip(request),
        user_agent=ua,
        request_id=rid,
        properties=props,
    )
    logger.info(
        "event name=%s request_id=%s path=%s user=%s",
        name,
        rid,
        getattr(request, "path", ""),
        getattr(getattr(request, "user", None), "id", None),
        extra={"event": name, "request_id": rid, "props": props},
    )
