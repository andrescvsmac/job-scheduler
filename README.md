# Job Scheduler with Retries and Backoff

Implement a minimal job scheduler with retries and backoff. A `job` can be represented as any callable or function along with some metadata, and your scheduler should support scheduling jobs to run either immediately or at a specific time in the future. Each job can optionally specify a maximum number of retry attempts and a simple backoff interval in seconds. Your scheduler should maintain a set of pending jobs, periodically check (polling) which ones are due, execute them, and—if a job fails—retry it according to its configured limits and backoff delay.

## Project Structure

```bash
job-scheduler/
├── example.py          # Example usage script
├── job.py              # Job class implementation
├── README.md           # This file
├── scheduler.py        # JobScheduler class implementation
└── test_scheduler.py   # Unit tests
```

- `job.py` - 3 methods to implement
- `scheduler.py` - 5 methods to implement

## API Reference

### Job Class

```python
Job(
    func: Callable,              # Function to execute
    name: str = "",              # Human-readable name (auto-generated if empty)
    args: tuple = (),            # Positional arguments
    kwargs: dict = {},           # Keyword arguments
    scheduled_time: datetime = None,  # When to run (None = immediate)
    max_retries: int = 0,        # Maximum retry attempts
    backoff_seconds: float = 1.0 # Delay between retries
)
```

**Methods:**

- `is_due(current_time: datetime) -> bool` - Check if job should run
- `can_retry() -> bool` - Check if retries remain
- `record_attempt(success: bool, error: Exception = None)` - Update job state

### JobScheduler Class

```python
JobScheduler(poll_interval: float = 0.1)
```

**Methods:**

- `schedule(job: Job) -> str` - Add a job, returns job ID
- `start()` - Start the scheduler thread
- `stop(wait: bool = True)` - Stop the scheduler
- `get_pending_jobs() -> List[Job]` - Get all pending jobs
- `get_job_count() -> int` - Get number of pending jobs
- `clear()` - Remove all pending jobs

## Running the Examples

### Demo Script

```bash
python example.py
```

## Testing

The test suite covers:

- Job creation and configuration
- Immediate and delayed execution
- Retry logic and backoff
- Multiple concurrent jobs
- Success/failure scenarios
- Thread safety

Run tests with:

```bash
python test_scheduler.py
```
