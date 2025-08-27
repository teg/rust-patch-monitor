# GitHub Repository Setup Guide

## Step 1: Create GitHub Repository

### Using GitHub Web Interface
1. Go to [GitHub.com](https://github.com)
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in the details:
   - **Repository name**: `rust-patch-monitor`
   - **Description**: `AI-powered monitoring and analysis tool for Rust for Linux patches from Patchwork`
   - **Visibility**: Public (recommended to showcase the project)
   - **Initialize this repository with**: Leave unchecked (we already have files)
   - **Add a README file**: Leave unchecked
   - **Add .gitignore**: Leave unchecked  
   - **Choose a license**: Leave unchecked (we have LICENSE file)

5. Click "Create repository"

### Using GitHub CLI (Alternative)
If you have GitHub CLI installed:
```bash
gh repo create rust-patch-monitor --public --description "AI-powered monitoring and analysis tool for Rust for Linux patches from Patchwork" --clone=false
```

## Step 2: Connect Local Repository to GitHub

After creating the repository on GitHub, connect your local repository:

```bash
# Add the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/rust-patch-monitor.git

# Push the code to GitHub
git push -u origin main
```

## Step 3: Enable GitHub Actions

GitHub Actions should be automatically enabled, but verify:
1. Go to your repository on GitHub
2. Click the "Actions" tab
3. If prompted, click "I understand my workflows, go ahead and enable them"

## Step 4: Set Up Branch Protection Rules

1. Go to your repository on GitHub
2. Click "Settings" tab
3. Click "Branches" in the left sidebar
4. Click "Add rule"
5. Configure the branch protection rule:
   - **Branch name pattern**: `main`
   - Check ✅ "Require a pull request before merging"
   - Check ✅ "Require approvals" (set to 1)
   - Check ✅ "Dismiss stale PR approvals when new commits are pushed"
   - Check ✅ "Require status checks to pass before merging"
   - Check ✅ "Require branches to be up to date before merging"
   - In "Status checks that are required", add:
     - `test (3.8)`, `test (3.9)`, `test (3.10)`, `test (3.11)`, `test (3.12)`
     - `lint`
     - `all-checks`
   - Check ✅ "Include administrators"
   - Check ✅ "Allow force pushes" (keep unchecked)
   - Check ✅ "Allow deletions" (keep unchecked)
6. Click "Create"

## Step 5: Configure Repository Settings

### General Settings
1. Go to Settings > General
2. Under "Features":
   - ✅ Enable Issues
   - ✅ Enable Projects  
   - ✅ Enable Wiki (optional)
   - ✅ Enable Discussions (optional)
3. Under "Pull Requests":
   - ✅ Allow merge commits
   - ✅ Allow squash merging (default)
   - ❌ Allow rebase merging
   - ✅ Always suggest updating pull request branches
   - ✅ Allow auto-merge
   - ✅ Automatically delete head branches

### Security Settings
1. Go to Settings > Security
2. Enable Dependabot alerts
3. Enable Dependabot security updates
4. Enable Dependabot version updates (optional)

## Step 6: Add Repository Badges

Add these badges to your README.md to show build status and quality metrics:

```markdown
# Rust for Linux Patch Monitor

[![CI](https://github.com/YOUR_USERNAME/rust-patch-monitor/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/rust-patch-monitor/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<!-- Rest of your README content -->
```

## Step 7: Test the Setup

1. Create a test branch and make a small change:
   ```bash
   git checkout -b test-pr-workflow
   echo "# Test PR workflow" >> test.md
   git add test.md
   git commit -m "test: verify PR workflow"
   git push origin test-pr-workflow
   ```

2. Create a Pull Request on GitHub
3. Verify that:
   - CI tests run automatically
   - Branch protection prevents direct merge
   - All status checks must pass
   - PR requires approval

4. Clean up the test:
   ```bash
   git checkout main
   git branch -D test-pr-workflow
   # Delete the PR branch on GitHub through the web interface
   ```

## Step 8: Development Workflow Quick Reference

### For Contributors
```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/my-new-feature

# Make changes and test
make check  # Run tests, linting, formatting

# Commit and push
git add .
git commit -m "feat: add awesome new feature"
git push origin feature/my-new-feature

# Create PR on GitHub web interface
# Wait for CI and review
# Merge once approved
```

### For Maintainers
- Review PRs carefully
- Ensure CI passes before merge
- Use "Squash and merge" for clean history
- Delete feature branches after merge
- Tag releases when appropriate

## Troubleshooting

### Common Issues

**CI failing on Python version mismatch:**
- Check that all Python versions in `.github/workflows/test.yml` are supported

**Branch protection blocking pushes:**
- This is expected! All changes should go through PRs

**Status checks not appearing:**
- Make sure to push a commit after setting up branch protection
- Status check names must match exactly what's in the workflow

**Pre-commit hooks failing:**
- Run `make lint` to fix formatting issues
- Run `make test` to ensure tests pass

## Next Steps

1. ✅ Repository created and configured
2. ✅ Branch protection enabled  
3. ✅ CI/CD pipeline running
4. 🎯 Start accepting contributions!

Your repository is now ready for collaborative development with a professional workflow!