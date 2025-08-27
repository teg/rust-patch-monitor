# Rust for Linux Patch Monitor

A Python tool to monitor and analyze Rust for Linux patches from the kernel mailing list via Patchwork, with AI-powered analysis using Claude.

## Features

- **Rust for Linux Focus**: Monitors only the dedicated Rust for Linux project on Patchwork
- **No Fallbacks**: Strictly queries the rust-for-linux project with no cross-project searching
- **Pending Patch Focus**: By default, excludes already applied/merged patch series to focus on active development
- **Executive AI Analysis**: Uses Claude as a technical adviser to generate succinct executive briefings:
  - **Strategic significance** and impact on Rust-for-Linux adoption  
  - **Subsystem context** with architecture explanations for directors
  - **Status assessment** (Ready/Stalled/Quality concerns/Strategic development)
  - **Community engagement analysis** (sign-offs, acks, reviews, timing)
  - **Issues flagging** for problems requiring leadership attention
- **Comprehensive Context**: Includes both patch content and community discussion threads
- **Structured Analysis**: Uses XML-structured prompts for better Claude parsing and analysis
- **Engagement Indicators**: Tracks patch versions, sign-offs, acks, reviews, and activity timing
- **Interactive Selection**: CLI interface for browsing and selecting patches to analyze
- **Configurable Analysis**: Options for analysis depth, comment inclusion, and patch limits
- **Executive Briefings**: Exports focused analysis in markdown format suitable for leadership

## Installation

### From GitHub

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/rust-patch-monitor.git
   cd rust-patch-monitor
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make the script executable:
   ```bash
   chmod +x rust_patch_monitor.py
   ```

### Development Installation

For development work:
```bash
git clone https://github.com/your-username/rust-patch-monitor.git
cd rust-patch-monitor
make dev-setup  # Installs dev dependencies and sets up pre-commit hooks
```

## Configuration

The tool automatically uses your existing Claude API key from the `ANTHROPIC_API_KEY` environment variable (which Claude Code already sets). 

If needed, you can override it with: `--claude-key YOUR_KEY`

## Usage

### List Recent Rust Patches

Show all pending Rust patch series from the last 90 days:

```bash
./rust_patch_monitor.py list-patches
```

Customize the time window:
```bash
./rust_patch_monitor.py list-patches --days 30
```

Include already applied/merged series:
```bash
./rust_patch_monitor.py list-patches --include-applied
```

### Analyze a Specific Patchset

Generate a comprehensive AI analysis of a patch series:

```bash
./rust_patch_monitor.py analyze
```

This will:
1. Show available pending patch series
2. Prompt you to select one for analysis
3. Fetch the patch content from Patchwork
4. Generate a detailed markdown analysis using Claude

Save analysis to file:
```bash
./rust_patch_monitor.py analyze --output report.md
```

Include applied patches in analysis selection:
```bash
./rust_patch_monitor.py analyze --include-applied
```

Skip community comments for faster analysis:
```bash
./rust_patch_monitor.py analyze --no-comments
```

Analyze more patches from a series:
```bash
./rust_patch_monitor.py analyze --max-patches 10
```

### Debug Recent Patches

See what recent patches look like to understand naming patterns:

```bash
./rust_patch_monitor.py debug-recent
```

## Executive Briefing Format

The tool generates focused executive briefings with:

1. **Status & Significance** - Quick assessment of readiness and strategic importance
2. **What & Why** - Succinct explanation of goals and relevance to Rust-for-Linux
3. **Technical Context** - Subsystem details and architecture explanations (when relevant)
4. **Issues & Conflicts** - Problems requiring leadership attention (when present)
5. **Stakeholder Summary** - Key talking points for external discussions (when significant)

**Report Focus**: Only includes sections with meaningful content, designed for directors of engineering who need to understand and communicate about Rust-for-Linux developments to stakeholders.

## Architecture

The tool consists of:

- **PatchworkClient**: Interfaces with Patchwork API to fetch patch series and content
- **ClaudeAnalyzer**: Handles AI analysis using the Anthropic Claude API
- **CLI Interface**: Click-based command-line interface for user interaction
- **Data Models**: Structured representations of patches and series

## Limitations

- The Patchwork API may have rate limits
- Analysis quality depends on patch content and Claude's understanding
- Historical data availability varies by Patchwork instance
- Large patchsets are truncated for API token limits

## Future Enhancements

- Real-time monitoring with notifications
- Integration with Git repositories
- Historical trend analysis
- Multi-project support beyond kernel
- Web interface for easier browsing

## Development

### Quick Start

```bash
# Run tests
make test

# Format and lint code
make lint

# Run all checks
make check
```

### Development Workflow

We use a strict PR-based development process:

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Make changes** with tests
3. **Run checks locally**: `make check`
4. **Create PR** on GitHub
5. **Wait for CI** and code review
6. **Merge** once approved

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Testing

- **Unit tests**: `make test-unit`
- **Integration tests**: `make test-integration`
- **Golden master tests**: `make test-golden`
- **Full test suite**: `make test`

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

Areas where contributions are especially welcome:
- Better patch filtering algorithms
- Enhanced analysis prompts
- Additional output formats
- Performance improvements
- Bug fixes and edge cases

## License

Use responsibly for kernel development monitoring and analysis purposes.