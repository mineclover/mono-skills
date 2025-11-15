"""Main CLI application for SubAgent Registry."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from registry_engine.database import get_db, init_db, SubAgentDB
from registry_engine.database.qdrant import QdrantDB
from registry_engine.models import SubAgentCreate, SubAgentMetadata
from registry_engine.search.indexer import SubAgentIndexer
from registry_engine.search.retriever import SubAgentRetriever

app = typer.Typer(help="SubAgent Registry CLI")
console = Console()


@app.command()
def import_yaml(
    file_path: Path = typer.Argument(..., help="Path to YAML file to import"),
    reindex: bool = typer.Option(True, help="Reindex after import"),
):
    """Import a subagent from a YAML file.

    Args:
        file_path: Path to YAML file
        reindex: Whether to reindex after import
    """
    if not file_path.exists():
        rprint(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    try:
        # Load YAML
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        # Validate and create SubAgent
        subagent_create = _yaml_to_subagent_create(data)

        # Initialize database
        init_db()
        db = get_db()
        session = db.get_session()

        try:
            subagent_db = SubAgentDB(session)

            # Check if already exists
            existing = subagent_db.get_by_name(subagent_create.metadata.name)
            if existing:
                rprint(
                    f"[yellow]Warning: SubAgent '{subagent_create.metadata.name}' already exists. Updating...[/yellow]"
                )
                subagent = subagent_db.update(subagent_create.metadata.name, subagent_create)
            else:
                subagent = subagent_db.create(subagent_create)

            rprint(f"[green]✓ Imported subagent: {subagent.name} (v{subagent.version})[/green]")

            # Reindex if requested
            if reindex:
                _reindex_subagent(subagent.id, session)

        finally:
            session.close()

    except Exception as e:
        rprint(f"[red]Error importing file: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_subagents(
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Filter by domain"),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of results"),
):
    """List all subagents.

    Args:
        domain: Filter by domain
        limit: Maximum number of results
    """
    init_db()
    db = get_db()
    session = db.get_session()

    try:
        subagent_db = SubAgentDB(session)
        subagents = subagent_db.list(domain=domain, limit=limit)

        if not subagents:
            rprint("[yellow]No subagents found[/yellow]")
            return

        # Create table
        table = Table(title="SubAgents")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Domain", style="magenta")
        table.add_column("Description", style="white")

        for subagent in subagents:
            table.add_row(
                subagent.name,
                subagent.version,
                subagent.domain,
                subagent.description[:60] + "..." if len(subagent.description) > 60 else subagent.description,
            )

        console.print(table)
        rprint(f"\n[blue]Total: {len(subagents)} subagent(s)[/blue]")

    finally:
        session.close()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Filter by domain"),
):
    """Search for subagents using natural language.

    Args:
        query: Search query
        top_k: Number of results to return
        domain: Filter by domain
    """
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        rprint("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
        raise typer.Exit(1)

    init_db()
    db = get_db()
    session = db.get_session()

    try:
        # Initialize Qdrant (in-memory for CLI)
        qdrant_db = QdrantDB(use_memory=True)

        # Reindex first (for CLI, we reindex on each search)
        indexer = SubAgentIndexer(qdrant_db)
        count = indexer.reindex_all(session)
        rprint(f"[blue]Indexed {count} subagent(s)[/blue]")

        # Search
        retriever = SubAgentRetriever(qdrant_db, session)
        results = retriever.search(query=query, top_k=top_k, domain=domain)

        if not results:
            rprint("[yellow]No results found[/yellow]")
            return

        # Display results
        table = Table(title=f"Search Results for: '{query}'")
        table.add_column("Rank", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Score", style="yellow")
        table.add_column("Domain", style="magenta")
        table.add_column("Description", style="white")

        for i, result in enumerate(results, 1):
            table.add_row(
                str(i),
                result["name"],
                f"{result.get('combined_score', result['score']):.3f}",
                result["domain"],
                result["description"][:50] + "..." if len(result["description"]) > 50 else result["description"],
            )

        console.print(table)

    finally:
        session.close()


@app.command()
def reindex():
    """Rebuild the entire vector index."""
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        rprint("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
        raise typer.Exit(1)

    init_db()
    db = get_db()
    session = db.get_session()

    try:
        # Initialize Qdrant
        qdrant_url = os.getenv("QDRANT_URL")
        if qdrant_url:
            qdrant_db = QdrantDB(url=qdrant_url, api_key=os.getenv("QDRANT_API_KEY"))
        else:
            rprint("[yellow]Warning: QDRANT_URL not set, using in-memory mode[/yellow]")
            qdrant_db = QdrantDB(use_memory=True)

        indexer = SubAgentIndexer(qdrant_db)
        count = indexer.reindex_all(session)

        rprint(f"[green]✓ Reindexed {count} subagent(s)[/green]")

    finally:
        session.close()


@app.command()
def validate(
    file_path: Path = typer.Argument(..., help="Path to YAML file to validate"),
):
    """Validate a YAML file without importing.

    Args:
        file_path: Path to YAML file
    """
    if not file_path.exists():
        rprint(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        # Try to create SubAgent model
        subagent_create = _yaml_to_subagent_create(data)

        rprint(f"[green]✓ Valid YAML file[/green]")
        rprint(f"  Name: {subagent_create.metadata.name}")
        rprint(f"  Version: {subagent_create.metadata.version}")
        rprint(f"  Domain: {subagent_create.metadata.domain}")

    except Exception as e:
        rprint(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(1)


def _yaml_to_subagent_create(data: dict) -> SubAgentCreate:
    """Convert YAML data to SubAgentCreate model.

    Args:
        data: YAML data dictionary

    Returns:
        SubAgentCreate model
    """
    from registry_engine.models import Installation, Activation, Example, Dependency

    # Parse metadata
    metadata_dict = data.get("metadata", {})
    metadata = SubAgentMetadata(**metadata_dict)

    # Parse installations
    installations = [
        Installation(**inst) for inst in data.get("installations", [])
    ]

    # Parse activations
    activations = [
        Activation(**act) for act in data.get("activations", [])
    ]

    # Parse examples
    examples = [
        Example(**ex) for ex in data.get("examples", [])
    ]

    # Parse dependencies
    dependencies = [
        Dependency(**dep) for dep in data.get("dependencies", [])
    ]

    return SubAgentCreate(
        metadata=metadata,
        prompts=data.get("prompts", []),
        interface=data.get("interface"),
        installations=installations,
        activations=activations,
        examples=examples,
        dependencies=dependencies,
    )


def _reindex_subagent(subagent_id: int, session):
    """Reindex a single subagent.

    Args:
        subagent_id: SubAgent database ID
        session: Database session
    """
    try:
        qdrant_url = os.getenv("QDRANT_URL")
        if qdrant_url:
            qdrant_db = QdrantDB(url=qdrant_url, api_key=os.getenv("QDRANT_API_KEY"))
            indexer = SubAgentIndexer(qdrant_db)

            subagent_db = SubAgentDB(session)
            subagent = subagent_db.get_by_id(subagent_id)
            if subagent:
                indexer.index_subagent(subagent)
                rprint("[blue]  ✓ Indexed in vector database[/blue]")
    except Exception as e:
        rprint(f"[yellow]Warning: Could not index in vector database: {e}[/yellow]")


if __name__ == "__main__":
    app()
