"""CLI interface for The Silent Cartographer."""

import asyncio
import shutil
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from tsc.config import get_settings
from tsc.parsers import parse_kindle_html, ParsedBook
from tsc.processors import route_highlights
from tsc.processors.concept_extractor import extract_concepts, ExtractedConcept
from tsc.processors.action_extractor import extract_actions, ExtractedAction
from tsc.generators.book_note import write_book_note
from tsc.generators.concept_note import write_concept_note
from tsc.generators.template_filler import fill_template
from tsc.integrations.asana_client import create_task
from tsc.integrations.email_client import send_notification, EmailClient
from tsc.integrations.semantic_search import SemanticSearch
from tsc.memory import MemoryTracker, ProcessedRecord, SpacedRepetitionEntry


# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

console = Console(force_terminal=True)


def _print_banner() -> None:
    """Print Halo-themed ASCII art banner."""
    width = shutil.get_terminal_size().columns

    if width >= 100:
        # Full large banner with filled block letters
        banner = """[bold cyan] ████████╗██╗  ██╗███████╗    ███████╗██╗██╗     ███████╗███╗   ██╗████████╗
 ╚══██╔══╝██║  ██║██╔════╝    ██╔════╝██║██║     ██╔════╝████╗  ██║╚══██╔══╝
    ██║   ███████║█████╗      ███████╗██║██║     █████╗  ██╔██╗ ██║   ██║
    ██║   ██╔══██║██╔══╝      ╚════██║██║██║     ██╔══╝  ██║╚██╗██║   ██║
    ██║   ██║  ██║███████╗    ███████║██║███████╗███████╗██║ ╚████║   ██║
    ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝

      ██████╗ █████╗ ██████╗ ████████╗ ██████╗  ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗███████╗██████╗
     ██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║██╔════╝██╔══██╗
     ██║     ███████║██████╔╝   ██║   ██║   ██║██║  ███╗██████╔╝███████║██████╔╝███████║█████╗  ██████╔╝
     ██║     ██╔══██║██╔══██╗   ██║   ██║   ██║██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗
     ╚██████╗██║  ██║██║  ██║   ██║   ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║███████╗██║  ██║
      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝[/bold cyan]"""
        console.print(banner)
        console.print()
        console.print("[dim cyan]                    ◇ ▽ ○ ◆ △ ● ◇ ▽ ○ ◆ △ ● ◇ ▽ ○ ◆ △ ● ◇[/dim cyan]")
        console.print("[bold white]                    Cartographic analysis pending Reclaimer directive[/bold white]")
    else:
        # Compact banner for narrow terminals
        console.print("[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
        console.print("[bold cyan]║[/bold cyan]      [bold white]THE SILENT CARTOGRAPHER[/bold white]           [bold cyan]║[/bold cyan]")
        console.print("[bold cyan]║[/bold cyan]  [dim cyan]◆━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◆[/dim cyan]   [bold cyan]║[/bold cyan]")
        console.print("[bold cyan]║[/bold cyan]    [white]Where knowledge hides, I reveal[/white]   [bold cyan]║[/bold cyan]")
        console.print("[bold cyan]╚════════════════════════════════════════╝[/bold cyan]")

    console.print()


def _load_profile() -> str:
    """Load user profile content."""
    settings = get_settings()
    try:
        return settings.tsc_profile_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        console.print("[yellow]Warning: profile.md not found, using empty profile[/yellow]")
        return ""


async def _process_single_book(
    file_path: Path,
    dry_run: bool = False,
    skip_email: bool = False,
    skip_asana: bool = False,
) -> Optional[ProcessedRecord]:
    """Process a single Kindle HTML export.

    Args:
        file_path: Path to HTML file.
        dry_run: If True, preview without writing.
        skip_email: Skip email notification.
        skip_asana: Skip Asana task creation.

    Returns:
        ProcessedRecord if successful, None otherwise.
    """
    settings = get_settings()
    tracker = MemoryTracker()

    # Check if already processed
    if tracker.is_processed(file_path.name):
        console.print(f"[yellow]Skipping (already processed): {file_path.name}[/yellow]")
        return None

    console.print(f"\n[bold blue]Processing:[/bold blue] {file_path.name}")

    # Parse the HTML
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Parsing HTML...", total=None)
        book = parse_kindle_html(file_path)
        progress.update(task, description="✓ Parsed HTML")

    counts = book.highlight_counts()
    console.print(f"  Found {sum(counts.values())} highlights:")
    console.print(f"    🟡 Yellow (concepts): {counts['yellow']}")
    console.print(f"    🩷 Pink (actions): {counts['pink']}")
    console.print(f"    🔵 Blue (quotes): {counts['blue']}")
    console.print(f"    🟠 Orange (disagreements): {counts['orange']}")

    # Route highlights
    routed = route_highlights(book)

    # Load profile and existing notes
    profile = _load_profile()
    search = SemanticSearch()
    existing_notes = search.get_all_note_titles()

    # Extract concepts from yellow highlights
    concepts: list[ExtractedConcept] = []
    if routed.concepts:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting concepts...", total=None)
            concepts = await extract_concepts(
                routed.concepts,
                book.metadata,
                profile,
            )
            progress.update(task, description=f"✓ Extracted {len(concepts)} concepts")

    # Extract actions from pink highlights
    actions: list[ExtractedAction] = []
    if routed.actions:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting actions...", total=None)
            actions = await extract_actions(
                routed.actions,
                book.metadata,
                profile,
            )
            progress.update(task, description=f"✓ Extracted {len(actions)} actions")

    if dry_run:
        console.print("\n[yellow][DRY RUN] Would create:[/yellow]")
        console.print(f"  Book note: {book.metadata.title}.md")
        for c in concepts:
            console.print(f"  Concept note: {c.name}.md")
        for a in actions:
            console.print(f"  Asana task: {a.title}")
        return None

    # Create Asana tasks
    asana_urls: dict[str, str] = {}
    if actions and not skip_asana:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating Asana tasks...", total=None)
            for action in actions:
                # Get the source highlight text
                highlight_text = ""
                if action.source_highlight < len(routed.actions):
                    highlight_text = routed.actions[action.source_highlight].text
                url = await create_task(action, book.metadata, highlight_text)
                if url:
                    asana_urls[action.title] = url
            progress.update(task, description=f"✓ Created {len(asana_urls)} Asana tasks")

    # Generate concept notes
    concept_names: list[str] = []
    if concepts:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating concept notes...", total=len(concepts))
            for i, concept in enumerate(concepts):
                progress.update(task, description=f"Generating: {concept.name}")

                # Fill template
                filled = await fill_template(
                    concept,
                    routed.concepts,
                    book.metadata,
                    profile,
                    existing_notes,
                )

                # Get supporting highlights by index
                supporting = [
                    routed.concepts[i] for i in concept.supporting_highlights
                    if i < len(routed.concepts)
                ]

                # Write note
                note_path = write_concept_note(
                    concept,
                    filled,
                    book.metadata,
                    settings.ideas_dir,
                    supporting,
                )
                concept_names.append(concept.name)

                # Add to spaced repetition
                tracker.add_spaced_repetition_entry(SpacedRepetitionEntry(
                    concept_name=concept.name,
                    concept_path=str(note_path),
                    source_book=book.metadata.title,
                ))

                progress.advance(task)

            progress.update(task, description=f"✓ Generated {len(concepts)} concept notes")

    # Generate book note
    book_note_path = write_book_note(
        book,
        concepts,
        actions,
        settings.books_dir,
        asana_urls,
    )
    console.print(f"[green]✓ Created book note:[/green] {book_note_path.name}")

    # Create processing record
    record = ProcessedRecord(
        source_file=file_path.name,
        book_title=book.metadata.title,
        book_author=book.metadata.author,
        highlight_counts=counts,
        concepts_created=concept_names,
        actions_created=[a.title for a in actions],
        book_note_path=str(book_note_path),
    )

    # Save to memory
    tracker.add_processed_record(record)

    # Move processed file
    processed_path = settings.processed_dir / file_path.name
    shutil.move(str(file_path), str(processed_path))
    console.print(f"[dim]Moved to: {processed_path}[/dim]")

    # Send email notification
    if not skip_email:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Sending notification...", total=None)
            success = await send_notification(book, concepts, actions, asana_urls)
            if success:
                progress.update(task, description="✓ Email sent")
            else:
                progress.update(task, description="[yellow]Email skipped (not configured)[/yellow]")

    return record


@click.group()
@click.version_option(version="0.1.0", prog_name="The Silent Cartographer")
def main():
    """The Silent Cartographer - Transform Kindle highlights into knowledge."""
    pass


@main.command()
@click.option("--file", "-f", "file_path", type=click.Path(exists=True, path_type=Path),
              help="Process specific HTML file")
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
@click.option("--skip-email", is_flag=True, help="Skip email notification")
@click.option("--skip-asana", is_flag=True, help="Skip Asana task creation")
def process(
    file_path: Optional[Path],
    dry_run: bool,
    skip_email: bool,
    skip_asana: bool,
):
    """Process Kindle HTML exports into Obsidian notes."""
    settings = get_settings()

    _print_banner()

    if file_path:
        files = [file_path]
    else:
        # Find all HTML files in Kindle directory
        files = list(settings.tsc_kindle_dir.glob("*.html"))
        if not files:
            console.print("[yellow]No HTML files found in Kindle directory[/yellow]")
            console.print(f"  Looking in: {settings.tsc_kindle_dir}")
            return

    console.print(f"Found {len(files)} file(s) to process")

    # Process each file
    records = []
    for f in files:
        try:
            record = asyncio.run(_process_single_book(
                f,
                dry_run=dry_run,
                skip_email=skip_email,
                skip_asana=skip_asana,
            ))
            if record:
                records.append(record)
        except Exception as e:
            console.print(f"[red]Error processing {f.name}: {e}[/red]")
            import traceback
            if console.is_terminal:
                console.print(traceback.format_exc())

    # Summary
    if records and not dry_run:
        console.print(Panel.fit(
            f"[green]✓ Processed {len(records)} book(s)[/green]\n"
            f"Concepts: {sum(len(r.concepts_created) for r in records)}\n"
            f"Actions: {sum(len(r.actions_created) for r in records)}",
            title="Summary",
            border_style="green",
        ))


@main.command()
@click.option("--type", "-t", "digest_type",
              type=click.Choice(["weekly", "monthly", "spaced"]),
              default="weekly",
              help="Type of digest to send")
@click.option("--dry-run", is_flag=True, help="Preview email content")
def digest(digest_type: str, dry_run: bool):
    """Send summary digests and reminders."""
    tracker = MemoryTracker()
    stats = tracker.get_stats()

    if digest_type == "spaced":
        # Spaced repetition reminders
        due = tracker.get_due_reviews()
        if not due:
            console.print("[green]No concepts due for review![/green]")
            return

        console.print(f"[bold]Concepts due for review: {len(due)}[/bold]\n")

        table = Table(title="Spaced Repetition Review")
        table.add_column("Concept", style="cyan")
        table.add_column("Source", style="dim")
        table.add_column("Reviews", justify="right")

        for entry in due:
            table.add_row(
                entry.concept_name,
                entry.source_book,
                str(entry.review_count),
            )

        console.print(table)

        if not dry_run:
            # Send email with due reviews
            try:
                client = EmailClient()
                concepts_list = "\n".join(
                    f"- {e.concept_name} (from \"{e.source_book}\")"
                    for e in due
                )
                html = f"""
                <html><body style="font-family: sans-serif;">
                <h1>📚 Concepts Due for Review</h1>
                <p>You have {len(due)} concepts ready for spaced repetition review:</p>
                <ul>
                {"".join(f'<li><strong>{e.concept_name}</strong> — from "{e.source_book}"</li>' for e in due)}
                </ul>
                <p>Open Obsidian and review these concepts to strengthen your retention!</p>
                </body></html>
                """
                client.send(f"📚 TSC: {len(due)} Concepts Due for Review", html)
                console.print("[green]✓ Reminder email sent[/green]")
            except ValueError:
                console.print("[yellow]Email not configured[/yellow]")

    elif digest_type == "weekly":
        # Weekly summary
        recent = tracker.get_recent_books(limit=7)

        console.print("[bold]Weekly Summary[/bold]\n")
        console.print(f"Books processed: {len(recent)}")
        console.print(f"Total concepts: {stats['concepts_created']}")
        console.print(f"Total actions: {stats['actions_created']}")
        console.print(f"Pending reviews: {stats['pending_reviews']}")

        if recent:
            console.print("\n[bold]Recent Books:[/bold]")
            for r in recent:
                console.print(f"  • {r.book_title} by {r.book_author}")

    elif digest_type == "monthly":
        # Monthly analytics
        console.print("[bold]Monthly Analytics[/bold]\n")

        table = Table(title="Knowledge Growth")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Books Processed", str(stats['books_processed']))
        table.add_row("Total Highlights", str(stats['total_highlights']))
        table.add_row("Concepts Created", str(stats['concepts_created']))
        table.add_row("Actions Created", str(stats['actions_created']))
        table.add_row("In Spaced Repetition", str(stats['total_in_rotation']))
        table.add_row("Pending Reviews", str(stats['pending_reviews']))

        console.print(table)


@main.command()
@click.option("--format", "-f", "output_format",
              type=click.Choice(["table", "json"]),
              default="table",
              help="Output format")
def dashboard(output_format: str):
    """Show statistics and status dashboard."""
    tracker = MemoryTracker()
    stats = tracker.get_stats()

    if output_format == "json":
        import json
        console.print(json.dumps(stats, indent=2))
        return

    _print_banner()

    # Stats table
    table = Table(title="Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("📚 Books Processed", str(stats['books_processed']))
    table.add_row("📝 Total Highlights", str(stats['total_highlights']))
    table.add_row("💡 Concepts Created", str(stats['concepts_created']))
    table.add_row("✅ Actions Created", str(stats['actions_created']))
    table.add_row("🔄 In Spaced Repetition", str(stats['total_in_rotation']))
    table.add_row("⏰ Pending Reviews", str(stats['pending_reviews']))

    console.print(table)

    # Recent books
    recent = tracker.get_recent_books(limit=5)
    if recent:
        console.print("\n[bold]Recent Books:[/bold]")
        for r in recent:
            console.print(f"  • {r.book_title}")
            console.print(f"    [dim]{r.processed_at.strftime('%Y-%m-%d')} | "
                         f"{len(r.concepts_created)} concepts, "
                         f"{len(r.actions_created)} actions[/dim]")


if __name__ == "__main__":
    main()
