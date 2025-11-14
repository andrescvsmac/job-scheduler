"""
Web server for Job Scheduler Dashboard.
Provides REST API endpoints and serves the HTML dashboard.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse
import threading
import time

from scheduler import JobScheduler
from job import Job


class ThreadSafeStats:
    """Thread-safe statistics counter."""

    def __init__(self):
        self._stats = {
            'completed': 0,
            'failed': 0,
            'executions': 0
        }
        self._lock = threading.Lock()

    def increment(self, key):
        """Atomically increment a stat counter."""
        with self._lock:
            self._stats[key] += 1

    def get_all(self):
        """Get a snapshot of all stats."""
        with self._lock:
            return self._stats.copy()

    def reset(self):
        """Reset all counters."""
        with self._lock:
            self._stats = {
                'completed': 0,
                'failed': 0,
                'executions': 0
            }


class SchedulerDashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the scheduler dashboard."""

    # Class-level scheduler instance
    scheduler = None
    stats = None  # Will be initialized as ThreadSafeStats instance

    def _set_headers(self, content_type='application/json'):
        """Set response headers."""
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        """Handle preflight requests."""
        self._set_headers()

    def do_GET(self):
        """Handle GET requests."""
        path = urlparse(self.path).path

        if path == '/':
            # Serve the dashboard HTML
            self._set_headers('text/html')
            try:
                with open('dashboard.html', 'r') as f:
                    self.wfile.write(f.read().encode())
            except FileNotFoundError:
                self.send_error(404, "dashboard.html not found")

        elif path == '/status':
            # Get scheduler status and jobs
            self._set_headers()
            jobs = self.scheduler.get_pending_jobs()
            current_stats = self.stats.get_all()

            response = {
                'stats': {
                    'pending': len(jobs),
                    'completed': current_stats['completed'],
                    'failed': current_stats['failed'],
                    'executions': current_stats['executions']
                },
                'jobs': [self._job_to_dict(job) for job in jobs],
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path

        if path == '/schedule/simple':
            job_id = self._schedule_simple_job()
            self._send_json_response({'job_id': job_id, 'type': 'simple'})

        elif path == '/schedule/delayed':
            job_id = self._schedule_delayed_job()
            self._send_json_response({'job_id': job_id, 'type': 'delayed'})

        elif path == '/schedule/retry':
            job_id = self._schedule_retry_job()
            self._send_json_response({'job_id': job_id, 'type': 'retry'})

        elif path == '/schedule/batch':
            job_ids = self._schedule_batch_jobs()
            self._send_json_response({'job_ids': job_ids, 'count': len(job_ids), 'type': 'batch'})

        elif path == '/schedule/failing':
            job_id = self._schedule_failing_job()
            self._send_json_response({'job_id': job_id, 'type': 'failing'})

        elif path == '/clear':
            self.scheduler.clear()
            self._send_json_response({'status': 'cleared'})

        else:
            self.send_error(404)

    def _send_json_response(self, data):
        """Send JSON response."""
        self._set_headers()
        self.wfile.write(json.dumps(data).encode())

    def _job_to_dict(self, job):
        """Convert Job object to dictionary."""
        return {
            'id': job.job_id[:8],
            'name': job.name,
            'attempts': job.attempts,
            'max_retries': job.max_retries,
            'scheduled_time': job.scheduled_time.strftime('%H:%M:%S') if job.scheduled_time else None,
            'next_retry': job.next_retry_time.strftime('%H:%M:%S') if job.next_retry_time else None,
            'last_error': str(job.last_error) if job.last_error else None,
            'status': 'pending'
        }

    def _schedule_simple_job(self):
        """Schedule a simple immediate job."""
        def simple_task():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Simple job executed!")
            time.sleep(0.5)
            self.stats.increment('completed')
            self.stats.increment('executions')

        job = Job(
            func=simple_task,
            name="simple_task"
        )
        return self.scheduler.schedule(job)

    def _schedule_delayed_job(self):
        """Schedule a job delayed by 5 seconds."""
        def delayed_task():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Delayed job executed!")
            time.sleep(0.3)
            self.stats['completed'] += 1
            self.stats['executions'] += 1

        job = Job(
            func=delayed_task,
            name="delayed_task",
            scheduled_time=datetime.now() + timedelta(seconds=5)
        )
        return self.scheduler.schedule(job)

    def _schedule_retry_job(self):
        """Schedule a job that fails twice then succeeds."""
        # Create a unique attempt counter for this job
        attempt_counter = {'count': 0}

        def retry_task():
            attempt_counter['count'] += 1
            self.stats.increment('executions')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Retry job attempt {attempt_counter['count']}")

            if attempt_counter['count'] < 3:
                raise Exception(f"Simulated failure (attempt {attempt_counter['count']})")

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Retry job succeeded!")
            self.stats.increment('completed')

        job = Job(
            func=retry_task,
            name="retry_task",
            max_retries=3,
            backoff_seconds=2.0
        )
        return self.scheduler.schedule(job)

    def _schedule_batch_jobs(self):
        """Schedule multiple jobs at once."""
        job_ids = []

        for i in range(5):
            def batch_task(task_num=i):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Batch task {task_num} completed")
                time.sleep(0.2)
                self.stats['completed'] += 1
                self.stats['executions'] += 1

            job = Job(
                func=batch_task,
                name=f"batch_task_{i}",
                scheduled_time=datetime.now() + timedelta(seconds=i * 2)
            )
            job_ids.append(self.scheduler.schedule(job))

        return job_ids

    def _schedule_failing_job(self):
        """Schedule a job that always fails."""
        # Track attempts to count as failed only once
        attempt_counter = {'count': 0}

        def failing_task():
            attempt_counter['count'] += 1
            current_attempt = attempt_counter['count']
            self.stats.increment('executions')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failing job attempt {current_attempt}")

            # Always raise an exception
            try:
                raise Exception("This job is designed to fail")
            except Exception as e:
                # If this is the last attempt (initial + max_retries), count as failed
                if current_attempt >= 3:  # 1 initial + 2 retries = 3 total attempts
                    self.stats.increment('failed')
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Job exhausted all retries - marked as failed")
                raise e

        job = Job(
            func=failing_task,
            name="failing_task",
            max_retries=2,
            backoff_seconds=1.5
        )

        return self.scheduler.schedule(job)

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")


def run_server(port=8000):
    """
    Start the dashboard web server.

    Args:
        port: Port number to run the server on
    """
    # Initialize the scheduler
    scheduler = JobScheduler(poll_interval=1)
    scheduler.start()
    SchedulerDashboardHandler.scheduler = scheduler

    # Initialize thread-safe stats
    SchedulerDashboardHandler.stats = ThreadSafeStats()

    # Create and start the HTTP server
    server = HTTPServer(('localhost', port), SchedulerDashboardHandler)
    print("=" * 60)
    print("Job Scheduler Dashboard Server")
    print("=" * 60)
    print(f"\nServer running at: http://localhost:{port}")
    print(f"Dashboard URL: http://localhost:{port}/")
    print("Scheduler status: Running")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Shutting down server...")
        scheduler.stop()
        server.shutdown()
        print("Server stopped.")
        print("=" * 60)


if __name__ == "__main__":
    run_server()
