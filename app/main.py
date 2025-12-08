#!/usr/bin/env python3
"""
Misanthrope PM - Advanced Project Management Analytics with Git Integration
"""

import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.tree import Tree
from rich import print as rprint

from misanthrope_pm.core.context import PMContext
from misanthrope_pm.core.project_manager import ProjectManager
from misanthrope_pm.analytics.predictor import TaskPredictor
from misanthrope_pm.analytics.contributor_analyzer import ContributorAnalyzer
from misanthrope_pm.reports.generator import ReportGenerator

# Initialize Typer app
app = typer.Typer(
    name="misanthrope-pm",
    help="Advanced Project Management Analytics with Git Integration",
    no_args_is_help=True,
    add_completion=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()
error_console = Console(stderr=True, style="bold red")


@app.command("add")
def add_project(
        project_path: Path = typer.Argument(
            ...,
            help="Path to git repository",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
        project_name: Optional[str] = typer.Option(
            None,
            "--name", "-n",
            help="Project name (default: directory name)",
        ),
        force: bool = typer.Option(
            False,
            "--force", "-f",
            help="Overwrite existing project data",
        ),
        fetch_git: bool = typer.Option(
            True,
            "--fetch-git/--no-fetch-git",
            help="Fetch git logs automatically",
        ),
        analyze_immediately: bool = typer.Option(
            True,
            "--analyze/--no-analyze",
            help="Run initial analysis after adding",
        ),
):
    """
    Add a new git project for analysis.

    Creates project folder in data directory and fetches git history.

    Examples:

    \b
    $ misanthrope-pm add ~/projects/my-repo
    $ misanthrope-pm add ~/projects/my-repo --name awesome-project --force
    $ misanthrope-pm add . --no-analyze
    """
    try:
        # Determine project name
        if not project_name:
            project_name = project_path.name

        project_manager = ProjectManager()

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=True,
        ) as progress:
            # Task 1: Initialize project
            task1 = progress.add_task(
                description=f"Initializing project '{project_name}'...",
                total=100
            )

            project = project_manager.add_project(
                name=project_name,
                repo_path=project_path,
                force=force
            )
            progress.update(task1, completed=100)

            # Task 2: Fetch git logs
            if fetch_git:
                task2 = progress.add_task(
                    description="Fetching git history...",
                    total=100
                )

                git_stats = project_manager.fetch_git_logs(project.name)
                progress.update(task2, completed=100)

                # Task 3: Extract git metadata
                task3 = progress.add_task(
                    description="Analyzing repository structure...",
                    total=100
                )

                metadata = project_manager.extract_repo_metadata(project.name)
                progress.update(task3, completed=100)

            # Task 4: Initial analysis
            if analyze_immediately:
                task4 = progress.add_task(
                    description="Running initial analysis...",
                    total=100
                )

                analysis = project_manager.analyze_project(project.name)
                progress.update(task4, completed=100)

        # Show results
        console.print(Panel.fit(
            f"[bold green]✓ Project '{project_name}' added successfully![/bold green]\n\n"
            f"[cyan]Project ID:[/cyan] {project.id}\n"
            f"[cyan]Repository:[/cyan] {project.repo_path}\n"
            f"[cyan]Data Path:[/cyan] {project.data_path}\n"
            f"[cyan]Created:[/cyan] {project.created_at}\n",
            title="[bold]Project Added[/bold]",
            border_style="green"
        ))

        if fetch_git:
            console.print(Panel.fit(
                f"[cyan]Commits:[/cyan] {git_stats['total_commits']}\n"
                f"[cyan]Contributors:[/cyan] {git_stats['contributors']}\n"
                f"[cyan]Date Range:[/cyan] {git_stats['date_range']}\n"
                f"[cyan]Total Changes:[/cyan] +{git_stats['total_insertions']}/-{git_stats['total_deletions']}",
                title="[bold]Git Statistics[/bold]",
                border_style="cyan"
            ))

        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  $ misanthrope-pm analyze {project.name}")
        console.print(f"  $ misanthrope-pm stats {project.name}")
        console.print(f"  $ misanthrope-pm predict {project.name}")

    except Exception as e:
        error_console.print(f"Error adding project: {e}")
        raise typer.Exit(code=1)


@app.command("analyze")
def analyze_project(
        project_name: str = typer.Argument(
            ...,
            help="Project name to analyze"
        ),
        period: Optional[str] = typer.Option(
            None,
            "--period", "-p",
            help="Analysis period (e.g., '30d', '3m', '1y')",
        ),
        detailed: bool = typer.Option(
            False,
            "--detailed", "-d",
            help="Show detailed analysis",
        ),
        output_format: str = typer.Option(
            "text",
            "--format", "-f",
            help="Output format",
            case_sensitive=False,
        ),
        output_file: Optional[Path] = typer.Option(
            None,
            "--output", "-o",
            help="Output file",
        ),
):
    """
    Analyze project metrics and generate insights.

    Examples:

    \b
    $ misanthrope-pm analyze my-project
    $ misanthrope-pm analyze my-project --period 30d --detailed
    $ misanthrope-pm analyze my-project --format json --output analysis.json
    """
    try:
        project_manager = ProjectManager()

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=True,
        ) as progress:
            # Task 1: Load project
            task1 = progress.add_task(
                description=f"Loading project '{project_name}'...",
                total=100
            )

            project = project_manager.get_project(project_name)
            context = PMContext(project.data_path)
            progress.update(task1, completed=100)

            # Task 2: Analyze project
            task2 = progress.add_task(
                description="Analyzing project metrics...",
                total=100
            )

            # Calculate date range if period specified
            from_date = None
            if period:
                from_date = _parse_period_to_date(period)

            analysis = project_manager.analyze_project(
                project_name,
                from_date=from_date,
                detailed=detailed
            )
            progress.update(task2, completed=100)

            # Task 3: Generate output
            task3 = progress.add_task(
                description="Generating output...",
                total=100
            )

            if output_format.lower() == "json":
                output = json.dumps(analysis, indent=2, default=str)
            else:
                output = _format_analysis_text(analysis, detailed)

            progress.update(task3, completed=100)

        # Output results
        if output_file:
            output_file.write_text(output)
            console.print(f"[green]✓[/green] Analysis saved to {output_file}")
        else:
            console.print(output)

    except Exception as e:
        error_console.print(f"Error analyzing project: {e}")
        raise typer.Exit(code=1)


@app.command("predict")
def predict_tasks(
        project_name: str = typer.Argument(
            ...,
            help="Project name"
        ),
        task_description: Optional[str] = typer.Option(
            None,
            "--task", "-t",
            help="Task description to predict",
        ),
        input_file: Optional[Path] = typer.Option(
            None,
            "--input", "-i",
            help="File with task descriptions (one per line)",
        ),
        output_format: str = typer.Option(
            "text",
            "--format", "-f",
            help="Output format",
        ),
):
    """
    Predict time estimates and complexity for tasks based on git history.

    Examples:

    \b
    $ misanthrope-pm predict my-project
    $ misanthrope-pm predict my-project --task "Fix login bug"
    $ misanthrope-pm predict my-project --input tasks.txt --format json
    """
    try:
        project_manager = ProjectManager()
        project = project_manager.get_project(project_name)

        predictor = TaskPredictor(project.data_path)

        # Prepare tasks for prediction
        tasks_to_predict = []

        if task_description:
            tasks_to_predict.append(task_description)
        elif input_file:
            if input_file.exists():
                tasks_to_predict = input_file.read_text().splitlines()
            else:
                error_console.print(f"Input file not found: {input_file}")
                raise typer.Exit(code=1)
        else:
            # Predict for existing tasks in project
            context = PMContext(project.data_path)
            tasks_to_predict = [task.text for task in context.closed_tasks[:10]]  # First 10 tasks

        if not tasks_to_predict:
            error_console.print("No tasks to predict")
            raise typer.Exit(code=1)

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
        ) as progress:
            task = progress.add_task(
                description="Training prediction model...",
                total=None
            )

            predictions = predictor.predict_tasks(tasks_to_predict)

            progress.update(task, completed=100)

        # Format output
        if output_format.lower() == "json":
            output = json.dumps(predictions, indent=2, default=str)
        else:
            output = _format_predictions_text(predictions)

        console.print(output)

    except Exception as e:
        error_console.print(f"Error predicting tasks: {e}")
        raise typer.Exit(code=1)


@app.command("contributors")
def show_contributors(
        project_name: str = typer.Argument(
            ...,
            help="Project name"
        ),
        period: Optional[str] = typer.Option(
            None,
            "--period", "-p",
            help="Time period to analyze (e.g., '30d', '3m')",
        ),
        top: Optional[int] = typer.Option(
            10,
            "--top", "-t",
            help="Show top N contributors",
        ),
        detailed: bool = typer.Option(
            False,
            "--detailed", "-d",
            help="Show detailed contributor stats",
        ),
):
    """
    Show contributor statistics and activity.

    Examples:

    \b
    $ misanthrope-pm contributors my-project
    $ misanthrope-pm contributors my-project --period 30d --top 5
    $ misanthrope-pm contributors my-project --detailed
    """
    try:
        project_manager = ProjectManager()
        project = project_manager.get_project(project_name)

        analyzer = ContributorAnalyzer(project.data_path)

        # Calculate date range if period specified
        from_date = None
        if period:
            from_date = _parse_period_to_date(period)

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
        ) as progress:
            task = progress.add_task(
                description="Analyzing contributors...",
                total=None
            )

            contributors = analyzer.analyze_contributors(
                from_date=from_date,
                top_n=top,
                detailed=detailed
            )

            progress.update(task, completed=100)

        # Format output
        if detailed:
            output = _format_contributors_detailed(contributors)
        else:
            output = _format_contributors_summary(contributors)

        console.print(output)

    except Exception as e:
        error_console.print(f"Error analyzing contributors: {e}")
        raise typer.Exit(code=1)


@app.command("stats")
def show_statistics(
        project_name: Optional[str] = typer.Argument(
            None,
            help="Project name (optional, shows all projects if omitted)"
        ),
        compare: bool = typer.Option(
            False,
            "--compare", "-c",
            help="Compare multiple projects",
        ),
        export: Optional[Path] = typer.Option(
            None,
            "--export", "-e",
            help="Export statistics to file",
        ),
):
    """
    Show project statistics and metrics.

    Examples:

    \b
    $ misanthrope-pm stats
    $ misanthrope-pm stats my-project
    $ misanthrope-pm stats --compare --export stats.csv
    """
    try:
        project_manager = ProjectManager()

        if project_name:
            # Show single project stats
            project = project_manager.get_project(project_name)
            context = PMContext(project.data_path)

            stats = {
                "project": project.name,
                "summary": context.get_summary(),
                "git_stats": project_manager.get_git_statistics(project.name),
                "daily_stats": context.get_daily_stats().to_dict(orient="records")
                if not context.daily_stats.empty else []
            }

            output = _format_single_project_stats(stats)

        else:
            # Show all projects
            projects = project_manager.list_projects()

            if compare:
                output = _format_compare_projects(projects, project_manager)
            else:
                output = _format_all_projects_list(projects)

        # Export if requested
        if export:
            if export.suffix == '.json':
                export.write_text(json.dumps(stats if project_name else projects, indent=2, default=str))
            elif export.suffix == '.csv':
                # Convert to CSV
                import pandas as pd
                df = pd.DataFrame([{
                    "project": p.name,
                    "created": p.created_at,
                    "commits": project_manager.get_git_statistics(p.name).get("total_commits", 0)
                } for p in projects])
                df.to_csv(export, index=False)
            console.print(f"[green]✓[/green] Statistics exported to {export}")

        console.print(output)

    except Exception as e:
        error_console.print(f"Error showing statistics: {e}")
        raise typer.Exit(code=1)


@app.command("report")
def generate_report(
        project_name: str = typer.Argument(
            ...,
            help="Project name"
        ),
        report_type: str = typer.Option(
            "weekly",
            "--type", "-t",
            help="Report type",
            case_sensitive=False,
        ),
        output_dir: Path = typer.Option(
            "./reports",
            "--output", "-o",
            help="Output directory",
            file_okay=False,
            dir_okay=True,
        ),
        template: Optional[str] = typer.Option(
            None,
            "--template",
            help="Custom report template name",
        ),
):
    """
    Generate professional reports for stakeholders.

    Examples:

    \b
    $ misanthrope-pm report my-project
    $ misanthrope-pm report my-project --type monthly --output ./my-reports
    $ misanthrope-pm report my-project --template executive
    """
    try:
        project_manager = ProjectManager()
        project = project_manager.get_project(project_name)

        generator = ReportGenerator(project.data_path)

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=True,
        ) as progress:
            task = progress.add_task(
                description=f"Generating {report_type} report...",
                total=100
            )

            report_path = generator.generate_report(
                report_type=report_type,
                output_dir=output_dir,
                template_name=template
            )

            progress.update(task, completed=100)

        console.print(Panel.fit(
            f"[bold green]✓ Report generated successfully![/bold green]\n\n"
            f"[cyan]Project:[/cyan] {project_name}\n"
            f"[cyan]Report Type:[/cyan] {report_type}\n"
            f"[cyan]Output File:[/cyan] {report_path}\n",
            title="[bold]Report Generated[/bold]",
            border_style="green"
        ))

        # Try to open the report
        try:
            if report_path.suffix == '.html':
                console.print("\n[cyan]Opening report in browser...[/cyan]")
                import webbrowser
                webbrowser.open(f"file://{report_path.absolute()}")
        except:
            pass

    except Exception as e:
        error_console.print(f"Error generating report: {e}")
        raise typer.Exit(code=1)


@app.command("update")
def update_project(
        project_name: str = typer.Argument(
            ...,
            help="Project name to update"
        ),
        fetch_git: bool = typer.Option(
            True,
            "--git/--no-git",
            help="Update git logs",
        ),
        force: bool = typer.Option(
            False,
            "--force", "-f",
            help="Force update even if no changes",
        ),
):
    """
    Update project data with latest information.

    Examples:

    \b
    $ misanthrope-pm update my-project
    $ misanthrope-pm update my-project --no-git
    """
    try:
        project_manager = ProjectManager()

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
        ) as progress:
            task = progress.add_task(
                description=f"Updating project '{project_name}'...",
                total=None
            )

            updated = project_manager.update_project(
                project_name,
                fetch_git=fetch_git,
                force=force
            )

            progress.update(task, completed=100)

        if updated:
            console.print(f"[green]✓[/green] Project '{project_name}' updated successfully")
        else:
            console.print(f"[yellow]⚠[/yellow] No updates needed for '{project_name}'")

    except Exception as e:
        error_console.print(f"Error updating project: {e}")
        raise typer.Exit(code=1)


@app.command("remove")
def remove_project(
        project_name: str = typer.Argument(
            ...,
            help="Project name to remove"
        ),
        keep_data: bool = typer.Option(
            False,
            "--keep-data", "-k",
            help="Keep project data files",
        ),
        confirm: bool = typer.Option(
            False,
            "--yes", "-y",
            help="Skip confirmation prompt",
        ),
):
    """
    Remove a project from analysis.

    Examples:

    \b
    $ misanthrope-pm remove old-project
    $ misanthrope-pm remove old-project --keep-data --yes
    """
    try:
        if not confirm:
            console.print(f"[yellow]⚠[/yellow] Are you sure you want to remove project '{project_name}'?")
            if not typer.confirm("Continue?"):
                console.print("[yellow]Removal cancelled[/yellow]")
                return

        project_manager = ProjectManager()

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
        ) as progress:
            task = progress.add_task(
                description=f"Removing project '{project_name}'...",
                total=None
            )

            project_manager.remove_project(project_name, keep_data=keep_data)

            progress.update(task, completed=100)

        console.print(f"[green]✓[/green] Project '{project_name}' removed successfully")

    except Exception as e:
        error_console.print(f"Error removing project: {e}")
        raise typer.Exit(code=1)


@app.command("list")
def list_projects(
        detailed: bool = typer.Option(
            False,
            "--detailed", "-d",
            help="Show detailed project information",
        ),
        sort_by: str = typer.Option(
            "name",
            "--sort",
            help="Sort projects by (name, created, size, activity)",
            case_sensitive=False,
        ),
):
    """
    List all tracked projects.

    Examples:

    \b
    $ misanthrope-pm list
    $ misanthrope-pm list --detailed --sort activity
    """
    try:
        project_manager = ProjectManager()
        projects = project_manager.list_projects()

        if not projects:
            console.print("[yellow]No projects found. Use 'misanthrope-pm add' to add a project.[/yellow]")
            return

        if detailed:
            output = _format_projects_detailed(projects, project_manager, sort_by)
        else:
            output = _format_projects_simple(projects, sort_by)

        console.print(output)

    except Exception as e:
        error_console.print(f"Error listing projects: {e}")
        raise typer.Exit(code=1)


def _parse_period_to_date(period: str) -> date:
    """Parse period string like '30d', '3m', '1y' to date"""
    today = date.today()

    if period.endswith('d'):
        days = int(period[:-1])
        return today - timedelta(days=days)
    elif period.endswith('w'):
        weeks = int(period[:-1])
        return today - timedelta(weeks=weeks)
    elif period.endswith('m'):
        months = int(period[:-1])
        # Approximate months
        return today - timedelta(days=months * 30)
    elif period.endswith('y'):
        years = int(period[:-1])
        return today - timedelta(days=years * 365)
    else:
        try:
            return datetime.strptime(period, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid period format: {period}")


def _format_analysis_text(analysis: Dict[str, Any], detailed: bool) -> str:
    """Format analysis results as text"""
    panels = []

    # Summary panel
    summary_panel = Panel.fit(
        f"[bold cyan]Project:[/bold cyan] {analysis.get('project_name', 'N/A')}\n"
        f"[bold cyan]Period:[/bold cyan] {analysis.get('period_start', 'N/A')} to {analysis.get('period_end', 'N/A')}\n"
        f"[bold cyan]Total Commits:[/bold cyan] {analysis.get('total_commits', 0)}\n"
        f"[bold cyan]Total Tasks:[/bold cyan] {analysis.get('total_tasks', 0)}\n"
        f"[bold cyan]Contributors:[/bold cyan] {analysis.get('contributors_count', 0)}\n"
        f"[bold cyan]Productivity Score:[/bold cyan] {analysis.get('productivity_score', 0):.2f}",
        title="[bold]Project Analysis Summary[/bold]",
        border_style="cyan"
    )
    panels.append(summary_panel)

    # Task categories table
    categories = analysis.get('task_categories', {})
    if categories:
        cat_table = Table(title="Task Categories", show_header=True)
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Count", style="green")
        cat_table.add_column("Percentage", style="yellow")

        total = sum(categories.values())
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            cat_table.add_row(cat, str(count), f"{percentage:.1f}%")

        panels.append(str(cat_table))

    # Daily activity (last 7 days)
    daily_stats = analysis.get('daily_stats', [])
    if daily_stats and len(daily_stats) > 0:
        recent_days = daily_stats[-7:] if len(daily_stats) > 7 else daily_stats

        daily_table = Table(title="Recent Activity (Last 7 Days)", show_header=True)
        daily_table.add_column("Date", style="cyan")
        daily_table.add_column("Commits", style="green")
        daily_table.add_column("Changes (+/-)", style="yellow")
        daily_table.add_column("Net", style="magenta")

        for day in recent_days:
            net = day.get('insertions', 0) - day.get('deletions', 0)
            daily_table.add_row(
                str(day.get('day', '')),
                str(day.get('commits', 0)),
                f"+{day.get('insertions', 0)}/-{day.get('deletions', 0)}",
                f"{net:+d}"
            )

        panels.append(str(daily_table))

    # Detailed information if requested
    if detailed:
        # Top contributors
        contributors = analysis.get('top_contributors', [])
        if contributors:
            contrib_table = Table(title="Top Contributors", show_header=True)
            contrib_table.add_column("Rank", style="cyan")
            contrib_table.add_column("Name", style="green")
            contrib_table.add_column("Commits", style="yellow")
            contrib_table.add_column("Changes", style="magenta")

            for i, contrib in enumerate(contributors[:10], 1):
                changes = contrib.get('insertions', 0) + contrib.get('deletions', 0)
                contrib_table.add_row(
                    str(i),
                    contrib.get('author', 'Unknown'),
                    str(contrib.get('commits', 0)),
                    f"{changes:,}"
                )

            panels.append(str(contrib_table))

        # Code metrics
        metrics = analysis.get('code_metrics', {})
        if metrics:
            metrics_panel = Panel.fit(
                f"[cyan]Avg Commits/Day:[/cyan] {metrics.get('avg_commits_per_day', 0):.1f}\n"
                f"[cyan]Avg Changes/Commit:[/cyan] {metrics.get('avg_changes_per_commit', 0):.1f}\n"
                f"[cyan]Bus Factor:[/cyan] {metrics.get('bus_factor', 0):.1f}\n"
                f"[cyan]Active Days:[/cyan] {metrics.get('active_days', 0)}",
                title="[bold]Code Metrics[/bold]",
                border_style="blue"
            )
            panels.append(str(metrics_panel))

    return "\n\n".join(panels)


def _format_predictions_text(predictions: List[Dict[str, Any]]) -> str:
    """Format task predictions as text"""
    if not predictions:
        return "[yellow]No predictions available[/yellow]"

    table = Table(title="Task Predictions", show_header=True)
    table.add_column("Task", style="cyan", no_wrap=False)
    table.add_column("Est. Hours", style="green")
    table.add_column("Complexity", style="yellow")
    table.add_column("Confidence", style="magenta")
    table.add_column("Category", style="blue")

    for pred in predictions:
        task_text = pred.get('task', '')[:50] + "..." if len(pred.get('task', '')) > 50 else pred.get('task', '')
        table.add_row(
            task_text,
            f"{pred.get('estimated_hours', 0):.1f}",
            pred.get('complexity', 'Medium'),
            f"{pred.get('confidence', 0):.0%}",
            pred.get('predicted_category', 'Unknown')
        )

    return str(table)


def _format_contributors_summary(contributors: List[Dict[str, Any]]) -> str:
    """Format contributor summary"""
    table = Table(title="Contributors Summary", show_header=True)
    table.add_column("Rank", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Commits", style="yellow")
    table.add_column("Insertions", style="green")
    table.add_column("Deletions", style="red")
    table.add_column("Net", style="magenta")
    table.add_column("Activity %", style="blue")

    total_commits = sum(c.get('commits', 0) for c in contributors)

    for i, contrib in enumerate(contributors, 1):
        activity_pct = (contrib.get('commits', 0) / total_commits * 100) if total_commits > 0 else 0
        net = contrib.get('insertions', 0) - contrib.get('deletions', 0)

        table.add_row(
            str(i),
            contrib.get('author', 'Unknown'),
            str(contrib.get('commits', 0)),
            str(contrib.get('insertions', 0)),
            str(contrib.get('deletions', 0)),
            f"{net:+d}",
            f"{activity_pct:.1f}%"
        )

    return str(table)


def _format_contributors_detailed(contributors: List[Dict[str, Any]]) -> str:
    """Format detailed contributor information"""
    panels = []

    for i, contrib in enumerate(contributors[:5], 1):  # Top 5
        panel = Panel.fit(
            f"[bold cyan]Rank {i}: {contrib.get('author', 'Unknown')}[/bold cyan]\n\n"
            f"[green]Commits:[/green] {contrib.get('commits', 0)}\n"
            f"[green]Insertions:[/green] +{contrib.get('insertions', 0):,}\n"
            f"[red]Deletions:[/red] -{contrib.get('deletions', 0):,}\n"
            f"[magenta]Net Changes:[/magenta] {contrib.get('insertions', 0) - contrib.get('deletions', 0):+d}\n"
            f"[yellow]First Commit:[/yellow] {contrib.get('first_commit', 'N/A')}\n"
            f"[yellow]Last Commit:[/yellow] {contrib.get('last_commit', 'N/A')}\n"
            f"[blue]Active Days:[/blue] {contrib.get('active_days', 0)}\n"
            f"[blue]Avg Commits/Day:[/blue] {contrib.get('avg_commits_per_day', 0):.2f}",
            title=f"[bold]Contributor Details[/bold]",
            border_style="cyan" if i == 1 else "green" if i == 2 else "yellow"
        )
        panels.append(str(panel))

    return "\n\n".join(panels)


def _format_single_project_stats(stats: Dict[str, Any]) -> str:
    """Format single project statistics"""
    project = stats.get('project', 'Unknown')
    summary = stats.get('summary', {})
    git_stats = stats.get('git_stats', {})

    panels = []

    # Project info panel
    info_panel = Panel.fit(
        f"[bold cyan]Project:[/bold cyan] {project}\n"
        f"[cyan]Created:[/cyan] {summary.get('date_range', {}).get('first_commit', 'N/A')}\n"
        f"[cyan]Last Activity:[/cyan] {summary.get('date_range', {}).get('last_commit', 'N/A')}",
        title="[bold]Project Information[/bold]",
        border_style="cyan"
    )
def _format_all_projects_list(projects: List[Any]) -> str:
    """Format
    panels.append(str(info_panel))

    # Git statistics panel
    git_panel = Panel.fit(
        f"[green]Total Commits:[/green] {git_stats.get('total_commits', 0)}\n"
        f"[green]Contributors:[/green] {git_stats.get('contributors', 0)}\n"
        f"[yellow]Total Insertions:[/yellow] +{git_stats.get('total_insertions', 0):,}\n"
        f"[red]Total Deletions:[/red] -{git_stats.get('total_deletions', 0):,}\n"
        f"[magenta]Net Changes:[/magenta] {git_stats.get('total_insertions', 0) - git_stats.get('total_deletions', 0):+d}",
        title="[bold]Git Statistics[/bold]",
        border_style="green"
    )
    panels.append(str(git_panel))

    # Task categories
    categories = summary.get('categories', {})
    if categories:
        cat_table = Table(title="Task Categories", show_header=True)
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Count", style="green")

        for cat, count in categories.items():
            cat_table.add_row(cat, str(count))

        panels.append(str(cat_table))

    return "\n\n".join(panels)

