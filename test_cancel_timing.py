#!/usr/bin/env python3
"""
Test script to precisely measure cancellation timing
"""
import asyncio
import time
import httpx
from datetime import datetime


def log_time(message: str):
    """Log message with precise timestamp"""
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{now}] {message}")


async def test_cancellation():
    """Test cancellation timing"""
    base_url = "http://localhost:5000"

    async with httpx.AsyncClient() as client:
        # Start execution
        log_time("Starting execution...")
        start_response = await client.post(
            f"{base_url}/api/executions",
            json={
                "playbook_path": "tests/test_cancellation.yaml",
                "parameters": {}
            }
        )
        data = start_response.json()
        execution_id = data["execution_id"]
        log_time(f"Execution started: {execution_id}")

        # Wait 2 seconds
        log_time("Waiting 2 seconds before cancelling...")
        await asyncio.sleep(2)

        # Send cancel
        log_time("Sending cancel request...")
        cancel_start = time.time()
        cancel_response = await client.post(
            f"{base_url}/api/executions/{execution_id}/cancel"
        )
        cancel_duration = time.time() - cancel_start
        log_time(f"Cancel request returned in {cancel_duration:.3f}s")

        # Wait a bit for cancellation to complete
        await asyncio.sleep(1)

        # Check status
        log_time("Checking execution status...")
        status_response = await client.get(
            f"{base_url}/api/executions/{execution_id}/status"
        )
        status_data = status_response.json()

        # Calculate total duration
        started_at = status_data["started_at"]
        completed_at = status_data["completed_at"]
        log_time(f"Execution status: {status_data['status']}")
        log_time(f"Started at: {started_at}")
        log_time(f"Completed at: {completed_at}")

        if completed_at:
            # Parse ISO timestamps and calculate duration
            from datetime import datetime
            start_time = datetime.fromisoformat(started_at)
            end_time = datetime.fromisoformat(completed_at)
            total_duration = (end_time - start_time).total_seconds()
            log_time(f"Total execution duration: {total_duration:.3f}s")
        else:
            log_time("Execution hasn't completed yet (cancellation may still be in progress)")

        # Check steps
        for i, step_result in enumerate(status_data["step_results"]):
            if step_result.get("started_at"):
                log_time(f"  Step {i+1} ({step_result['step_id']}): {step_result['status']}")


if __name__ == "__main__":
    asyncio.run(test_cancellation())
