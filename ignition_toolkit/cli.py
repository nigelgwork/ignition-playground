"""
Command-line interface for Ignition Automation Toolkit
"""

import click
import uvicorn
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def main() -> None:
    """Ignition Automation Toolkit - SCADA automation made simple"""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="API server host")
@click.option("--port", default=5000, help="API server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the API server and web UI"""
    console.print(
        Panel.fit(
            "[bold cyan]Ignition Automation Toolkit[/bold cyan]\n"
            f"Server starting on http://{host}:{port}",
            border_style="cyan",
        )
    )

    uvicorn.run(
        "ignition_toolkit.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@main.command()
def init() -> None:
    """Initialize credential vault and configuration"""
    from ignition_toolkit.credentials.vault import CredentialVault

    console.print("\n[bold cyan]Initializing Ignition Automation Toolkit...[/bold cyan]\n")

    # Create credential vault
    vault = CredentialVault()
    vault_path = vault.vault_path

    console.print(f"✅ Credential vault created: [green]{vault_path}[/green]")
    console.print(f"✅ Encryption key generated: [green]{vault_path / 'encryption.key'}[/green]")
    console.print("\n[yellow]⚠️  Keep your encryption key safe! Loss of key = loss of credentials[/yellow]")

    # Create data directory
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    console.print(f"✅ Data directory created: [green]{data_dir.absolute()}[/green]")

    # Create playbooks directory
    playbooks_dir = Path("./playbooks")
    playbooks_dir.mkdir(exist_ok=True)
    console.print(f"✅ Playbooks directory created: [green]{playbooks_dir.absolute()}[/green]")

    console.print("\n[bold green]✅ Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Run: [cyan]ignition-toolkit serve[/cyan]")
    console.print("  2. Open: [cyan]http://localhost:5000[/cyan]")
    console.print("  3. Add credentials via web UI or CLI\n")


@main.group()
def credential() -> None:
    """Manage credentials"""
    pass


@credential.command("add")
@click.argument("name")
@click.option("--username", prompt=True, help="Username")
@click.option("--password", prompt=True, hide_input=True, help="Password")
@click.option("--description", default="", help="Credential description")
def credential_add(name: str, username: str, password: str, description: str) -> None:
    """Add a new credential"""
    from ignition_toolkit.credentials.vault import CredentialVault
    from ignition_toolkit.credentials.models import Credential

    vault = CredentialVault()
    credential = Credential(
        name=name,
        username=username,
        password=password,
        description=description,
    )
    vault.save_credential(credential)

    console.print(f"\n✅ Credential '[cyan]{name}[/cyan]' saved successfully")
    console.print(f"   Use in playbooks: [yellow]{{{{ credential.{name} }}}}[/yellow]\n")


@credential.command("list")
def credential_list() -> None:
    """List all stored credentials"""
    from ignition_toolkit.credentials.vault import CredentialVault
    from rich.table import Table

    vault = CredentialVault()
    credentials = vault.list_credentials()

    if not credentials:
        console.print("\n[yellow]No credentials stored yet[/yellow]")
        console.print("Add one with: [cyan]ignition-toolkit credential add <name>[/cyan]\n")
        return

    table = Table(title="Stored Credentials", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="cyan")
    table.add_column("Username", style="white")
    table.add_column("Description", style="dim")

    for cred in credentials:
        table.add_row(cred.name, cred.username, cred.description or "")

    console.print()
    console.print(table)
    console.print()


@credential.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this credential?")
def credential_delete(name: str) -> None:
    """Delete a credential"""
    from ignition_toolkit.credentials.vault import CredentialVault

    vault = CredentialVault()
    vault.delete_credential(name)

    console.print(f"\n✅ Credential '[cyan]{name}[/cyan]' deleted\n")


@main.group()
def playbook() -> None:
    """Manage playbooks"""
    pass


@playbook.command("list")
def playbook_list() -> None:
    """List available playbooks"""
    from pathlib import Path
    from rich.table import Table

    playbooks_dir = Path("./playbooks")
    if not playbooks_dir.exists():
        console.print("\n[yellow]No playbooks directory found[/yellow]\n")
        return

    yaml_files = list(playbooks_dir.rglob("*.yaml")) + list(playbooks_dir.rglob("*.yml"))

    if not yaml_files:
        console.print("\n[yellow]No playbooks found[/yellow]")
        console.print("Create one in: [cyan]./playbooks/[/cyan]\n")
        return

    table = Table(title="Available Playbooks", show_header=True, header_style="bold cyan")
    table.add_column("Path", style="cyan")
    table.add_column("Size", style="white")

    for yaml_file in sorted(yaml_files):
        rel_path = yaml_file.relative_to(playbooks_dir)
        size = f"{yaml_file.stat().st_size / 1024:.1f} KB"
        table.add_row(str(rel_path), size)

    console.print()
    console.print(table)
    console.print()


@playbook.command("run")
@click.argument("playbook_path", type=click.Path(exists=True))
@click.option("--param", "-p", multiple=True, help="Parameter in format name=value")
@click.option("--gateway-url", help="Gateway URL (alternative to --param)")
@click.option("--gateway-username", help="Gateway username")
@click.option("--gateway-credential", help="Gateway credential name from vault")
def playbook_run(
    playbook_path: str,
    param: tuple,
    gateway_url: str | None,
    gateway_username: str | None,
    gateway_credential: str | None,
) -> None:
    """Run a playbook"""
    import asyncio
    from pathlib import Path
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from ignition_toolkit.playbook.loader import PlaybookLoader
    from ignition_toolkit.playbook.engine import PlaybookEngine
    from ignition_toolkit.gateway import GatewayClient
    from ignition_toolkit.credentials import CredentialVault
    from ignition_toolkit.storage import get_database

    # Load playbook
    console.print(f"\n[bold cyan]Loading playbook:[/bold cyan] {playbook_path}\n")
    loader = PlaybookLoader()
    playbook = loader.load_from_file(Path(playbook_path))

    console.print(f"  Name: [green]{playbook.name}[/green]")
    console.print(f"  Version: [green]{playbook.version}[/green]")
    console.print(f"  Steps: [green]{len(playbook.steps)}[/green]\n")

    # Parse parameters
    parameters = {}
    for p in param:
        if "=" not in p:
            console.print(f"[red]Invalid parameter format: {p}[/red]")
            console.print("Use: --param name=value\n")
            return
        name, value = p.split("=", 1)
        parameters[name] = value

    # Add gateway parameters if provided
    if gateway_url:
        parameters["gateway_url"] = gateway_url
    if gateway_username:
        parameters["gateway_username"] = gateway_username
    if gateway_credential:
        parameters["gateway_credential"] = gateway_credential

    # Prompt for missing required parameters
    for param_def in playbook.parameters:
        if param_def.required and param_def.name not in parameters:
            if param_def.type.value == "credential":
                console.print(
                    f"[yellow]Required credential parameter:[/yellow] {param_def.name}"
                )
                console.print(f"Use: --param {param_def.name}=<credential_name>\n")
                return
            else:
                value = click.prompt(
                    f"Enter value for '{param_def.name}' ({param_def.type.value})"
                )
                parameters[param_def.name] = value

    # Initialize components
    vault = CredentialVault()
    database = get_database()
    gateway_client = None

    # Create Gateway client if needed
    if gateway_url:
        gateway_client = GatewayClient(gateway_url)

    # Execute playbook
    async def run():
        engine = PlaybookEngine(
            gateway_client=gateway_client,
            credential_vault=vault,
            database=database,
        )

        console.print("[bold cyan]Executing playbook...[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running...", total=None)

            def update_callback(state):
                step_count = len(state.step_results)
                total_steps = len(playbook.steps)
                progress.update(task, description=f"Step {step_count}/{total_steps}")

            engine.set_update_callback(update_callback)

            try:
                if gateway_client:
                    await gateway_client.__aenter__()

                execution_state = await engine.execute_playbook(
                    playbook, parameters, base_path=Path(playbook_path).parent
                )

                progress.stop()

                # Show results
                console.print(f"\n[bold]Execution Status:[/bold] ", end="")
                if execution_state.status.value == "completed":
                    console.print(f"[bold green]{execution_state.status.value}[/bold green]")
                elif execution_state.status.value == "failed":
                    console.print(f"[bold red]{execution_state.status.value}[/bold red]")
                    if execution_state.error:
                        console.print(f"[red]Error: {execution_state.error}[/red]")
                else:
                    console.print(f"[bold yellow]{execution_state.status.value}[/bold yellow]")

                # Show step results
                from rich.table import Table

                table = Table(title="Step Results", show_header=True, header_style="bold cyan")
                table.add_column("Step ID", style="cyan")
                table.add_column("Status", style="white")
                table.add_column("Duration", style="dim")

                for result in execution_state.step_results:
                    if result.completed_at and result.started_at:
                        duration = (result.completed_at - result.started_at).total_seconds()
                        duration_str = f"{duration:.1f}s"
                    else:
                        duration_str = "-"

                    status_color = {
                        "completed": "green",
                        "failed": "red",
                        "skipped": "yellow",
                    }.get(result.status.value, "white")

                    table.add_row(
                        result.step_id,
                        f"[{status_color}]{result.status.value}[/{status_color}]",
                        duration_str,
                    )

                console.print()
                console.print(table)
                console.print()

            finally:
                if gateway_client:
                    await gateway_client.__aexit__(None, None, None)

    asyncio.run(run())


@playbook.command("export")
@click.argument("playbook_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output JSON file path")
def playbook_export(playbook_path: str, output: str | None) -> None:
    """Export playbook to JSON for sharing"""
    from ignition_toolkit.playbook.loader import PlaybookLoader
    from ignition_toolkit.playbook.exporter import PlaybookExporter
    from pathlib import Path

    # Load playbook
    loader = PlaybookLoader()
    playbook = loader.load_from_file(Path(playbook_path))

    # Export to JSON
    exporter = PlaybookExporter()
    json_data = exporter.export(playbook)

    # Determine output path
    if output is None:
        output = str(Path(playbook_path).with_suffix(".json"))

    Path(output).write_text(json_data)

    console.print(f"\n✅ Playbook exported to: [green]{output}[/green]")
    console.print(f"   Share this file with colleagues\n")


@playbook.command("import")
@click.argument("json_path", type=click.Path(exists=True))
@click.option("--output-dir", default="./playbooks/imported", help="Output directory")
def playbook_import(json_path: str, output_dir: str) -> None:
    """Import playbook from JSON"""
    from ignition_toolkit.playbook.exporter import PlaybookExporter
    from pathlib import Path

    # Import from JSON
    exporter = PlaybookExporter()
    playbook = exporter.import_from_json(Path(json_path).read_text())

    # Save to YAML
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    yaml_path = output_path / f"{playbook.name.lower().replace(' ', '_')}.yaml"

    from ignition_toolkit.playbook.loader import PlaybookLoader
    loader = PlaybookLoader()
    loader.save_to_file(playbook, yaml_path)

    console.print(f"\n✅ Playbook imported to: [green]{yaml_path}[/green]")
    console.print(f"   Run with: [cyan]ignition-toolkit playbook run {yaml_path}[/cyan]\n")


if __name__ == "__main__":
    main()
