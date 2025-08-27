#!/usr/bin/env python3
"""
Rust for Linux Patch Monitor

A tool to monitor and analyze Rust for Linux patches from the kernel mailing list.
"""

import requests
import click
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import re
import anthropic
import json


@dataclass
class PatchSeries:
    id: int
    name: str
    date: datetime
    submitter: Dict
    total: int
    patches: List[Dict]
    cover_letter: Optional[Dict]
    web_url: str


@dataclass
class Patch:
    id: int
    name: str
    date: datetime
    submitter: Dict
    content: str
    state: str
    web_url: str
    mbox_url: str


class PatchworkClient:
    def __init__(self, base_url="https://patchwork.kernel.org/api"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_rust_for_linux_project_id(self):
        """Find the specific Rust for Linux project ID"""

        # Since rust-for-linux project exists but isn't in the API list,
        # try to access its API endpoint directly
        try:
            # Try to access the series API with the project string identifier
            test_response = self.session.get(f"{self.base_url}/series/?project=rust-for-linux&per_page=1")
            if test_response.status_code == 200:
                print("Found Rust for Linux project - using string identifier")
                return "rust-for-linux"  # Return string instead of numeric ID

            # Try to get all projects and search through them more thoroughly
            response = self.session.get(f"{self.base_url}/projects/")
            response.raise_for_status()

            projects = response.json()
            print(f"Searching through {len(projects)} projects for Rust for Linux...")

            # Look for any rust-related project
            for project in projects:
                name = project.get("name", "").lower()
                link_name = project.get("link_name", "").lower()

                # More comprehensive search
                if any(term in name for term in ["rust", "r4l"]) or any(term in link_name for term in ["rust", "r4l"]):
                    print(f"Found potential Rust project: {project.get('name')} (link: {project.get('link_name')})")
                    return project["id"]

            # If still not found, maybe it requires authentication or special access
            print("Rust for Linux project not accessible via public API.")
            print("The project exists at https://patchwork.kernel.org/project/rust-for-linux/list/")
            print("but may require authentication or have API access restrictions.")

        except Exception as e:
            print(f"Error accessing Rust for Linux project: {e}")

        raise ValueError("Rust for Linux project not accessible")

    def _is_series_applied(self, patches: List[Dict]) -> bool:
        """Use heuristics to determine if a patch series might be applied"""
        if not patches:
            return False

        # Check if the series data includes state information
        first_patch = patches[0]
        patch_name = first_patch.get("name", "").lower()

        # Common patterns that suggest a series might be applied:
        if "[git,pull]" in patch_name or "git pull" in patch_name:
            return True

        # Look for state information in the patch data
        states = []
        for patch in patches[:3]:  # Check first 3 patches
            state = patch.get("state")
            if state:
                states.append(state.lower())

        if states:
            # If we have state information, use it
            applied_states = {"accepted", "committed", "superseded"}
            applied_count = sum(1 for state in states if state in applied_states)

            # If majority are applied, consider series applied
            if applied_count > len(states) * 0.5:
                return True

        return False

    def get_recent_series(self, project_id, days: int = 90, include_applied: bool = False) -> List[PatchSeries]:
        """Get patch series from the Rust for Linux project in the last N days, optionally excluding applied series"""
        cutoff_date = datetime.now() - timedelta(days=days)

        params = {"project": project_id, "ordering": "-date", "per_page": 50}

        series_list = []
        page = 1
        applied_count = 0

        filter_text = "all patches" if include_applied else "PENDING patches"
        print(f"Searching Rust for Linux project for {filter_text} in last {days} days...")

        while True:
            params["page"] = page
            response = self.session.get(f"{self.base_url}/series/", params=params)
            response.raise_for_status()

            data = response.json()

            if not data:
                break

            for series_data in data:
                try:
                    series_date = datetime.fromisoformat(series_data["date"].replace("Z", "+00:00"))
                    # Convert to timezone-naive for comparison
                    if series_date.tzinfo:
                        series_date = series_date.replace(tzinfo=None)

                    if series_date < cutoff_date:
                        continue

                    # Handle missing or None submitter
                    submitter = series_data.get("submitter") or {}

                    # Check if the series has been applied by examining patch states
                    patches = series_data.get("patches", [])
                    if not include_applied and self._is_series_applied(patches):
                        applied_count += 1
                        continue  # Skip applied series

                    series = PatchSeries(
                        id=series_data["id"],
                        name=series_data.get("name", "Untitled"),
                        date=series_date,
                        submitter=submitter,
                        total=series_data.get("total", 0),
                        patches=patches,
                        cover_letter=series_data.get("cover_letter"),
                        web_url=series_data.get("web_url", ""),
                    )
                    series_list.append(series)
                except Exception:
                    # Skip series with data issues
                    continue

            if len(data) < 50:  # Last page
                break
            page += 1

        if not include_applied:
            print(f"Excluded {applied_count} applied patch series")
        return series_list

    def get_patch_content(self, patch_id: int) -> Patch:
        """Get detailed patch content including mbox"""
        response = self.session.get(f"{self.base_url}/patches/{patch_id}/")
        response.raise_for_status()

        patch_data = response.json()

        # Fetch mbox content
        mbox_response = self.session.get(patch_data["mbox"])
        mbox_response.raise_for_status()

        return Patch(
            id=patch_data["id"],
            name=patch_data["name"],
            date=datetime.fromisoformat(patch_data["date"].replace("Z", "+00:00")),
            submitter=patch_data["submitter"],
            content=mbox_response.text,
            state=patch_data["state"],
            web_url=patch_data["web_url"],
            mbox_url=patch_data["mbox"],
        )

    def get_patch_comments(self, patch_id: int) -> List[Dict]:
        """Get comments/discussion for a specific patch"""
        try:
            response = self.session.get(f"{self.base_url}/patches/{patch_id}/comments/")
            response.raise_for_status()
            return response.json()
        except Exception:
            return []  # Return empty list if comments can't be fetched


class ClaudeAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Client(api_key=api_key)

    def _analyze_engagement(self, series: PatchSeries, patches: List[Patch]) -> Dict:
        """Analyze community engagement indicators from patches"""
        from datetime import datetime, timezone

        # Extract version information from series name
        version_match = re.search(r"\[?v(\d+)\]?", series.name, re.IGNORECASE)
        current_version = int(version_match.group(1)) if version_match else 1

        # Calculate days since posting
        now = datetime.now(timezone.utc)
        series_date = series.date.replace(tzinfo=timezone.utc) if series.date.tzinfo is None else series.date
        days_since_posting = (now - series_date).days

        # Extract sign-offs and endorsements from all patches
        endorsements = {
            "signed_off_by": [],
            "acked_by": [],
            "reviewed_by": [],
            "tested_by": [],
        }

        for patch in patches:

            # Find all endorsement lines
            for line in patch.content.split("\n"):
                line = line.strip()

                if line.lower().startswith("signed-off-by:"):
                    name = self._extract_name_from_line(line)
                    if name and name not in endorsements["signed_off_by"]:
                        endorsements["signed_off_by"].append(name)

                elif line.lower().startswith("acked-by:"):
                    name = self._extract_name_from_line(line)
                    if name and name not in endorsements["acked_by"]:
                        endorsements["acked_by"].append(name)

                elif line.lower().startswith("reviewed-by:"):
                    name = self._extract_name_from_line(line)
                    if name and name not in endorsements["reviewed_by"]:
                        endorsements["reviewed_by"].append(name)

                elif line.lower().startswith("tested-by:"):
                    name = self._extract_name_from_line(line)
                    if name and name not in endorsements["tested_by"]:
                        endorsements["tested_by"].append(name)

        return {
            "version": current_version,
            "days_since_posting": days_since_posting,
            "endorsements": endorsements,
        }

    def _extract_name_from_line(self, line: str) -> str:
        """Extract name from endorsement line like 'Acked-by: John Doe <john@example.com>'"""

        # Remove the prefix (e.g., "Acked-by: ")
        colon_index = line.find(":")
        if colon_index == -1:
            return ""

        name_part = line[colon_index + 1 :].strip()

        # Extract name before email if present
        email_match = re.search(r"<[^>]+>", name_part)
        if email_match:
            name = name_part[: email_match.start()].strip()
        else:
            name = name_part

        return name

    def analyze_patchset(
        self,
        series: PatchSeries,
        patches: List[Patch],
        client=None,
        include_comments: bool = True,
        max_patches: int = 5,
        max_patch_chars: int = 3000,
    ) -> str:
        """Generate comprehensive analysis of a patchset with community feedback"""
        from datetime import datetime, timezone

        # Extract engagement metrics
        engagement_data = self._analyze_engagement(series, patches)

        # Build structured XML-like context
        patches_xml = []

        for i, patch in enumerate(patches[:max_patches]):
            patch_xml = f"""    <patch id="{i+1}" name="{patch.name}">
      <content>
{patch.content[:max_patch_chars]}
      </content>"""

            # Fetch and include comments if requested
            if include_comments and client:
                comments = client.get_patch_comments(patch.id)
                if comments:
                    comments_xml = []
                    for j, comment in enumerate(comments[:3]):  # Limit to 3 comments per patch
                        submitter_name = comment.get("submitter", {}).get("name", "Unknown")
                        comment_date = comment.get("date", "Unknown")[:10]  # Just the date part
                        comment_content = comment.get("content", "")[:1500]  # Limit comment length

                        comment_xml = f"""        <comment author="{submitter_name}" date="{comment_date}">
{comment_content}
        </comment>"""
                        comments_xml.append(comment_xml)

                    patch_xml += f"""
      <comments>
{chr(10).join(comments_xml)}
      </comments>"""
                else:
                    patch_xml += """
      <comments>
        <!-- No comments found for this patch -->
      </comments>"""
            else:
                patch_xml += """
      <comments>
        <!-- Comments not fetched (--no-comments flag used) -->
      </comments>"""

            patch_xml += """
    </patch>"""
            patches_xml.append(patch_xml)

        # Count total comments and find most recent activity
        total_comments = 0
        most_recent_activity = series.date

        for i, patch in enumerate(patches[:max_patches]):
            if include_comments and client:
                comments = client.get_patch_comments(patch.id)
                total_comments += len(comments)

                # Track most recent comment date
                for comment in comments:
                    try:
                        comment_date = datetime.fromisoformat(comment.get("date", "").replace("Z", "+00:00"))
                        if comment_date > most_recent_activity:
                            most_recent_activity = comment_date
                    except Exception:
                        pass

        # Calculate days since last activity
        now = datetime.now(timezone.utc)
        last_activity = (
            most_recent_activity.replace(tzinfo=timezone.utc)
            if most_recent_activity.tzinfo is None
            else most_recent_activity
        )
        days_since_last_activity = (now - last_activity).days

        # Build engagement analysis XML
        engagement_xml = f"""  <engagement_analysis>
    <version_info>
      <current_version>{engagement_data['version']}</current_version>
      <days_since_posting>{engagement_data['days_since_posting']}</days_since_posting>
    </version_info>
    <endorsements>
      <signed_off_by count="{len(engagement_data['endorsements']['signed_off_by'])}">{
          ', '.join(engagement_data['endorsements']['signed_off_by'][:5])
      }</signed_off_by>
      <acked_by count="{len(engagement_data['endorsements']['acked_by'])}">{
          ', '.join(engagement_data['endorsements']['acked_by'][:5])
      }</acked_by>
      <reviewed_by count="{len(engagement_data['endorsements']['reviewed_by'])}">{
          ', '.join(engagement_data['endorsements']['reviewed_by'][:5])
      }</reviewed_by>
      <tested_by count="{len(engagement_data['endorsements']['tested_by'])}">{
          ', '.join(engagement_data['endorsements']['tested_by'][:5])
      }</tested_by>
    </endorsements>
    <activity_indicators>
      <comment_count>{total_comments}</comment_count>
      <days_since_last_activity>{days_since_last_activity}</days_since_last_activity>
    </activity_indicators>
  </engagement_analysis>"""

        # Build the structured XML context
        analysis_context = f"""<patchset>
  <metadata>
    <title>{series.name}</title>
    <author name="{series.submitter.get('name', 'Unknown')}" email="{series.submitter.get('email', '')}"/>
    <date>{series.date.strftime('%Y-%m-%d')}</date>
    <total_patches>{series.total}</total_patches>
    <analyzed_patches>{min(len(patches), max_patches)}</analyzed_patches>
    <patchwork_url>{series.web_url}</patchwork_url>
  </metadata>

{engagement_xml}

  <patches>
{chr(10).join(patches_xml)}
  </patches>
</patchset>"""

        prompt = f"""
        Analyze this Rust for Linux kernel patchset and provide a comprehensive markdown report.

        {analysis_context}

<analysis_request>
  <output_format>markdown</output_format>
  <target_audience>Director of Engineering familiar with Linux kernel development and Rust-for-Linux strategy,
  but potentially unfamiliar with specific subsystems</target_audience>

  <role>You are a technical adviser providing succinct executive briefings. The director needs to understand
  what matters, why it matters, and be able to explain it to stakeholders. Assume deep kernel knowledge but
  explain subsystem-specific details.</role>

  <engagement_guidance>
    <status_indicators>
      - High version (v5+) + recent + many acks = "Ready for merge"
      - Recent high version + endorsements + minimal discussion = "Mature/stable"
      - Old posting (30+ days) + no acks + no activity = "Stalled"
      - Recent v1 + active discussion = "Early development"
      - Quality concerns in comments = "Needs attention"
    </status_indicators>
  </engagement_guidance>

  <format_requirements>
    <structure>
      # Executive Brief: {series.name}

      **Status**: [Ready for merge | Under review | Stalled | Quality concerns | Strategic development]
      **Significance**: [Major advance | Incremental improvement | Bug fix | Infrastructure | Experiment]

      ## What & Why
      [2-3 sentences: what this does and why it matters to Rust-for-Linux]

      ## Technical Context (expand if subsystem explanation needed)
      [Subsystem-specific details, architecture differences, interaction with existing C code]

      ## Issues & Conflicts (only if present)
      [Problems requiring director attention: quality concerns, community conflicts, blocking issues]

      ## Stakeholder Summary (if strategically significant)
      [Key talking points for external discussions]
    </structure>

    <guidelines>
      - Skip sections that don't contain meaningful information
      - Focus on what requires director attention or stakeholder communication
      - Be succinct except in Technical Context where detail helps
      - Highlight strategic advances in Rust-for-Linux adoption
      - Flag quality issues, conflicts, or unusual patterns
    </guidelines>
  </format_requirements>
</analysis_request>

Provide an executive brief following the structure above, including only sections with meaningful content.
        """

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text


@click.group()
def cli():
    """Rust for Linux Patch Monitor"""
    pass


@cli.command()
def list_projects():
    """List all available projects to find the correct one"""
    client = PatchworkClient()

    response = client.session.get(f"{client.base_url}/projects/")
    response.raise_for_status()
    projects = response.json()

    click.echo("All available projects on this Patchwork instance:\n")
    for i, project in enumerate(projects, 1):
        name = project.get("name", "Unknown")
        link_name = project.get("link_name", "Unknown")
        click.echo(f"{i:3d}. {name}")
        click.echo(f"     Link: {link_name}")
        click.echo()


@cli.command()
@click.option("--days", default=90, help="Days to look back for patches")
def debug_recent(days):
    """Debug: show recent patch series titles to find naming patterns"""
    client = PatchworkClient()

    params = {"ordering": "-date", "per_page": 20}

    response = client.session.get(f"{client.base_url}/series/", params=params)
    response.raise_for_status()
    data = response.json()

    click.echo("Recent patch series (showing titles for debugging):\n")
    for i, series in enumerate(data[:20], 1):
        click.echo(f"{i:2d}. {series['name']}")
        click.echo(f"    Date: {series['date'][:10]} | Project: {series.get('project', {}).get('name', 'Unknown')}")
        click.echo()


@cli.command()
@click.option("--days", default=90, help="Days to look back for patches")
@click.option("--include-applied", is_flag=True, help="Include already applied patch series")
@click.option("--claude-key", envvar="ANTHROPIC_API_KEY", help="Claude API key")
def list_patches(days, include_applied, claude_key):
    """List recent Rust for Linux patch series"""
    client = PatchworkClient()

    try:
        project_id = client.get_rust_for_linux_project_id()
        series_list = client.get_recent_series(project_id, days, include_applied)

        click.echo(f"Found {len(series_list)} patch series in the last {days} days:\n")

        for i, series in enumerate(series_list, 1):
            click.echo(f"{i:2d}. {series.name}")
            submitter_name = series.submitter.get("name", "Unknown") if series.submitter else "Unknown"
            click.echo(f"    By: {submitter_name} on {series.date.strftime('%Y-%m-%d')}")
            click.echo(f"    Patches: {series.total} | URL: {series.web_url}")
            click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option("--days", default=90, help="Days to look back for patches")
@click.option("--include-applied", is_flag=True, help="Include already applied patch series")
@click.option("--no-comments", is_flag=True, help="Skip fetching community comments (faster)")
@click.option("--max-patches", default=5, help="Maximum number of patches to analyze")
@click.option("--claude-key", envvar="ANTHROPIC_API_KEY", help="Claude API key")
@click.option("--output", "-o", help="Output file for the report")
def analyze(days, include_applied, no_comments, max_patches, claude_key, output):
    """Analyze a specific patch series"""
    if not claude_key:
        click.echo("Error: Claude API key is required for analysis.", err=True)
        click.echo(
            "Either set the ANTHROPIC_API_KEY environment variable or use --claude-key",
            err=True,
        )
        return

    client = PatchworkClient()
    analyzer = ClaudeAnalyzer(claude_key)

    try:
        project_id = client.get_rust_for_linux_project_id()
        series_list = client.get_recent_series(project_id, days, include_applied)

        if not series_list:
            click.echo("No recent patch series found")
            return

        # Display series for selection
        click.echo("Select a patch series to analyze:\n")
        for i, series in enumerate(series_list, 1):
            click.echo(f"{i:2d}. {series.name}")
            submitter_name = series.submitter.get("name", "Unknown") if series.submitter else "Unknown"
            click.echo(f"    By: {submitter_name} on {series.date.strftime('%Y-%m-%d')}")
            click.echo()

        selection = click.prompt("Enter series number", type=int)

        if selection < 1 or selection > len(series_list):
            click.echo("Invalid selection")
            return

        selected_series = series_list[selection - 1]

        # Fetch patch details
        click.echo(f"Fetching patches for: {selected_series.name}")
        patches = []

        for patch_info in selected_series.patches:
            patch = client.get_patch_content(patch_info["id"])
            patches.append(patch)

        # Analyze with Claude
        include_comments = not no_comments
        if include_comments:
            click.echo("Analyzing patchset with Claude (including community feedback)...")
        else:
            click.echo("Analyzing patchset with Claude (patch content only)...")

        analysis = analyzer.analyze_patchset(
            selected_series,
            patches,
            client=client,
            include_comments=include_comments,
            max_patches=max_patches,
        )

        if output:
            with open(output, "w") as f:
                f.write(analysis)
            click.echo(f"Analysis saved to {output}")
        else:
            click.echo("\n" + "=" * 80 + "\n")
            click.echo(analysis)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option("--days", default=14, help="Days to look back for patches")
@click.option("--max-series", default=10, help="Maximum number of series to analyze")
@click.option("--output-dir", default="reports", help="Output directory for reports")
@click.option("--claude-key", envvar="ANTHROPIC_API_KEY", help="Claude API key")
@click.option("--no-comments", is_flag=True, help="Skip community comments (faster)")
@click.option("--summary-report", is_flag=True, help="Generate combined summary report")
@click.option("--max-patches", default=5, help="Maximum patches per series")
def analyze_bulk(days, max_series, output_dir, claude_key, no_comments, summary_report, max_patches):
    """Analyze multiple recent patch series in batch"""
    if not claude_key:
        click.echo("Error: Claude API key is required for analysis.", err=True)
        click.echo(
            "Either set the ANTHROPIC_API_KEY environment variable or use --claude-key",
            err=True,
        )
        return

    import os
    from pathlib import Path
    
    client = PatchworkClient()
    analyzer = ClaudeAnalyzer(claude_key)

    try:
        project_id = client.get_rust_for_linux_project_id()
        series_list = client.get_recent_series(project_id, days, include_applied=False)

        if not series_list:
            click.echo("No recent patch series found")
            return

        # Sort by date (newest first) and limit series to analyze
        series_list.sort(key=lambda x: x.date, reverse=True)
        series_to_analyze = series_list[:max_series]
        
        click.echo(f"Found {len(series_list)} recent series, analyzing top {len(series_to_analyze)}")
        
        # Create output directory
        output_path = Path(output_dir)
        timestamp_dir = output_path / datetime.now().strftime("%Y-%m-%d")
        timestamp_dir.mkdir(parents=True, exist_ok=True)
        
        # Track results for summary and web export
        analysis_results = []
        failed_analyses = []
        
        # Process each series
        for i, series in enumerate(series_to_analyze, 1):
            click.echo(f"\n[{i}/{len(series_to_analyze)}] Analyzing: {series.name}")
            
            try:
                # Fetch patches
                click.echo("  Fetching patches...")
                patches = []
                for patch_info in series.patches[:max_patches]:
                    try:
                        patch = client.get_patch_content(patch_info["id"])
                        patches.append(patch)
                    except Exception as e:
                        click.echo(f"    Warning: Failed to fetch patch {patch_info['id']}: {e}")
                        continue
                
                if not patches:
                    click.echo("  Error: No patches could be fetched")
                    failed_analyses.append((series, "No patches available"))
                    continue
                
                # Analyze with Claude
                include_comments = not no_comments
                click.echo(f"  Analyzing with Claude ({len(patches)} patches)...")
                
                analysis = analyzer.analyze_patchset(
                    series,
                    patches,
                    client=client,
                    include_comments=include_comments,
                    max_patches=max_patches,
                )
                
                # Save individual analysis
                filename = f"series-{series.id}.md"
                filepath = timestamp_dir / filename
                with open(filepath, "w") as f:
                    f.write(f"# Analysis: {series.name}\n\n")
                    f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**Series ID**: {series.id}\n")
                    f.write(f"**Author**: {series.submitter.get('name', 'Unknown')}\n")
                    f.write(f"**Date**: {series.date.strftime('%Y-%m-%d')}\n")
                    f.write(f"**Patches**: {series.total}\n")
                    f.write(f"**Patchwork URL**: {series.web_url}\n\n")
                    f.write("---\n\n")
                    f.write(analysis)
                
                # Store for summary and web export
                analysis_results.append({
                    'series': series,
                    'analysis': analysis,
                    'patches': patches,
                    'filepath': str(filepath)
                })
                
                click.echo(f"  ✓ Saved to {filepath}")
                
            except Exception as e:
                click.echo(f"  ✗ Failed: {e}")
                failed_analyses.append((series, str(e)))
                continue
        
        # Generate summary report if requested
        if summary_report:
            click.echo(f"\nGenerating summary report...")
            summary_path = timestamp_dir / "summary.md"
            
            with open(summary_path, "w") as f:
                f.write(f"# Rust for Linux Patch Analysis Summary\n\n")
                f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Period**: Last {days} days\n")
                f.write(f"**Analyzed**: {len(analysis_results)}/{len(series_to_analyze)} series\n\n")
                
                if failed_analyses:
                    f.write(f"## Failed Analyses ({len(failed_analyses)})\n\n")
                    for series, error in failed_analyses:
                        f.write(f"- **{series.name}**: {error}\n")
                    f.write("\n")
                
                f.write(f"## Successful Analyses ({len(analysis_results)})\n\n")
                for result in analysis_results:
                    series = result['series']
                    f.write(f"### {series.name}\n\n")
                    f.write(f"- **Author**: {series.submitter.get('name', 'Unknown')}\n")
                    f.write(f"- **Date**: {series.date.strftime('%Y-%m-%d')}\n")
                    f.write(f"- **Patches**: {series.total}\n")
                    f.write(f"- **Report**: [{result['filepath']}]({os.path.basename(result['filepath'])})\n")
                    f.write(f"- **Patchwork**: {series.web_url}\n\n")
            
            click.echo(f"✓ Summary saved to {summary_path}")
        
        # Auto-generate web UI data
        click.echo(f"\nGenerating web UI data...")
        web_data_path = Path("web-ui/src/data/patches.json")
        
        # Create enhanced export data with analysis summaries
        export_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "project": "rust-for-linux",
                "days_back": days,
                "include_applied": False,
                "total_series": len(analysis_results),
                "analysis_method": "claude_bulk"
            },
            "patch_series": []
        }
        
        for result in analysis_results:
            series = result['series']
            patches = result['patches']
            
            # Get engagement analysis
            engagement = analyzer._analyze_engagement(series, patches)
            
            # Extract key insights from Claude analysis (simplified)
            analysis_text = result['analysis']
            status = "Under Review"  # Default
            if "ready" in analysis_text.lower():
                status = "Ready"
            elif "stall" in analysis_text.lower():
                status = "Stalled"
            elif "strategic" in analysis_text.lower():
                status = "Strategic Development"
            
            series_data = {
                "id": series.id,
                "name": series.name,
                "date": series.date.isoformat(),
                "submitter": {
                    "name": series.submitter.get("name", "Unknown") if series.submitter else "Unknown",
                    "email": series.submitter.get("email", "") if series.submitter else ""
                },
                "total_patches": series.total,
                "web_url": series.web_url,
                "engagement": {
                    "version": engagement["version"],
                    "days_since_posting": engagement["days_since_posting"], 
                    "endorsements": {
                        "signed_off_by": len(engagement["endorsements"]["signed_off_by"]),
                        "acked_by": len(engagement["endorsements"]["acked_by"]),
                        "reviewed_by": len(engagement["endorsements"]["reviewed_by"]),
                        "tested_by": len(engagement["endorsements"]["tested_by"])
                    }
                },
                "analysis": {
                    "status": status,
                    "significance": "Generated by Claude analysis",
                    "summary": analysis_text,
                    "technical_context": "See detailed analysis report",
                    "patches": [{"id": i+1, "name": f"Patch {i+1}", "description": "See full report"} for i in range(min(3, len(patches)))],
                    "issues": []
                }
            }
            export_data["patch_series"].append(series_data)
        
        # Ensure web-ui directory exists
        web_data_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(web_data_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
            
        click.echo(f"✓ Web UI data saved to {web_data_path}")
        
        # Final summary
        click.echo(f"\n🎉 Bulk analysis complete!")
        click.echo(f"✓ Analyzed: {len(analysis_results)}/{len(series_to_analyze)} series")
        click.echo(f"✗ Failed: {len(failed_analyses)} series")
        click.echo(f"📁 Reports: {timestamp_dir}")
        click.echo(f"🌐 Web UI: {web_data_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option("--days", default=90, help="Days to look back for patches")
@click.option("--include-applied", is_flag=True, help="Include already applied patch series")
@click.option("--output", "-o", required=True, help="Output JSON file")
def export_json(days, include_applied, output):
    """Export patch data as JSON for web UI consumption"""
    client = PatchworkClient()
    
    try:
        project_id = client.get_rust_for_linux_project_id()
        series_list = client.get_recent_series(project_id, days, include_applied)
        
        if not series_list:
            click.echo("No recent patch series found")
            return
            
        # Convert series data to JSON-serializable format
        export_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "project": "rust-for-linux",
                "days_back": days,
                "include_applied": include_applied,
                "total_series": len(series_list)
            },
            "patch_series": []
        }
        
        click.echo(f"Exporting {len(series_list)} patch series...")
        
        for series in series_list:
            # Get engagement analysis for each series
            analyzer = ClaudeAnalyzer("dummy-key")  # Just for analysis function
            try:
                # Get first few patches for analysis
                patches = []
                for patch_ref in series.patches[:3]:  # Limit to first 3 patches
                    try:
                        patch = client.get_patch_content(patch_ref["id"])
                        patches.append(patch)
                    except:
                        continue  # Skip failed patches
                
                engagement = analyzer._analyze_engagement(series, patches)
            except:
                engagement = {
                    "version": 1,
                    "days_since_posting": 0,
                    "endorsements": {"signed_off_by": [], "acked_by": [], "reviewed_by": [], "tested_by": []}
                }
            
            series_data = {
                "id": series.id,
                "name": series.name,
                "date": series.date.isoformat(),
                "submitter": {
                    "name": series.submitter.get("name", "Unknown") if series.submitter else "Unknown",
                    "email": series.submitter.get("email", "") if series.submitter else ""
                },
                "total_patches": series.total,
                "web_url": series.web_url,
                "engagement": {
                    "version": engagement["version"],
                    "days_since_posting": engagement["days_since_posting"], 
                    "endorsements": {
                        "signed_off_by": len(engagement["endorsements"]["signed_off_by"]),
                        "acked_by": len(engagement["endorsements"]["acked_by"]),
                        "reviewed_by": len(engagement["endorsements"]["reviewed_by"]),
                        "tested_by": len(engagement["endorsements"]["tested_by"])
                    }
                }
            }
            export_data["patch_series"].append(series_data)
        
        # Write to JSON file
        with open(output, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
            
        click.echo(f"Data exported to {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    cli()
