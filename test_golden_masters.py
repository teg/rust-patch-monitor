#!/usr/bin/env python3
"""
Golden Master Tests for Rust Patch Monitor

These tests ensure that the XML prompt structure and analysis format
remain stable across changes.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
import difflib

from rust_patch_monitor import ClaudeAnalyzer


class TestGoldenMasters:
    """Golden master tests to prevent regression in output format"""

    def test_xml_prompt_structure(self):
        """Test that XML prompt structure matches expected format"""

        analyzer = ClaudeAnalyzer("fake-api-key")

        # Create consistent test data
        series = Mock()
        series.name = "[v3] rust: kernel: add device abstractions"
        series.submitter = {"name": "Test Author", "email": "test@example.com"}
        series.date = datetime(2025, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
        series.total = 2
        series.web_url = "https://patchwork.kernel.org/project/rust-for-linux/list/?series=123"

        mock_patch = Mock()
        mock_patch.name = "rust: kernel: add device abstraction"
        mock_patch.content = "Sample patch content\nSigned-off-by: Test Author <test@example.com>"
        mock_patch.id = 456

        expected_xml_structure = """<patchset>
  <metadata>
    <title>[v3] rust: kernel: add device abstractions</title>
    <author name="Test Author" email="test@example.com"/>
    <date>2025-08-27</date>
    <total_patches>2</total_patches>
    <analyzed_patches>1</analyzed_patches>
    <patchwork_url>https://patchwork.kernel.org/project/rust-for-linux/list/?series=123</patchwork_url>
  </metadata>
  
  <engagement_analysis>
    <version_info>
      <current_version>3</current_version>
      <days_since_posting>0</days_since_posting>
    </version_info>
    <endorsements>
      <signed_off_by count="1">Test Author</signed_off_by>
      <acked_by count="0"></acked_by>
      <reviewed_by count="0"></reviewed_by>
      <tested_by count="0"></tested_by>
    </endorsements>
    <activity_indicators>
      <comment_count>0</comment_count>
      <days_since_last_activity>0</days_since_last_activity>
    </activity_indicators>
  </engagement_analysis>
  
  <patches>
    <patch id="1" name="rust: kernel: add device abstraction">
      <content>
Sample patch content
Signed-off-by: Test Author <test@example.com>
      </content>
      <comments>
        <!-- Comments not fetched (--no-comments flag used) -->
      </comments>
    </patch>
  </patches>
</patchset>"""

        # Generate actual XML
        with patch("rust_patch_monitor.ClaudeAnalyzer._analyze_engagement") as mock_engagement:
            mock_engagement.return_value = {
                "version": 3,
                "days_since_posting": 0,
                "endorsements": {
                    "signed_off_by": ["Test Author"],
                    "acked_by": [],
                    "reviewed_by": [],
                    "tested_by": [],
                },
            }

            with patch.object(analyzer, "client") as mock_client:
                mock_response = Mock()
                mock_response.content = [Mock(text="Mock response")]
                mock_client.messages.create.return_value = mock_response

                # Call analyze_patchset to generate XML
                analyzer.analyze_patchset(series, [mock_patch], include_comments=False)

                # Get the generated prompt
                call_args = mock_client.messages.create.call_args
                actual_prompt = call_args[1]["messages"][0]["content"]

                # Extract the XML part (before analysis_request)
                xml_start = actual_prompt.find("<patchset>")
                xml_end = actual_prompt.find("</patchset>") + len("</patchset>")
                actual_xml = actual_prompt[xml_start:xml_end]

                # Compare structures (normalize whitespace)
                expected_lines = [line.strip() for line in expected_xml_structure.strip().split("\n") if line.strip()]
                actual_lines = [line.strip() for line in actual_xml.strip().split("\n") if line.strip()]

                if expected_lines != actual_lines:
                    diff = "\n".join(
                        difflib.unified_diff(
                            expected_lines,
                            actual_lines,
                            fromfile="expected",
                            tofile="actual",
                            lineterm="",
                        )
                    )
                    pytest.fail(f"XML structure mismatch:\n{diff}")

    def test_analysis_request_format(self):
        """Test that the analysis request format is stable"""

        analyzer = ClaudeAnalyzer("fake-api-key")

        series = Mock()
        series.name = "Test Series"
        series.submitter = {"name": "Test", "email": "test@example.com"}
        series.date = datetime.now(timezone.utc)
        series.total = 1
        series.web_url = "https://example.com"

        mock_patch = Mock()
        mock_patch.name = "Test Patch"
        mock_patch.content = "Test content"
        mock_patch.id = 1

        with patch("rust_patch_monitor.ClaudeAnalyzer._analyze_engagement") as mock_engagement:
            mock_engagement.return_value = {
                "version": 1,
                "days_since_posting": 0,
                "endorsements": {
                    "signed_off_by": [],
                    "acked_by": [],
                    "reviewed_by": [],
                    "tested_by": [],
                },
            }

            with patch.object(analyzer, "client") as mock_client:
                mock_response = Mock()
                mock_response.content = [Mock(text="Mock response")]
                mock_client.messages.create.return_value = mock_response

                analyzer.analyze_patchset(series, [mock_patch], include_comments=False)

                call_args = mock_client.messages.create.call_args
                prompt = call_args[1]["messages"][0]["content"]

                # Check for key elements in analysis request
                required_elements = [
                    "<analysis_request>",
                    "<target_audience>Director of Engineering",
                    "<role>You are a technical adviser",
                    "**Status**:",
                    "**Significance**:",
                    "## What & Why",
                    "## Technical Context",
                    "Executive Brief:",
                ]

                for element in required_elements:
                    assert element in prompt, f"Missing required element: {element}"


def test_save_golden_master():
    """Utility to save current output as golden master (run manually when needed)"""
    # This test is normally skipped - run with pytest -k golden_save to update masters
    pytest.skip("Golden master save test - run manually when needed")

    # Generate current output with known inputs
    # ... implementation to save current output to file
    # Only run this when you intentionally want to update the golden masters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
