class EventBus:
    """Synchronous in-process pub/sub: publish(event_name, **payload) calls
    every callback subscribed to that event_name, in subscription order."""

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_name, callback):
        self._subscribers.setdefault(event_name, []).append(callback)

    def publish(self, event_name, **payload):
        for callback in self._subscribers.get(event_name, []):
            callback(**payload)
