"""
Job class representing a schedulable unit of work with retry and backoff configuration.

TODO: Implement the core methods to make jobs work with scheduling and retries.
"""
from typing import Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Job:
    """
    Represents a job to be scheduled and executed.

    Attributes:
        func: The callable to execute
        name: Human-readable name for the job
        args: Positional arguments for the callable
        kwargs: Keyword arguments for the callable
        scheduled_time: When the job should run (None = immediately)
        max_retries: Maximum number of retry attempts (0 = no retries)
        backoff_seconds: Delay in seconds between retry attempts
        job_id: Unique identifier for the job
        attempts: Current number of execution attempts
        next_retry_time: When the next retry should occur
        last_error: Last exception encountered during execution
    """
    func: Callable
    name: str = ""
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    scheduled_time: Optional[datetime] = None
    max_retries: int = 0
    backoff_seconds: float = 1.0

    # Internal state (auto-generated)
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attempts: int = field(default=0, init=False)
    next_retry_time: Optional[datetime] = field(default=None, init=False)
    last_error: Optional[Exception] = field(default=None, init=False)

    def __post_init__(self):
        """Initialize job name if not provided."""
        if not self.name:
            self.name = f"{self.func.__name__}_{self.job_id[:8]}"

    def is_due(self, current_time: datetime) -> bool:
        """
        TODO: Implement this method.

        Check if the job is due to run at the given time.
        Consider:
        - If the job is waiting for a retry (check next_retry_time)
        - If the job is scheduled for the future (check scheduled_time)
        - If the job has no scheduling constraints (should run immediately)

        Args:
            current_time: The current datetime to check against

        Returns:
            True if the job should be executed now, False otherwise
        """
        raise NotImplementedError("Needs to implement is_due()")

    def can_retry(self) -> bool:
        """
        TODO: Implement this method.

        Check if the job can be retried after a failure.
        Consider that a job with max_retries=2 can run 3 times total:
        - Initial attempt (attempts=0)
        - First retry (attempts=1)
        - Second retry (attempts=2)

        Returns:
            True if retry attempts remain, False otherwise
        """
        raise NotImplementedError("Candidate needs to implement can_retry()")

    def record_attempt(self, success: bool, error: Optional[Exception] = None):
        """
        TODO: Implement this method.

        Record an execution attempt and update job state.
        - Increment the attempts counter
        - If failed, store the error
        - If failed and can retry, calculate and set next_retry_time

        Args:
            success: Whether the execution succeeded
            error: Exception if execution failed
        """
        raise NotImplementedError("Needs to implement record_attempt()")

    def __repr__(self) -> str:
        """String representation of the job."""
        return (f"Job(name='{self.name}', id={self.job_id[:8]}, "
                f"attempts={self.attempts}/{self.max_retries + 1})")
