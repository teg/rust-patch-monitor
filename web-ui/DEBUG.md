# Web UI Debugging Guide

This guide explains how to debug the Rust Patch Monitor Web UI using the enhanced debugging tools available to Claude Code.

## 🔧 Available Debugging Tools

### 1. Quick Screenshot (`npm run screenshot`)
Takes a screenshot of the live GitHub Pages site for quick visual inspection.

**Output**: `screenshots/live-site-{timestamp}.png`

```bash
npm run screenshot
```

### 2. Build Analysis (`npm run analyze`)
Analyzes the build output for errors, warnings, and performance issues.

**Output**: 
- `build-analysis/build-analysis.json` - Detailed JSON report
- `build-analysis/build-summary.txt` - Human-readable summary

```bash
npm run analyze
```

**What it checks:**
- ✅ Build success/failure
- 📊 File sizes and performance metrics  
- ⚠️ Common issues (missing favicon, large assets)
- 💡 Optimization recommendations
- 🏗️ HTML structure analysis

### 3. Full Debug Session (`npm run debug`)
Comprehensive debugging with local dev server, screenshots, and interactivity testing.

**Output**: 
- `debug-output/screenshots/` - Multiple viewports and states
- `debug-output/logs/` - Detailed logs and reports

```bash
npm run debug
```

**What it captures:**
- 📱 Multiple device viewports (desktop, tablet, mobile)
- 🖱️ Interactive states (prompt expanded, patch selected)
- 🐛 JavaScript errors and console output
- 🌐 Network request failures
- 📋 Comprehensive debug report

### 4. Visual Testing (`npm run test:visual`)
Creates baseline or comparison screenshots for visual regression testing.

```bash
# Create baseline screenshots
npm run test:visual baseline

# Create current screenshots for comparison
npm run test:visual current
```

**Output**: `visual-tests/baseline/` or `visual-tests/current/`

## 🚀 CI Integration

The GitHub Actions workflow automatically:

1. **Builds** the web UI with enhanced error reporting
2. **Analyzes** build output for issues
3. **Screenshots** the live site (if accessible)
4. **Uploads** all debug artifacts for Claude to review

**Artifacts available in CI:**
- `web-ui-build` - Built site files
- `debug-output` - Screenshots, analysis, and logs

## 📖 How Claude Uses These Tools

### For Build Issues:
1. Check `build-analysis.json` for errors and warnings
2. Review `build-summary.txt` for human-readable issues
3. Examine build logs if compilation fails

### For Visual Issues:
1. View screenshots from various viewports
2. Compare interactive states (expanded/collapsed)
3. Check responsive behavior across devices
4. Analyze visual regressions between versions

### For Performance Issues:
1. Review file sizes and optimization recommendations
2. Check for oversized assets or bundles
3. Analyze HTML structure for inefficiencies

## 🛠️ Local Development Debugging

### Quick Visual Check
```bash
npm run screenshot
```

### Full Analysis After Changes
```bash
npm run analyze
```

### Comprehensive Testing
```bash
npm run debug
```

### Compare Visual Changes
```bash
# Before changes
npm run test:visual baseline

# After changes  
npm run test:visual current

# Compare baseline/ and current/ directories
```

## 📁 Output Structure

```
web-ui/
├── screenshots/           # Quick screenshots
├── build-analysis/        # Build analysis reports
├── debug-output/          # Full debug session output
│   ├── screenshots/       # Multiple viewports and states
│   └── logs/             # Debug logs and reports
└── visual-tests/          # Baseline vs current comparisons
    ├── baseline/
    └── current/
```

## 🎯 Claude Code Integration

All debugging outputs are designed to be:

✅ **Machine-readable** - JSON reports for automated analysis  
✅ **Human-readable** - Text summaries for quick review  
✅ **Visual** - Screenshots for UI analysis  
✅ **Comprehensive** - Multiple viewports and interaction states  
✅ **CI-integrated** - Automatic generation and artifact upload

This enables Claude to:
- 🔍 Diagnose build and runtime issues
- 📱 Verify responsive design behavior  
- 🎨 Analyze visual output and styling
- ⚡ Identify performance bottlenecks
- 🧪 Compare changes visually
- 🚀 Debug issues in CI/CD pipeline