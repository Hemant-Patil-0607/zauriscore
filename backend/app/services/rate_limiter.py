import redis
from datetime import datetime, timezone
from app.core.config import settings


class RateLimiter:
    """Redis token bucket rate limiter per user per day."""

    PLAN_LIMITS = {
        "free": settings.rate_limit_free_scans_per_day,
        "pro": settings.rate_limit_pro_scans_per_day,
        "enterprise": -1,  # unlimited
    }

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = redis.from_url(settings.redis_url, decode_responses=True)
        return self._client

    def _key(self, user_id: str) -> str:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"rate_limit:{user_id}:{today}"

    def check_and_consume(self, user_id: str, plan: str) -> tuple[bool, int, int]:
        """
        Returns (allowed, used, limit).
        Raises nothing — callers handle the response.
        """
        limit = self.PLAN_LIMITS.get(plan, self.PLAN_LIMITS["free"])

        if limit == -1:
            return True, 0, -1

        key = self._key(user_id)
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 86400)  # 24 hours TTL
        results = pipe.execute()
        used = results[0]

        if used > limit:
            return False, used, limit

        return True, used, limit

    def refund(self, user_id: str, plan: str):
        """
        Refund one usage when enqueue fails.
        """
        limit = self.PLAN_LIMITS.get(plan, self.PLAN_LIMITS["free"])
        if limit == -1:
            return  # no refund needed for unlimited

        key = self._key(user_id)
        # DECR and ensure not below 0
        used = self.client.decr(key)
        if used < 0:
            self.client.set(key, 0)


rate_limiter = RateLimiter()
