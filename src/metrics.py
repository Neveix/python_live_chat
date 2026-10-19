from prometheus_client import Counter, Gauge, Histogram

ACTIVE_WS = Gauge("chat_active_websocket_connections", "Active WebSocket connections")

MSG_RECEIVED = Counter("chat_messages_received_total", "Messages received from clients")
MSG_SENT = Counter("chat_messages_sent_total", "Messages sent to clients")

SEND_LATENCY = Histogram(
    "chat_websocket_send_seconds",
    "Time spent sending a message to a single websocket",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)
