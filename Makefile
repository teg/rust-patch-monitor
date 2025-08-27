.PHONY: help test test-unit test-integration test-golden lint format clean install dev-install

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r test_requirements.txt
	pip install black flake8 pre-commit

test: ## Run all tests
	python3 -m pytest test_rust_patch_monitor.py test_golden_masters.py -v

test-unit: ## Run unit tests only
	python3 -m pytest test_rust_patch_monitor.py::TestEngagementAnalysis -v
	python3 -m pytest test_rust_patch_monitor.py::TestXMLGeneration -v
	python3 -m pytest test_rust_patch_monitor.py::TestCLIInterface -v

test-integration: ## Run integration tests only
	python3 -m pytest test_rust_patch_monitor.py::TestPatchworkClient -v

test-golden: ## Run golden master tests only
	python3 -m pytest test_golden_masters.py::TestGoldenMasters -v

test-cli: ## Test CLI functionality
	python3 rust_patch_monitor.py --help
	python3 rust_patch_monitor.py list-patches --help
	python3 rust_patch_monitor.py analyze --help
	python3 rust_patch_monitor.py analyze-bulk --help
	python3 rust_patch_monitor.py export-json --help

format: ## Format code with black
	black rust_patch_monitor.py test_rust_patch_monitor.py test_golden_masters.py --line-length=120

format-check: ## Check code formatting
	black rust_patch_monitor.py test_rust_patch_monitor.py test_golden_masters.py --check --diff --line-length=120

lint: ## Run linting
	flake8 rust_patch_monitor.py test_rust_patch_monitor.py test_golden_masters.py --max-line-length=120

lint-fix: format ## Format code and run linting
	$(MAKE) lint

check: ## Run all checks (tests, formatting, linting)
	$(MAKE) test
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test-cli

clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.md.tmp" -delete
	find . -type f -name "analysis_*.md" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf reports

pre-commit: ## Run pre-commit checks
	$(MAKE) format
	$(MAKE) test
	$(MAKE) lint

# Development workflow helpers
dev-setup: dev-install ## Complete development setup
	pre-commit install
	@echo "Development environment ready!"
	@echo "Run 'make check' to verify everything works."

quick-test: ## Quick test run (unit tests only)
	python3 -m pytest test_rust_patch_monitor.py::TestEngagementAnalysis test_rust_patch_monitor.py::TestXMLGeneration -v

# Bulk analysis targets
reports: ## Generate reports for active PRs in last 14 days (includes web UI update)
	python3 rust_patch_monitor.py analyze-bulk --days 14 --max-series 10 --summary-report

reports-weekly: ## Generate weekly reports (7 days) with web UI update  
	python3 rust_patch_monitor.py analyze-bulk --days 7 --max-series 5 --summary-report

reports-custom: ## Generate reports for custom period (use DAYS=X to specify)
	python3 rust_patch_monitor.py analyze-bulk --days $(DAYS) --max-series 10 --summary-report

reports-fast: ## Generate reports without community comments (faster)
	python3 rust_patch_monitor.py analyze-bulk --days 14 --max-series 10 --no-comments --summary-report