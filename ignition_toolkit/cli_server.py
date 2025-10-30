"""
Cross-platform server management commands

Replaces bash-only scripts (start_server.sh, stop_server.sh, check_server.sh)
with Python commands that work on Windows, Linux, and macOS.
"""
import os
import sys
import time
from pathlib import Path

import click
import psutil
from rich.console import Console

console = Console()


def find_server_processes():
    """Find all uvicorn processes for ignition_toolkit"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'uvicorn' in ' '.join(cmdline) and 'ignition_toolkit' in ' '.join(cmdline):
                processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes


def is_port_in_use(port=5000):
    """Check if port is in use"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False


@click.command()
@click.option('--port', default=5000, help='Port to run server on')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
def start(port, host):
    """Start the Ignition Toolkit server"""
    console.print("[bold cyan]Starting Ignition Automation Toolkit Server[/bold cyan]")

    # Check if server is already running
    processes = find_server_processes()
    if processes:
        console.print(f"[red]ERROR: Server already running ({len(processes)} process(es))[/red]")
        for proc in processes:
            console.print(f"  PID: {proc.pid}")
        console.print("\n[yellow]Run 'ignition-toolkit server stop' first[/yellow]")
        sys.exit(1)

    # Check if port is available
    if is_port_in_use(port):
        console.print(f"[red]ERROR: Port {port} is already in use[/red]")
        console.print("[yellow]Try a different port with --port option[/yellow]")
        sys.exit(1)

    # Set environment variables for consistent paths
    from ignition_toolkit.config import setup_environment
    setup_environment()

    console.print("[green]✓[/green] Pre-flight checks passed")
    console.print(f"[cyan]Starting server on http://{host}:{port}[/cyan]")
    console.print("\n[bold]Press CTRL+C to stop the server[/bold]\n")

    # Start server using uvicorn module
    try:
        import subprocess
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'ignition_toolkit.api.app:app',
            '--host', host,
            '--port', str(port)
        ])
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error starting server: {e}[/red]")
        sys.exit(1)


@click.command()
@click.option('--force', is_flag=True, help='Force kill processes if normal termination fails')
def stop(force):
    """Stop the Ignition Toolkit server"""
    console.print("[bold cyan]Stopping Ignition Automation Toolkit Server[/bold cyan]")

    processes = find_server_processes()
    if not processes:
        console.print("[green]No server processes found (server not running)[/green]")
        return

    console.print(f"Found {len(processes)} server process(es)")

    # Try graceful termination first
    for proc in processes:
        try:
            console.print(f"Terminating process {proc.pid}...")
            proc.terminate()
        except psutil.NoSuchProcess:
            console.print(f"  Process {proc.pid} already gone")
        except psutil.AccessDenied:
            console.print(f"  [yellow]Access denied for process {proc.pid}[/yellow]")

    # Wait for processes to stop
    console.print("Waiting for processes to stop...")
    time.sleep(2)

    # Check if any still running
    remaining = find_server_processes()
    if remaining:
        if force:
            console.print(f"[yellow]{len(remaining)} process(es) didn't stop, forcing...[/yellow]")
            for proc in remaining:
                try:
                    console.print(f"Killing process {proc.pid}...")
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass
                except psutil.AccessDenied:
                    console.print(f"  [red]Access denied for process {proc.pid}[/red]")

            time.sleep(1)
            final_check = find_server_processes()
            if final_check:
                console.print(f"[red]Warning: {len(final_check)} process(es) could not be stopped[/red]")
                for proc in final_check:
                    console.print(f"  PID: {proc.pid}")
            else:
                console.print("[green]✓ All processes stopped[/green]")
        else:
            console.print(f"[yellow]Warning: {len(remaining)} process(es) didn't stop gracefully[/yellow]")
            for proc in remaining:
                console.print(f"  PID: {proc.pid}")
            console.print("\n[cyan]Try running with --force to kill remaining processes[/cyan]")
    else:
        console.print("[green]✓ Server stopped successfully[/green]")


@click.command()
@click.option('--port', default=5000, help='Port to check')
def status(port):
    """Check server status and health"""
    console.print("[bold cyan]Ignition Toolkit Server Health Check[/bold cyan]\n")

    # Check for running processes
    processes = find_server_processes()
    if not processes:
        console.print("[red]✗ Server is NOT running[/red]")
        console.print("\n[yellow]To start server:[/yellow]")
        console.print("  ignition-toolkit server start")
        sys.exit(1)

    console.print(f"[green]✓ Server process found[/green]")
    for proc in processes:
        console.print(f"  PID: {proc.pid}")

    # Check if port is listening
    if not is_port_in_use(port):
        console.print(f"[yellow]⚠ Port {port} is not listening (server may be starting)[/yellow]")
    else:
        console.print(f"[green]✓ Port {port} is listening[/green]")

    # Try HTTP health check
    try:
        import httpx

        console.print(f"\nChecking HTTP endpoint at http://localhost:{port}/...")
        response = httpx.get(f'http://localhost:{port}/', timeout=5)

        if response.status_code == 200:
            console.print(f"[green]✓ Server is responding (HTTP {response.status_code})[/green]")
        else:
            console.print(f"[yellow]⚠ Server returned HTTP {response.status_code}[/yellow]")

        # Try health endpoint
        try:
            health_response = httpx.get(f'http://localhost:{port}/api/health', timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                console.print(f"[green]✓ Health check passed[/green]")
                console.print(f"  Version: {health_data.get('version', 'unknown')}")
                console.print(f"  Status: {health_data.get('status', 'unknown')}")
        except Exception:
            pass  # Health endpoint optional

        # Summary
        console.print(f"\n[bold green]✓ Server is HEALTHY[/bold green]")
        console.print(f"\n[bold]Access the web UI:[/bold]")
        console.print(f"  http://localhost:{port}")
        console.print(f"\n[bold]Server Info:[/bold]")
        console.print(f"  PID: {processes[0].pid}")
        console.print(f"  Port: {port}")

    except ImportError:
        console.print("\n[yellow]⚠ httpx not installed, skipping HTTP health check[/yellow]")
        console.print("[green]Process is running but HTTP check not available[/green]")
    except Exception as e:
        console.print(f"\n[red]✗ Server not responding to HTTP requests[/red]")
        console.print(f"  Error: {e}")
        console.print("\n[yellow]Server process is running but may not be ready yet[/yellow]")
        sys.exit(1)


@click.group()
def server():
    """Server management commands (start, stop, status)"""
    pass


# Register subcommands
server.add_command(start)
server.add_command(stop)
server.add_command(status)
