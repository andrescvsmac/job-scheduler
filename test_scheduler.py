"""
Unit tests for the job scheduler.
"""
import unittest
from datetime import datetime, timedelta
import time

from job import Job
from scheduler import JobScheduler


class TestJob(unittest.TestCase):
    """Test cases for the Job class."""
    
    def test_job_creation(self):
        """Test basic job creation."""
        def dummy_func():
            pass
        
        job = Job(func=dummy_func, name="test_job")
        self.assertEqual(job.name, "test_job")
        self.assertEqual(job.func, dummy_func)
        self.assertEqual(job.attempts, 0)
        self.assertIsNotNone(job.job_id)
    
    def test_job_auto_name(self):
        """Test automatic job naming."""
        def my_function():
            pass
        
        job = Job(func=my_function)
        self.assertTrue(job.name.startswith("my_function_"))
    
    def test_is_due_immediate(self):
        """Test that jobs with no scheduling are immediately due."""
        job = Job(func=lambda: None)
        self.assertTrue(job.is_due(datetime.now()))
    
    def test_is_due_future(self):
        """Test that future jobs are not due yet."""
        future_time = datetime.now() + timedelta(seconds=10)
        job = Job(func=lambda: None, scheduled_time=future_time)
        self.assertFalse(job.is_due(datetime.now()))
        self.assertTrue(job.is_due(future_time + timedelta(seconds=1)))
    
    def test_can_retry(self):
        """Test retry logic."""
        job = Job(func=lambda: None, max_retries=2)
        self.assertTrue(job.can_retry())  # 0 attempts, can retry
        
        job.attempts = 1
        self.assertTrue(job.can_retry())  # 1 attempt, can retry
        
        job.attempts = 2
        self.assertTrue(job.can_retry())  # 2 attempts, can retry
        
        job.attempts = 3
        self.assertFalse(job.can_retry())  # 3 attempts, exhausted
    
    def test_record_attempt_success(self):
        """Test recording a successful attempt."""
        job = Job(func=lambda: None)
        job.record_attempt(success=True)
        self.assertEqual(job.attempts, 1)
        self.assertIsNone(job.last_error)
        self.assertIsNone(job.next_retry_time)
    
    def test_record_attempt_failure(self):
        """Test recording a failed attempt."""
        job = Job(func=lambda: None, max_retries=2, backoff_seconds=1.0)
        error = Exception("Test error")
        job.record_attempt(success=False, error=error)
        
        self.assertEqual(job.attempts, 1)
        self.assertEqual(job.last_error, error)
        self.assertIsNotNone(job.next_retry_time)


class TestJobScheduler(unittest.TestCase):
    """Test cases for the JobScheduler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = JobScheduler(poll_interval=0.05)
    
    def tearDown(self):
        """Clean up after tests."""
        if self.scheduler.running:
            self.scheduler.stop()
    
    def test_scheduler_creation(self):
        """Test scheduler initialization."""
        self.assertFalse(self.scheduler.running)
        self.assertEqual(self.scheduler.get_job_count(), 0)
    
    def test_schedule_job(self):
        """Test scheduling a job."""
        job = Job(func=lambda: None, name="test")
        job_id = self.scheduler.schedule(job)
        
        self.assertIsNotNone(job_id)
        self.assertEqual(self.scheduler.get_job_count(), 1)
    
    def test_start_stop_scheduler(self):
        """Test starting and stopping the scheduler."""
        self.scheduler.start()
        self.assertTrue(self.scheduler.running)
        
        self.scheduler.stop()
        self.assertFalse(self.scheduler.running)
    
    def test_execute_immediate_job(self):
        """Test execution of an immediate job."""
        result = []
        
        def task():
            result.append("executed")
        
        job = Job(func=task)
        self.scheduler.schedule(job)
        self.scheduler.start()
        
        # Wait for job to execute
        time.sleep(0.3)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "executed")
        self.assertEqual(self.scheduler.get_job_count(), 0)
    
    def test_execute_delayed_job(self):
        """Test execution of a delayed job."""
        result = []
        
        def task():
            result.append(datetime.now())
        
        schedule_time = datetime.now() + timedelta(seconds=0.2)
        job = Job(func=task, scheduled_time=schedule_time)
        self.scheduler.schedule(job)
        self.scheduler.start()
        
        # Job should not execute immediately
        time.sleep(0.1)
        self.assertEqual(len(result), 0)
        
        # Job should execute after delay
        time.sleep(0.3)
        self.assertEqual(len(result), 1)
        self.assertGreaterEqual(result[0], schedule_time)
    
    def test_job_retry_on_failure(self):
        """Test that jobs retry on failure."""
        attempts = []
        
        def failing_task():
            attempts.append(1)
            raise Exception("Intentional failure")
        
        job = Job(
            func=failing_task,
            max_retries=2,
            backoff_seconds=0.1
        )
        self.scheduler.schedule(job)
        self.scheduler.start()
        
        # Wait for retries to complete
        time.sleep(0.6)
        
        # Should have executed 3 times (initial + 2 retries)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(self.scheduler.get_job_count(), 0)
    
    def test_job_eventual_success(self):
        """Test that a job eventually succeeds after retries."""
        attempts = []
        
        def task_succeeds_on_third_try():
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("Not yet")
        
        job = Job(
            func=task_succeeds_on_third_try,
            max_retries=5,
            backoff_seconds=0.1
        )
        self.scheduler.schedule(job)
        self.scheduler.start()
        
        # Wait for job to succeed
        time.sleep(0.5)
        
        # Should succeed on third attempt
        self.assertEqual(len(attempts), 3)
        self.assertEqual(self.scheduler.get_job_count(), 0)
    
    def test_multiple_jobs(self):
        """Test scheduling and executing multiple jobs."""
        results = []
        
        def task(value):
            results.append(value)
        
        job1 = Job(func=task, args=(1,))
        job2 = Job(func=task, args=(2,))
        job3 = Job(func=task, args=(3,))
        
        self.scheduler.schedule(job1)
        self.scheduler.schedule(job2)
        self.scheduler.schedule(job3)
        
        self.assertEqual(self.scheduler.get_job_count(), 3)
        
        self.scheduler.start()
        time.sleep(0.3)
        
        self.assertEqual(sorted(results), [1, 2, 3])
        self.assertEqual(self.scheduler.get_job_count(), 0)
    
    def test_clear_jobs(self):
        """Test clearing all jobs."""
        job1 = Job(func=lambda: None)
        job2 = Job(func=lambda: None)
        
        self.scheduler.schedule(job1)
        self.scheduler.schedule(job2)
        self.assertEqual(self.scheduler.get_job_count(), 2)
        
        self.scheduler.clear()
        self.assertEqual(self.scheduler.get_job_count(), 0)
    
    def test_get_pending_jobs(self):
        """Test retrieving pending jobs."""
        job1 = Job(func=lambda: None, name="job1")
        job2 = Job(func=lambda: None, name="job2")
        
        self.scheduler.schedule(job1)
        self.scheduler.schedule(job2)
        
        pending = self.scheduler.get_pending_jobs()
        self.assertEqual(len(pending), 2)
        self.assertIn(job1, pending)
        self.assertIn(job2, pending)


def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
