# sse.py

from queue import Queue
from threading import Lock

_connections = {}
_lock = Lock()


def subscribe(session_uuid):
    """
    Create a queue for a new browser connection.
    """
    q = Queue()

    with _lock:
        _connections.setdefault(str(session_uuid), []).append(q)

    return q


def unsubscribe(session_uuid, q):
    """
    Remove a queue when browser disconnects.
    """
    session_uuid = str(session_uuid)

    with _lock:
        queues = _connections.get(session_uuid, [])

        if q in queues:
            queues.remove(q)

        if not queues:
            _connections.pop(session_uuid, None)


def notify_session(session_uuid, event_type, payload=None):
    """
    Send event to all connected browsers.
    """
    session_uuid = str(session_uuid)

    if payload is None:
        payload = {}

    event = {
        "type": event_type,
        "payload": payload,
    }

    with _lock:
        queues = list(_connections.get(session_uuid, []))

    for q in queues:
        q.put(event)