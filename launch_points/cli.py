"""Command line interface for launch_points.

Provides `generate` and `validate` commands. Default data locations are used
so no file-location arguments are required for normal usage.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import webbrowser
from typing import List

import typer

from . import generator, validator

app = typer.Typer(help="Launch Points CLI")


def _default_marker_files() -> List[str]:
    return [
        "berlin/launch_with_transport.csv",
        "berlin/launch_without_transport.csv",
        "berlin/resting_points.csv",
    ]


@app.command()
def generate(
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and show actions but do not write files"),
    validate_before: bool = typer.Option(True, "--validate/--no-validate", help="Run data validation before generating"),
    open_after: bool = typer.Option(False, "--open", help="Open the generated index page in the default browser"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Generate map HTML from built-in project data files.

    Uses the standard `berlin/` data files by default. For now this command does
    not accept custom file locations (defaults are used).
    """
    markers = [(p, "launch_with_transport" if "with_transport" in p else ("resting_point" if "resting" in p else "launch_without_transport")) for p in _default_marker_files()]
    geojson = "berlin/routes.geojson"
    station_paths = "berlin/station_paths.geojson"
    transport_config = "berlin/transport_types.json"

    if validate_before:
        paths = _default_marker_files()
        res = validator.validate_all_marker_files(paths)
        problems = sum(len(v) for v in res.values())
        # Always show validation details when problems are found so users see errors directly
        if problems:
            typer.secho(f"Validation found {problems} issues:", fg=typer.colors.YELLOW)
            typer.echo(json.dumps(res, indent=2))
            # Provide human-friendly guidance for common issues
            typer.secho("\nSuggested fixes:", fg=typer.colors.CYAN)
            # Aggregate issue types
            issue_text = _explain_issues(res)
            typer.echo(issue_text)
            # Exit with a non-zero code after showing issues
            raise typer.Exit(code=2)

    if dry_run:
        typer.secho("Dry run: generation would run but files will not be written.", fg=typer.colors.BLUE)
        return

    # Perform generation and show any unexpected errors with full traceback
    try:
        generator.generate_map(markers, geojson, station_paths=station_paths, transport_config=transport_config)
        # Successful generation: report written files to the user
        typer.secho("Map generation complete. Files written to 'berlin/index.html' and 'berlin/editor.html'", fg=typer.colors.GREEN)
        if open_after:
            webbrowser.open("berlin/index.html")
    except Exception:
        import traceback

        typer.secho("Error during generation:", fg=typer.colors.RED)
        # Show a short human-friendly explanation and recommended next steps
        typer.secho("What happened:", fg=typer.colors.YELLOW)
        typer.echo("An unexpected error occurred while building the map. This can be caused by invalid input data (CSV/GeoJSON), missing files, or environment issues.")
        typer.secho("Suggested next steps:", fg=typer.colors.CYAN)
        typer.echo("  1) Run 'python -m launch_points.cli validate --format json --no-exit-on-error' to list data issues.")
        typer.echo("  2) Re-run with `python -m launch_points.cli generate --dry-run --verbose` to reproduce the error and inspect logs, or run tests to locate failures.")
        typer.echo("  3) If the error is environment-related, ensure your conda env 'launch_points' has required packages installed.")
        typer.echo("\nFull traceback (for debugging):")
        typer.echo(traceback.format_exc())
        raise typer.Exit(code=1)


def _explain_issues(results: dict) -> str:
    """Translate validator issues into human-friendly guidance."""
    messages = []
    for path, issues in results.items():
        if not issues:
            continue
        messages.append(f"File: {path}")
        # summarize common issues
        missing_pics = [i for i in issues if i.startswith("missing-picture")]
        if missing_pics:
            messages.append("  - Missing pictures referenced in the CSV. Ensure image files exist relative to the CSV file (e.g. 'berlin/figs/').")
            messages.append("    Action: place the files in the referenced path or update the 'picture' column with correct paths.")
        invalid_coords = [i for i in issues if i.startswith("invalid-coordinates")]
        if invalid_coords:
            messages.append("  - Non-numeric or invalid latitude/longitude values found.")
            messages.append("    Action: ensure 'lat' and 'lon' columns are decimal numbers (e.g. 52.4463, 13.67013).")
        transport_issues = [i for i in issues if i.startswith("transport-unknown-format")]
        if transport_issues:
            messages.append("  - 'transport' column contains unknown values.")
            messages.append("    Action: use 'True' or 'False' (or leave empty).")
        if "header-whitespace" in issues:
            messages.append("  - CSV header contains leading/trailing whitespace.")
            messages.append("    Action: run the validator with --fix or manually trim header names.")
        missing_cols = [i for i in issues if i.startswith("missing-columns")]
        if missing_cols:
            messages.append(f"  - Missing required columns: {', '.join(missing_cols)}")
            messages.append("    Action: add the required columns (name, lat, lon).")
        messages.append("")
    messages.append("If you need help reproducing the issue, re-run the CLI in verbose/dry-run mode or run the test suite to pinpoint the failure.")
    return "\n".join(messages)



@app.command()
def validate(
    format: str = typer.Option("text", "--format", help="Output format: text or json"),
    fix: bool = typer.Option(False, "--fix", help="Attempt to auto-fix trivial issues (header whitespace)"),
    exit_on_error: bool = typer.Option(True, "--exit-on-error/--no-exit-on-error", help="Exit with non-zero code if issues found"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Validate marker CSVs and GeoJSON in the default `berlin/` folder.

    By default this validates all CSV files in `berlin/` and `berlin/routes.geojson`.
    """
    csv_paths = sorted(glob.glob("berlin/*.csv"))
    results = validator.validate_all_marker_files(csv_paths)

    # Optionally auto-fix trivial issues
    if fix:
        for p, issues in results.items():
            if "header-whitespace" in issues:
                # reload, strip headers and overwrite
                df = __import__("pandas").read_csv(p)
                df.columns = [c.strip() for c in df.columns]
                df.to_csv(p, index=False)
                typer.secho(f"Fixed header whitespace in {p}", fg=typer.colors.GREEN)

    total_issues = sum(len(v) for v in results.values())
    if format == "json":
        typer.echo(json.dumps(results, indent=2))
    else:
        for p, issues in results.items():
            typer.secho(f"{p}: {len(issues)} issues", fg=typer.colors.BLUE)
            for i in issues:
                typer.echo(f"  - {i}")

    # Validate GeoJSON separately
    geojson_path = "berlin/routes.geojson"
    geo_ok = generator.validate_geojson(geojson_path)
    if not geo_ok:
        typer.secho(f"GeoJSON validation failed: {geojson_path}", fg=typer.colors.RED)
        total_issues += 1
    elif verbose:
        typer.secho(f"GeoJSON file OK: {geojson_path}", fg=typer.colors.GREEN)

    # Validate optional station paths
    station_paths = "berlin/station_paths.geojson"
    transport_config = "berlin/transport_types.json"
    stations_ok = generator.validate_station_paths(station_paths, transport_config=transport_config)
    if not stations_ok:
        typer.secho(f"Station paths GeoJSON validation failed: {station_paths}", fg=typer.colors.RED)
        total_issues += 1
    elif verbose and os.path.exists(station_paths):
        typer.secho(f"Station paths file OK: {station_paths}", fg=typer.colors.GREEN)

    if total_issues and exit_on_error:
        raise typer.Exit(code=3)


def main():
    app()


if __name__ == "__main__":
    app()
