class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()

    def mark_seen(self, topic: str, idempotency_key: str) -> bool:
        key = (topic, idempotency_key)
        if key in self._seen:
            return False
        self._seen.add(key)
        return True
