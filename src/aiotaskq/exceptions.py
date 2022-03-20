class WorkerNotReady(Exception):
    """Attempt to send task to worker but no worker is subscribing to tasks channel."""
