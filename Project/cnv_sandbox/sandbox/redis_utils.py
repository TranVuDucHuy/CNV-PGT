import os
from rq import Queue
from redis import Redis


def connect_redis() -> Redis:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    return Redis(host=host, port=port)


def connect_queue(redis_conn: Redis, queue_name: str = "sandbox_queue") -> Queue:
    return Queue(queue_name, connection=redis_conn)
