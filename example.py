"""
Example usage of the job scheduler demonstrating various features.
"""
from datetime import datetime, timedelta
import time

from scheduler import JobScheduler
from job import Job


# Example job functions
def simple_task(message: str):
    """A simple task that prints a message."""
    print(f"[TASK] {message}")


def failing_task(fail_count: int = 2):
    """A task that fails a specified number of times before succeeding."""
    if not hasattr(failing_task, 'attempts'):
        failing_task.attempts = {}

    # Track attempts per call
    call_id = id(fail_count)
    if call_id not in failing_task.attempts:
        failing_task.attempts[call_id] = 0

    failing_task.attempts[call_id] += 1
    current_attempt = failing_task.attempts[call_id]

    if current_attempt <= fail_count:
        print(f"[FAILING] Attempt {current_attempt} - Simulating failure...")
        raise Exception(f"Simulated failure (attempt {current_attempt})")
    else:
        print(f"[SUCCESS] Attempt {current_attempt} - Task succeeded!")


def compute_task(x: int, y: int):
    """A computational task."""
    result = x + y
    print(f"[COMPUTE] {x} + {y} = {result}")
    return result


def main():
    """Run example scenarios."""
    print("=" * 60)
    print("Job Scheduler Demo")
    print("=" * 60)

    # Create scheduler
    scheduler = JobScheduler(poll_interval=0.1)
    scheduler.start()

    print("\n1. Scheduling immediate job...")
    job1 = Job(
        func=simple_task,
        name="immediate_job",
        args=("Hello from immediate job!",)
    )
    scheduler.schedule(job1)

    print("\n2. Scheduling delayed job (2 seconds from now)...")
    job2 = Job(
        func=simple_task,
        name="delayed_job",
        args=("Hello from delayed job!",),
        scheduled_time=datetime.now() + timedelta(seconds=2)
    )
    scheduler.schedule(job2)

    print("\n3. Scheduling job with retries (will fail twice, then succeed)...")
    job3 = Job(
        func=failing_task,
        name="retry_job",
        args=(2,),  # Fail 2 times before succeeding
        max_retries=3,
        backoff_seconds=1.0
    )
    scheduler.schedule(job3)

    print("\n4. Scheduling computational job with kwargs...")
    job4 = Job(
        func=compute_task,
        name="compute_job",
        kwargs={"x": 42, "y": 8},
        scheduled_time=datetime.now() + timedelta(seconds=1)
    )
    scheduler.schedule(job4)

    print("\n5. Scheduling job that will exhaust retries...")
    job5 = Job(
        func=failing_task,
        name="exhausted_job",
        args=(10,),  # Fail 10 times (more than max retries)
        max_retries=2,
        backoff_seconds=0.5
    )
    scheduler.schedule(job5)

    # Let jobs run
    print("\n" + "-" * 60)
    print("Scheduler running... Watch jobs execute below:")
    print("-" * 60 + "\n")

    # Monitor progress
    for i in range(15):
        time.sleep(1)
        pending = scheduler.get_job_count()
        if pending == 0 and i > 5:
            print(f"\n[INFO] All jobs completed after {i + 1} seconds")
            break
        if i % 3 == 0:
            print(f"[INFO] Pending jobs: {pending}")

    # Stop scheduler
    print("\n" + "=" * 60)
    scheduler.stop()
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
