#!/usr/bin/env node

/**
 * Build analyzer for detailed build output analysis
 * Helps Claude understand build issues and performance
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DIST_DIR = path.join(__dirname, '..', 'dist');
const ANALYSIS_DIR = path.join(__dirname, '..', 'build-analysis');

class BuildAnalyzer {
  constructor() {
    this.analysis = {
      timestamp: new Date().toISOString(),
      build_success: false,
      files: [],
      assets: [],
      errors: [],
      warnings: [],
      performance: {},
      recommendations: []
    };
  }

  async analyzeBuildOutput() {
    console.log('🔍 Analyzing build output...');
    
    try {
      // Check if build was successful
      const indexExists = await this.fileExists(path.join(DIST_DIR, 'index.html'));
      this.analysis.build_success = indexExists;
      
      if (!indexExists) {
        this.analysis.errors.push('Main index.html file not found in dist/');
        return;
      }

      // Analyze all files in dist
      await this.analyzeDirectory(DIST_DIR, '');
      
      // Analyze index.html specifically
      await this.analyzeIndexHtml();
      
      // Check for common issues
      await this.checkCommonIssues();
      
      console.log('✅ Build analysis complete');
      
    } catch (error) {
      this.analysis.errors.push(`Analysis failed: ${error.message}`);
      console.error('❌ Analysis failed:', error.message);
    }
  }

  async analyzeDirectory(dirPath, relativePath) {
    try {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        const relPath = path.join(relativePath, entry.name);
        
        if (entry.isDirectory()) {
          await this.analyzeDirectory(fullPath, relPath);
        } else {
          const stats = await fs.stat(fullPath);
          const fileInfo = {
            path: relPath,
            size: stats.size,
            size_mb: (stats.size / 1024 / 1024).toFixed(2),
            modified: stats.mtime.toISOString(),
            type: this.getFileType(entry.name)
          };
          
          if (fileInfo.type === 'asset') {
            this.analysis.assets.push(fileInfo);
          } else {
            this.analysis.files.push(fileInfo);
          }
        }
      }
    } catch (error) {
      this.analysis.warnings.push(`Could not analyze directory ${relativePath}: ${error.message}`);
    }
  }

  async analyzeIndexHtml() {
    try {
      const indexPath = path.join(DIST_DIR, 'index.html');
      const content = await fs.readFile(indexPath, 'utf-8');
      
      // Check for common issues in HTML
      const issues = [];
      
      if (!content.includes('<title>')) {
        issues.push('Missing page title');
      }
      
      if (!content.includes('viewport')) {
        issues.push('Missing viewport meta tag');
      }
      
      if (content.includes('undefined') || content.includes('null')) {
        issues.push('Potential undefined/null values in rendered content');
      }
      
      // Check for successful hydration indicators
      if (content.includes('astro-island')) {
        this.analysis.performance.has_islands = true;
      }
      
      // Count script tags
      const scriptMatches = content.match(/<script[^>]*>/g) || [];
      this.analysis.performance.script_tags = scriptMatches.length;
      
      // Count CSS links
      const cssMatches = content.match(/<link[^>]*stylesheet[^>]*>/g) || [];
      this.analysis.performance.css_links = cssMatches.length;
      
      this.analysis.performance.html_size_kb = (content.length / 1024).toFixed(2);
      
      if (issues.length > 0) {
        this.analysis.warnings.push(...issues);
      }
      
    } catch (error) {
      this.analysis.errors.push(`Could not analyze index.html: ${error.message}`);
    }
  }

  async checkCommonIssues() {
    // Check for oversized assets
    const largeAssets = this.analysis.assets.filter(asset => asset.size > 1024 * 1024); // > 1MB
    if (largeAssets.length > 0) {
      this.analysis.warnings.push(`Large assets detected: ${largeAssets.map(a => `${a.path} (${a.size_mb}MB)`).join(', ')}`);
    }

    // Check for missing favicon
    const hasFavicon = this.analysis.files.some(f => f.path.includes('favicon'));
    if (!hasFavicon) {
      this.analysis.warnings.push('No favicon found');
    }

    // Performance recommendations
    if (this.analysis.performance.css_links > 3) {
      this.analysis.recommendations.push('Consider bundling CSS files to reduce requests');
    }
    
    if (this.analysis.performance.script_tags > 5) {
      this.analysis.recommendations.push('Consider bundling JavaScript files');
    }

    const totalSize = this.analysis.files.reduce((sum, f) => sum + f.size, 0) + 
                      this.analysis.assets.reduce((sum, a) => sum + a.size, 0);
    
    this.analysis.performance.total_size_mb = (totalSize / 1024 / 1024).toFixed(2);

    if (totalSize > 10 * 1024 * 1024) { // > 10MB
      this.analysis.recommendations.push('Build output is quite large, consider optimization');
    }
  }

  getFileType(filename) {
    const ext = path.extname(filename).toLowerCase();
    const assetExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.woff', '.woff2', '.ttf'];
    return assetExtensions.includes(ext) ? 'asset' : 'file';
  }

  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async generateReport() {
    console.log('📋 Generating analysis report...');
    
    // Ensure analysis directory exists
    await fs.mkdir(ANALYSIS_DIR, { recursive: true });
    
    // Save detailed JSON report
    const jsonPath = path.join(ANALYSIS_DIR, 'build-analysis.json');
    await fs.writeFile(jsonPath, JSON.stringify(this.analysis, null, 2));
    
    // Generate readable summary
    const summary = this.generateSummary();
    const summaryPath = path.join(ANALYSIS_DIR, 'build-summary.txt');
    await fs.writeFile(summaryPath, summary);
    
    console.log(`📁 Analysis saved to: ${ANALYSIS_DIR}`);
    console.log('\n' + summary);
  }

  generateSummary() {
    const a = this.analysis;
    
    return `
Rust Patch Monitor Web UI - Build Analysis
=========================================
Generated: ${a.timestamp}

Build Status: ${a.build_success ? '✅ SUCCESS' : '❌ FAILED'}

Files & Assets:
- Files: ${a.files.length}
- Assets: ${a.assets.length}  
- Total Size: ${a.performance.total_size_mb || 'N/A'} MB

Performance Metrics:
- HTML Size: ${a.performance.html_size_kb || 'N/A'} KB
- Script Tags: ${a.performance.script_tags || 0}
- CSS Links: ${a.performance.css_links || 0}
- Has Islands: ${a.performance.has_islands ? 'Yes' : 'No'}

Issues Found:
- Errors: ${a.errors.length}
- Warnings: ${a.warnings.length}

${a.errors.length > 0 ? `
ERRORS:
${a.errors.map(e => `❌ ${e}`).join('\n')}
` : ''}

${a.warnings.length > 0 ? `
WARNINGS:
${a.warnings.map(w => `⚠️  ${w}`).join('\n')}
` : ''}

${a.recommendations.length > 0 ? `
RECOMMENDATIONS:
${a.recommendations.map(r => `💡 ${r}`).join('\n')}
` : ''}

Largest Files:
${[...a.files, ...a.assets]
  .sort((a, b) => b.size - a.size)
  .slice(0, 5)
  .map(f => `📄 ${f.path} (${f.size_mb}MB)`)
  .join('\n')}

${a.build_success ? '🎉 Build completed successfully!' : '💥 Build failed - see errors above'}
`;
  }

  async run() {
    console.log('🔧 Starting build analysis...\n');
    
    await this.analyzeBuildOutput();
    await this.generateReport();
  }
}

const analyzer = new BuildAnalyzer();
await analyzer.run();