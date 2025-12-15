import queue

# Global queue to process errors from different threads
error_queue: queue.Queue[tuple] = queue.Queue()
