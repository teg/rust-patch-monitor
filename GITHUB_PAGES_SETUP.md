# GitHub Pages Setup Guide

This guide explains how to set up and use GitHub Pages deployment for the Rust Patch Monitor web UI.

## 🚀 Overview

The GitHub Pages deployment system allows you to generate and host a static website with fresh patch analysis data. The workflow runs manually and deploys to `https://teg.github.io/rust-patch-monitor`.

## 📋 Setup Required

### 1. GitHub Repository Settings

You need to configure GitHub repository settings manually:

1. Go to **Settings** → **Pages** in your GitHub repository
2. Ensure **Source** is set to **GitHub Actions** (not "Deploy from a branch")
3. This enables custom deployment workflows

### 2. GitHub Secrets Configuration

Add your Anthropic API key as a repository secret:

1. Go to **Settings** → **Secrets and Variables** → **Actions**
2. Click **New repository secret**
3. Set:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Secret**: Your Claude API key

The `GITHUB_TOKEN` is provided automatically by GitHub Actions.

## 🎯 How to Deploy

### Manual Deployment

1. Go to the **Actions** tab in your GitHub repository
2. Select **"Deploy to GitHub Pages"** workflow
3. Click **"Run workflow"** 
4. Configure parameters (optional):
   - **Days back**: Number of days to look back for patches (default: 14)
   - **Max patches**: Maximum patch series to analyze (default: 10)
5. Click **"Run workflow"** to start

### What Happens During Deployment

The workflow will:

1. **Fetch Fresh Data**: Connect to Patchwork API to get latest Rust patches
2. **Run Analysis**: Use your Anthropic API key to analyze patches with Claude
3. **Generate Web UI**: Build the Astro-based dashboard with real data
4. **Deploy**: Upload static files to GitHub Pages

## 📊 Accessing Your Site

After successful deployment, your site will be available at:
**https://teg.github.io/rust-patch-monitor**

The site includes:
- Interactive dashboard with latest patch analysis
- Filtering and sorting capabilities  
- Detailed patch analysis powered by Claude
- Mobile-responsive design

## ⚙️ Workflow Configuration

### Default Parameters
- **Days back**: 14 days
- **Max patches**: 10 series
- **Comments**: Excluded for faster processing

### Workflow File Location
`.github/workflows/deploy-pages.yml`

### Required Permissions
The workflow uses these GitHub permissions:
- `contents: read` - Access repository content
- `pages: write` - Deploy to GitHub Pages
- `id-token: write` - OIDC authentication

## 💰 Cost Considerations

- **API Usage**: Each deployment makes calls to Anthropic's API (costs apply)
- **Manual Control**: You control when to refresh data and incur API costs
- **Typical Cost**: Analyzing 10 patch series ≈ $0.50-2.00 depending on patch complexity

## 🔧 Customization

### Changing Analysis Parameters

Edit the workflow inputs in `.github/workflows/deploy-pages.yml`:

```yaml
workflow_dispatch:
  inputs:
    days_back:
      default: '14'  # Change default lookback period
    max_patches:
      default: '10'  # Change max patches to analyze
```

### Deployment Frequency

The workflow is manual-only by design. To automate:

1. Add a `schedule` trigger to the workflow
2. Be aware this will increase API costs
3. Consider rate limiting and error handling

## 🚀 Future Enhancements

### PR Branch Deployments (Planned)

Future versions will support:
- PR preview deployments at `/pr-123/` paths
- Separate workflows for PR environments
- No conflicts with main branch deployments

### Integration Options

The system is designed for:
- Static hosting (GitHub Pages, Netlify, Vercel)
- CI/CD integration
- Custom domain configuration
- CDN deployment

## 🔍 Troubleshooting

### Common Issues

1. **"Pages not found"**: Ensure GitHub Pages is enabled and set to GitHub Actions
2. **"Missing API key"**: Check that `ANTHROPIC_API_KEY` secret is configured
3. **"Build failed"**: Check Actions logs for specific error messages
4. **"No patches found"**: Verify Patchwork API is accessible

### Debugging

View detailed logs in:
**Actions** tab → **Deploy to GitHub Pages** → Latest workflow run

## 📝 Technical Architecture

- **Static Site Generator**: Astro v5.13.4
- **Styling**: Tailwind CSS v4 + DaisyUI
- **Data Source**: Patchwork API + Claude analysis  
- **Build Process**: Node.js 20 + Python 3.11
- **Deployment**: GitHub Actions → GitHub Pages

The system generates a complete static website that requires no backend infrastructure to operate.