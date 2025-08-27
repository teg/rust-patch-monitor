#!/usr/bin/env python3
"""
Tests for Rust Patch Monitor

Run with: python -m pytest test_rust_patch_monitor.py -v
"""

import pytest
import responses
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Import the classes we want to test
from rust_patch_monitor import PatchworkClient, ClaudeAnalyzer


class TestEngagementAnalysis:
    """Test the engagement analysis functionality - high regression risk"""

    def test_extract_version_from_series_name(self):
        """Test version number extraction from patch series names"""
        analyzer = ClaudeAnalyzer("fake-api-key")

        # Create mock series with different version patterns
        test_cases = [
            ("[v7] drm: Add UAPI for the Asahi driver", 7),
            ("rust: Add bug/warn abstractions v3", 3),
            ("[PATCH v12 1/5] rust: kernel: add basic support", 12),
            ("rust: kernel: device: Add support", 1),  # No version = v1
            ("[RFC v2] rust: experimental feature", 2),
        ]

        for series_name, expected_version in test_cases:
            series = Mock()
            series.name = series_name
            series.date = datetime.now(timezone.utc)

            result = analyzer._analyze_engagement(series, [])
            assert result["version"] == expected_version, f"Failed for '{series_name}'"

    def test_extract_endorsements_from_patch_content(self):
        """Test parsing of sign-offs, acks, reviews from patch content"""
        analyzer = ClaudeAnalyzer("fake-api-key")

        # Create mock patch with various endorsements
        patch_content = """
        Subject: rust: add new feature

        This patch adds important functionality.

        Signed-off-by: Alice Author <alice@example.com>
        Reviewed-by: Bob Reviewer <bob@kernel.org>
        Acked-by: Carol Maintainer <carol@kernel.org>
        Tested-by: Dave Tester <dave@test.com>
        Signed-off-by: Eve Committer <eve@kernel.org>
        """

        mock_patch = Mock()
        mock_patch.content = patch_content

        series = Mock()
        series.name = "test series"
        series.date = datetime.now(timezone.utc)

        result = analyzer._analyze_engagement(series, [mock_patch])

        endorsements = result["endorsements"]
        assert len(endorsements["signed_off_by"]) == 2
        assert len(endorsements["acked_by"]) == 1
        assert len(endorsements["reviewed_by"]) == 1
        assert len(endorsements["tested_by"]) == 1

        assert "Alice Author" in endorsements["signed_off_by"]
        assert "Eve Committer" in endorsements["signed_off_by"]
        assert "Bob Reviewer" in endorsements["reviewed_by"]
        assert "Carol Maintainer" in endorsements["acked_by"]
        assert "Dave Tester" in endorsements["tested_by"]

    def test_extract_name_from_endorsement_line(self):
        """Test name extraction from various endorsement line formats"""
        analyzer = ClaudeAnalyzer("fake-api-key")

        test_cases = [
            ("Signed-off-by: John Doe <john@example.com>", "John Doe"),
            (
                "Acked-by: Jane Smith<jane@kernel.org>",
                "Jane Smith",
            ),  # No space before <
            ("Reviewed-by: Bob O'Connor <bob.oconnor@company.com>", "Bob O'Connor"),
            ("Tested-by: Multi Word Name <multi@test.org>", "Multi Word Name"),
            ("Signed-off-by: SingleName <single@example.com>", "SingleName"),
            ("Acked-by: Name-With-Dashes <dashes@test.com>", "Name-With-Dashes"),
        ]

        for line, expected_name in test_cases:
            result = analyzer._extract_name_from_line(line)
            assert result == expected_name, f"Failed for '{line}'"

    def test_days_since_posting_calculation(self):
        """Test age calculation with timezone handling"""
        from freezegun import freeze_time

        analyzer = ClaudeAnalyzer("fake-api-key")

        # Freeze time for predictable testing
        with freeze_time("2025-08-27 12:00:00"):
            # Test patch from 5 days ago
            past_date = datetime(2025, 8, 22, 12, 0, 0, tzinfo=timezone.utc)
            series = Mock()
            series.name = "test"
            series.date = past_date

            result = analyzer._analyze_engagement(series, [])
            assert result["days_since_posting"] == 5


class TestTokenUsageCapture:
    """Test token usage capture from Claude API responses"""

    def test_analyze_patchset_captures_token_usage(self):
        """Test that analyze_patchset returns both analysis and token usage"""
        analyzer = ClaudeAnalyzer("fake-api-key")

        # Create mock data
        series = Mock()
        series.name = "Test Series"
        series.submitter = {"name": "Test Author", "email": "test@example.com"}
        series.date = datetime(2025, 8, 27, tzinfo=timezone.utc)
        series.total = 1
        series.web_url = "https://example.com/series/1"

        mock_patch = Mock()
        mock_patch.name = "Test Patch"
        mock_patch.content = "Test patch content"
        mock_patch.id = 123

        with patch("rust_patch_monitor.ClaudeAnalyzer._analyze_engagement") as mock_engagement:
            mock_engagement.return_value = {
                "version": 1,
                "days_since_posting": 5,
                "endorsements": {
                    "signed_off_by": ["Author Name"],
                    "acked_by": [],
                    "reviewed_by": [],
                    "tested_by": [],
                },
            }

            # Mock Claude API client with realistic response structure
            with patch.object(analyzer, "client") as mock_client:
                mock_response = Mock()
                mock_response.content = [Mock(text="Test analysis content")]
                mock_response.usage = Mock(input_tokens=1000, output_tokens=100)
                mock_client.messages.create.return_value = mock_response

                # Call analyze_patchset
                result = analyzer.analyze_patchset(series, [mock_patch], include_comments=False)

                # Verify result structure
                assert isinstance(result, dict)
                assert "analysis" in result
                assert "token_usage" in result

                # Verify analysis content
                assert result["analysis"] == "Test analysis content"

                # Verify token usage structure
                token_usage = result["token_usage"]
                assert token_usage["input_tokens"] == 1000
                assert token_usage["output_tokens"] == 100
                assert token_usage["model"] == "claude-sonnet-4-20250514"

    def test_bulk_analysis_aggregates_token_usage(self):
        """Test that bulk analysis properly aggregates token usage across multiple series"""
        from click.testing import CliRunner
        from rust_patch_monitor import cli

        runner = CliRunner()

        # Mock the entire pipeline with realistic token usage
        with patch("rust_patch_monitor.PatchworkClient") as MockClient, patch(
            "rust_patch_monitor.ClaudeAnalyzer"
        ) as MockAnalyzer:

            # Setup mock client
            mock_client_instance = MockClient.return_value
            mock_series = Mock()
            mock_series.id = 1
            mock_series.name = "Test Series"
            mock_series.submitter = {"name": "Test", "email": "test@example.com"}
            mock_series.date = datetime.now(timezone.utc)
            mock_series.total = 1
            mock_series.web_url = "https://example.com"
            mock_series.patches = [{"id": 1, "name": "Test patch"}]

            mock_client_instance.get_rust_for_linux_project_id.return_value = "rust-for-linux"
            mock_client_instance.get_recent_series.return_value = [mock_series]
            mock_client_instance.get_patch_content.return_value = Mock(content="test", id=1)

            # Setup mock analyzer with token usage
            mock_analyzer_instance = MockAnalyzer.return_value
            mock_analyzer_instance.analyze_patchset.return_value = {
                "analysis": "Test analysis",
                "token_usage": {
                    "input_tokens": 1000,
                    "output_tokens": 100,
                    "model": "claude-sonnet-4-20250514",
                },
            }
            mock_analyzer_instance._analyze_engagement.return_value = {
                "version": 1,
                "days_since_posting": 0,
                "endorsements": {
                    "signed_off_by": [],
                    "acked_by": [],
                    "reviewed_by": [],
                    "tested_by": [],
                },
            }

            # Run bulk analysis command
            with runner.isolated_filesystem():
                # Create web-ui directory structure
                import os

                os.makedirs("web-ui/src/data", exist_ok=True)

                result = runner.invoke(
                    cli,
                    [
                        "analyze-bulk",
                        "--days",
                        "7",
                        "--max-patches",
                        "1",
                        "--claude-key",
                        "test-key",
                        "--no-comments",
                    ],
                )

                # Should succeed and show token usage
                assert result.exit_code == 0
                assert "📊 Tokens:" in result.output
                assert "1000 in / 100 out" in result.output

    def test_json_export_includes_token_metadata(self):
        """Test that JSON export includes aggregated token usage in metadata"""
        import tempfile
        import json

        # Create a temporary analysis result with token usage
        analysis_results = [
            {
                "series": Mock(id=1, name="Test Series 1"),
                "analysis": "Analysis 1",
                "patches": [Mock()],
                "token_usage": {"input_tokens": 800, "output_tokens": 75},
            },
            {
                "series": Mock(id=2, name="Test Series 2"),
                "analysis": "Analysis 2",
                "patches": [Mock()],
                "token_usage": {"input_tokens": 1200, "output_tokens": 125},
            },
        ]

        # Mock the analyzer and create export data structure
        total_input = sum(r["token_usage"]["input_tokens"] for r in analysis_results)
        total_output = sum(r["token_usage"]["output_tokens"] for r in analysis_results)

        export_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "project": "rust-for-linux",
                "total_series": len(analysis_results),
                "token_usage": {
                    "total_input_tokens": total_input,
                    "total_output_tokens": total_output,
                    "model": "claude-sonnet-4-20250514",
                    "analysis_count": len(analysis_results),
                },
            }
        }

        # Verify token aggregation
        assert export_data["metadata"]["token_usage"]["total_input_tokens"] == 2000
        assert export_data["metadata"]["token_usage"]["total_output_tokens"] == 200
        assert export_data["metadata"]["token_usage"]["analysis_count"] == 2


class TestXMLGeneration:
    """Test XML prompt generation - critical for Claude integration"""

    def test_xml_structure_validity(self):
        """Ensure generated XML is well-formed"""
        analyzer = ClaudeAnalyzer("fake-api-key")

        # Create mock data
        series = Mock()
        series.name = "Test Series"
        series.submitter = {"name": "Test Author", "email": "test@example.com"}
        series.date = datetime(2025, 8, 27, tzinfo=timezone.utc)
        series.total = 1
        series.web_url = "https://example.com/series/1"

        mock_patch = Mock()
        mock_patch.name = "Test Patch"
        mock_patch.content = "Test patch content"
        mock_patch.id = 123

        # Generate XML (without calling Claude API)
        with patch("rust_patch_monitor.ClaudeAnalyzer._analyze_engagement") as mock_engagement:
            mock_engagement.return_value = {
                "version": 1,
                "days_since_posting": 5,
                "endorsements": {
                    "signed_off_by": ["Author Name"],
                    "acked_by": [],
                    "reviewed_by": [],
                    "tested_by": [],
                },
            }

            # Call analyze_patchset but intercept before API call
            with patch.object(analyzer, "client") as mock_client:
                mock_response = Mock()
                mock_response.content = [Mock(text="Test response")]
                mock_response.usage = Mock(input_tokens=1000, output_tokens=100)
                mock_client.messages.create.return_value = mock_response

                result = analyzer.analyze_patchset(series, [mock_patch], include_comments=False)

                # Verify we get the new return format
                assert isinstance(result, dict)
                assert "analysis" in result
                assert "token_usage" in result

                # Verify the XML context was passed to Claude
                call_args = mock_client.messages.create.call_args
                prompt = call_args[1]["messages"][0]["content"]

                # Check for key XML structures
                assert "<patchset>" in prompt
                assert "</patchset>" in prompt
                assert "<metadata>" in prompt
                assert "<engagement_analysis>" in prompt
                assert "<patches>" in prompt
                assert "<analysis_request>" in prompt


class TestPatchworkClient:
    """Test API interactions with mocked responses"""

    @responses.activate
    def test_rust_project_detection(self):
        """Test finding the rust-for-linux project"""

        # Mock successful response
        responses.add(
            responses.GET,
            "https://patchwork.kernel.org/api/series/?project=rust-for-linux&per_page=1",
            json=[],
            status=200,
        )

        client = PatchworkClient()
        project_id = client.get_rust_for_linux_project_id()
        assert project_id == "rust-for-linux"

    @responses.activate
    def test_series_filtering_applied_patches(self):
        """Test that applied patches are properly filtered"""

        # Mock series API response
        mock_series_data = [
            {
                "id": 1,
                "name": "Applied series",
                "date": "2025-08-20T10:00:00Z",
                "submitter": {"name": "Test Author", "email": "test@example.com"},
                "total": 1,
                "patches": [{"id": 1, "name": "[GIT,PULL] Rust fixes for 6.15"}],
                "cover_letter": None,
                "web_url": "https://example.com/series/1",
            },
            {
                "id": 2,
                "name": "rust: add new feature",
                "date": "2025-08-20T10:00:00Z",
                "submitter": {"name": "Test Author", "email": "test@example.com"},
                "total": 1,
                "patches": [{"id": 2, "name": "Regular patch"}],
                "cover_letter": None,
                "web_url": "https://example.com/series/2",
            },
        ]

        responses.add(
            responses.GET,
            "https://patchwork.kernel.org/api/series/?project=rust-for-linux&ordering=-date&per_page=50&page=1",
            json=mock_series_data,
            status=200,
        )

        # Mock empty response for page 2 to end pagination
        responses.add(
            responses.GET,
            "https://patchwork.kernel.org/api/series/?project=rust-for-linux&ordering=-date&per_page=50&page=2",
            json=[],
            status=200,
        )

        client = PatchworkClient()

        # Test with include_applied=False (default)
        series_list = client.get_recent_series("rust-for-linux", days=90, include_applied=False)

        # Should filter out GIT,PULL request but keep regular patch
        assert len(series_list) == 1
        assert "rust: add new feature" in series_list[0].name

    @responses.activate
    def test_patch_comments_fetching(self):
        """Test comment fetching for patches"""

        mock_comments = [
            {
                "id": 1,
                "submitter": {"name": "Reviewer One", "email": "reviewer1@example.com"},
                "date": "2025-05-02T10:00:00Z",
                "content": "This looks good but needs a small fix.",
            },
            {
                "id": 2,
                "submitter": {"name": "Reviewer Two", "email": "reviewer2@example.com"},
                "date": "2025-05-02T11:00:00Z",
                "content": "I agree with the approach.",
            },
        ]

        responses.add(
            responses.GET,
            "https://patchwork.kernel.org/api/patches/123/comments/",
            json=mock_comments,
            status=200,
        )

        client = PatchworkClient()
        comments = client.get_patch_comments(123)

        assert len(comments) == 2
        assert comments[0]["submitter"]["name"] == "Reviewer One"
        assert "looks good" in comments[0]["content"]


class TestCLIInterface:
    """Test command-line interface"""

    def test_cli_help_output(self):
        """Ensure help output contains all expected options"""
        from click.testing import CliRunner
        from rust_patch_monitor import cli

        runner = CliRunner()

        # Test main help
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Rust for Linux Patch Monitor" in result.output

        # Test analyze command help
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "--days" in result.output
        assert "--include-applied" in result.output
        assert "--no-comments" in result.output
        assert "--max-patches" in result.output
        assert "--claude-key" in result.output
        assert "--output" in result.output

    def test_cli_missing_api_key_handling(self):
        """Test graceful handling of missing API key"""
        from click.testing import CliRunner
        from rust_patch_monitor import cli

        runner = CliRunner()

        # Should fail gracefully when no API key provided
        result = runner.invoke(cli, ["analyze"])
        assert result.exit_code == 0  # Click doesn't exit(1) by default
        assert "Claude API key is required" in result.output


# Integration test data
SAMPLE_PATCH_CONTENT = """
From: Alice Author <alice@rust-project.org>
Subject: [PATCH v3 1/2] rust: kernel: add device abstraction

This patch adds device abstraction for Rust drivers.

The device abstraction provides a safe wrapper around
the kernel device model, allowing Rust drivers to
interact with devices safely.

Signed-off-by: Alice Author <alice@rust-project.org>
Reviewed-by: Bob Reviewer <bob@kernel.org>
Acked-by: Carol Maintainer <carol@kernel.org>
"""

SAMPLE_SERIES_RESPONSE = {
    "id": 958022,
    "name": "[v3] rust: kernel: device abstractions",
    "date": "2025-04-29T10:00:00Z",
    "submitter": {"name": "Alice Author", "email": "alice@rust-project.org"},
    "total": 2,
    "patches": [
        {"id": 1, "name": "rust: kernel: add device abstraction"},
        {"id": 2, "name": "rust: kernel: add device driver trait"},
    ],
    "cover_letter": None,
    "web_url": "https://patchwork.kernel.org/project/rust-for-linux/list/?series=958022",
}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
