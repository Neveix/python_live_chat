from redis import Redis

redis = Redis.from_url(
    "redis://localhost:6379", socket_timeout=5, socket_connect_timeout=5
)
