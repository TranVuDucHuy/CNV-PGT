import os
from rq import Queue, Worker
from redis import Redis


def redis_connection() -> Redis:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    return Redis(host=host, port=port)


def main():
    conn = redis_connection()
    q = Queue(name="sandbox_queue", connection=conn)

    worker = Worker([q], connection=conn, job_monitoring_interval=5)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
