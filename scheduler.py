"""
Job scheduler with support for delayed execution, retries, and exponential backoff.

TODO: Implement the core scheduling logic.
"""
from typing import List, Optional
from datetime import datetime
import logging
from threading import Thread, Event, Lock

from job import Job


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class JobScheduler:
    """
    A minimal job scheduler that supports:
    - Immediate and delayed job execution
    - Configurable retry attempts
    - Backoff delays between retries
    - Thread-safe job queue management
    """

    def __init__(self, poll_interval: float = 0.1):
        """
        Initialize the job scheduler.

        Args:
            poll_interval: How often (in seconds) to check for due jobs
        """
        self.poll_interval = poll_interval
        self.jobs: List[Job] = []
        self.jobs_lock = Lock()
        self.running = False
        self.scheduler_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.logger = logging.getLogger(__name__)

    def schedule(self, job: Job) -> str:
        """
        TODO: Implement this method.

        Add a job to the scheduler in a thread-safe manner.

        Args:
            job: The job to schedule

        Returns:
            The job's unique identifier
        """
        raise NotImplementedError("Needs to implement schedule()")

    def start(self):
        """
        Start the scheduler in a background thread.

        - Check if already running
        - Set running flag
        - Clear stop event
        - Create and start daemon thread running _run()
        """
        self.running = True
        self.stop_event.clear()
        self.scheduler_thread = Thread(target=self._run, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Scheduler started")

    def stop(self, wait: bool = True):
        """
        Stop the scheduler gracefully.
        - Set running to False
        - Signal stop event
        - Optionally wait for thread to finish

        Args:
            wait: If True, wait for the scheduler thread to finish
        """
        if not self.running:
            return

        self.running = False
        self.stop_event.set()

        if wait and self.scheduler_thread:
            self.scheduler_thread.join()

        self.logger.info("Scheduler stopped")

    def _run(self):
        """
        TODO: Implement this method.

        Main scheduler loop (runs in background thread).
        - Loop while running
        - Get current time
        - Find jobs that are due (thread-safe)
        - Execute due jobs (outside the lock)
        - Wait for poll_interval before next iteration
        """
        while self.running:
            current_time = datetime.now()

            # Find and execute due jobs
            jobs_to_execute = []

            # TODO: Implement job fetching logic

            # Execute jobs outside the lock to avoid blocking
            for job in jobs_to_execute:
                self._execute_job(job)

            # Wait before next poll
            self.stop_event.wait(self.poll_interval)

    def _execute_job(self, job: Job):
        """
        TODO: Implement this method.

        Execute a job and handle retries.
        - Try to execute job.func(*job.args, **job.kwargs)
        - On success: record success, remove job
        - On failure: record failure with error
          - If can retry: log retry info
          - If cannot retry: remove job

        Args:
            job: The job to execute
        """
        self.logger.info(f"Executing {job}")

        raise NotImplementedError("Needs to implement _execute_job()")

    def _remove_job(self, job: Job):
        """
        TODO: Implement this method.

        Remove a job from the scheduler in a thread-safe manner.

        Args:
            job: The job to remove
        """
        raise NotImplementedError("Needs to implement _remove_job()")

    def get_pending_jobs(self) -> List[Job]:
        """
        Get a copy of all pending jobs (thread-safe).

        Returns:
            List of pending jobs
        """
        raise NotImplementedError("Needs to implement get_pending_jobs()")

    def get_job_count(self) -> int:
        """
        Get the number of pending jobs (thread-safe).

        Returns:
            Number of jobs in the queue
        """
        raise NotImplementedError("Needs to implement get_job_count()")

    def clear(self):
        """Remove all pending jobs (thread-safe)."""
        with self.jobs_lock:
            self.jobs.clear()
            self.logger.info("Cleared all jobs")
