# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Rust Patch Monitor
- CLI interface for listing and analyzing Rust for Linux patches
- AI-powered analysis using Claude for executive briefings
- Comprehensive test suite with unit, integration, and golden master tests
- GitHub Actions CI/CD pipeline
- Development workflow with pre-commit hooks
- Makefile for common development tasks
- Security scanning with Bandit and Safety
- Test coverage reporting
- Structured XML prompts for improved AI analysis
- Community engagement metrics (sign-offs, acks, reviews)
- Patch series filtering (applied vs pending)
- Interactive patch selection
- Markdown export functionality

### Features
- **Rust for Linux Focus**: Monitors only the dedicated rust-for-linux project
- **Executive AI Analysis**: Generates strategic briefings for technical leadership
- **Community Engagement Tracking**: Analyzes sign-offs, acks, reviews, and timing
- **Comprehensive Testing**: Unit, integration, and regression tests
- **Development Tools**: Pre-commit hooks, linting, formatting
- **CI/CD Pipeline**: Automated testing and security scanning

## [0.1.0] - 2025-08-27

### Added
- Initial project setup
- Basic patch fetching from Patchwork API
- Claude integration for patch analysis
- CLI commands: `list-patches`, `analyze`, `debug-recent`
- Comprehensive test suite
- Development documentation and guidelines