#!/usr/bin/env node

/**
 * Debug script for Rust Patch Monitor Web UI
 * Provides comprehensive debugging capabilities for Claude Code
 */

import puppeteer from 'puppeteer';
import fs from 'fs/promises';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DEBUG_OUTPUT_DIR = path.join(__dirname, '..', 'debug-output');
const SCREENSHOT_DIR = path.join(DEBUG_OUTPUT_DIR, 'screenshots');
const LOGS_DIR = path.join(DEBUG_OUTPUT_DIR, 'logs');

// Ensure output directories exist
await fs.mkdir(SCREENSHOT_DIR, { recursive: true });
await fs.mkdir(LOGS_DIR, { recursive: true });

console.log('🔧 Starting Web UI Debug Session...\n');

class WebUIDebugger {
  constructor() {
    this.browser = null;
    this.page = null;
    this.serverProcess = null;
    this.logs = [];
  }

  async log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${type.toUpperCase()}] ${message}`;
    console.log(logEntry);
    this.logs.push(logEntry);
  }

  async startDevServer() {
    await this.log('Starting Astro dev server...');
    
    return new Promise((resolve, reject) => {
      this.serverProcess = spawn('npm', ['run', 'dev'], {
        cwd: path.join(__dirname, '..'),
        stdio: 'pipe'
      });

      let serverReady = false;
      
      this.serverProcess.stdout.on('data', (data) => {
        const output = data.toString();
        if (output.includes('ready in') || output.includes('Local')) {
          if (!serverReady) {
            serverReady = true;
            this.log('Dev server started successfully');
            resolve();
          }
        }
      });

      this.serverProcess.stderr.on('data', (data) => {
        this.log(`Server Error: ${data.toString()}`, 'error');
      });

      // Timeout after 30 seconds
      setTimeout(() => {
        if (!serverReady) {
          reject(new Error('Server failed to start within 30 seconds'));
        }
      }, 30000);
    });
  }

  async launchBrowser() {
    await this.log('Launching headless browser...');
    
    this.browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    this.page = await this.browser.newPage();
    
    // Enable console logging
    this.page.on('console', (msg) => {
      this.log(`Browser Console [${msg.type()}]: ${msg.text()}`);
    });

    // Capture JavaScript errors
    this.page.on('pageerror', (error) => {
      this.log(`JavaScript Error: ${error.message}`, 'error');
    });

    // Capture network failures
    this.page.on('requestfailed', (request) => {
      this.log(`Network Error: ${request.url()} - ${request.failure().errorText}`, 'error');
    });

    await this.page.setViewport({ width: 1920, height: 1080 });
  }

  async captureScreenshots() {
    await this.log('Capturing screenshots...');

    const url = 'http://localhost:4321/rust-patch-monitor/';
    
    try {
      await this.page.goto(url, { waitUntil: 'networkidle2', timeout: 10000 });
      
      // Full page screenshot
      await this.page.screenshot({
        path: path.join(SCREENSHOT_DIR, 'full-page.png'),
        fullPage: true
      });
      
      // Desktop viewport
      await this.page.setViewport({ width: 1920, height: 1080 });
      await this.page.screenshot({
        path: path.join(SCREENSHOT_DIR, 'desktop-viewport.png')
      });
      
      // Tablet viewport  
      await this.page.setViewport({ width: 768, height: 1024 });
      await this.page.screenshot({
        path: path.join(SCREENSHOT_DIR, 'tablet-viewport.png')
      });
      
      // Mobile viewport
      await this.page.setViewport({ width: 375, height: 667 });
      await this.page.screenshot({
        path: path.join(SCREENSHOT_DIR, 'mobile-viewport.png')
      });

      await this.log('Screenshots captured successfully');
      
    } catch (error) {
      await this.log(`Screenshot capture failed: ${error.message}`, 'error');
    }
  }

  async testInteractivity() {
    await this.log('Testing page interactivity...');
    
    try {
      // Test prompt template toggle
      await this.page.setViewport({ width: 1920, height: 1080 });
      await this.page.goto('http://localhost:4321/rust-patch-monitor/', { waitUntil: 'networkidle2' });
      
      const toggleButton = await this.page.$('#toggle-prompt');
      if (toggleButton) {
        await this.log('Found prompt toggle button, testing click...');
        await toggleButton.click();
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Take screenshot after toggle
        await this.page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'prompt-expanded.png')
        });
        
        await this.log('Prompt toggle test completed');
      } else {
        await this.log('Prompt toggle button not found', 'warning');
      }

      // Test patch series selection if available
      const patchCards = await this.page.$$('.patch-series-card');
      if (patchCards.length > 0) {
        await this.log(`Found ${patchCards.length} patch series cards, testing selection...`);
        await patchCards[0].click();
        await new Promise(resolve => setTimeout(resolve, 500));
        
        await this.page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'patch-selected.png')
        });
        
        await this.log('Patch selection test completed');
      }

    } catch (error) {
      await this.log(`Interactivity test failed: ${error.message}`, 'error');
    }
  }

  async generateReport() {
    await this.log('Generating debug report...');
    
    const report = {
      timestamp: new Date().toISOString(),
      url: 'http://localhost:4321/rust-patch-monitor/',
      screenshots: [
        'full-page.png',
        'desktop-viewport.png', 
        'tablet-viewport.png',
        'mobile-viewport.png',
        'prompt-expanded.png',
        'patch-selected.png'
      ],
      logs: this.logs,
      summary: {
        total_logs: this.logs.length,
        errors: this.logs.filter(log => log.includes('[ERROR]')).length,
        warnings: this.logs.filter(log => log.includes('[WARNING]')).length
      }
    };

    const reportPath = path.join(LOGS_DIR, 'debug-report.json');
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    
    // Also create a readable summary
    const summaryPath = path.join(LOGS_DIR, 'debug-summary.txt');
    const summary = `
Rust Patch Monitor Web UI Debug Report
=====================================
Generated: ${report.timestamp}
URL: ${report.url}

Summary:
- Total log entries: ${report.summary.total_logs}
- Errors: ${report.summary.errors}
- Warnings: ${report.summary.warnings}

Screenshots captured:
${report.screenshots.map(s => `- ${s}`).join('\n')}

Full logs available in: debug-report.json
Screenshots available in: screenshots/

${report.summary.errors > 0 ? '⚠️  ERRORS DETECTED - Review logs for details' : '✅ No errors detected'}
`;

    await fs.writeFile(summaryPath, summary);
    await this.log('Debug report generated');
  }

  async cleanup() {
    await this.log('Cleaning up...');
    
    if (this.browser) {
      await this.browser.close();
    }
    
    if (this.serverProcess) {
      this.serverProcess.kill();
    }
  }

  async run() {
    try {
      await this.startDevServer();
      await this.launchBrowser();
      
      // Wait a moment for server to be fully ready
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      await this.captureScreenshots();
      await this.testInteractivity();
      await this.generateReport();
      
      console.log('\n✅ Debug session completed successfully!');
      console.log(`📁 Output directory: ${DEBUG_OUTPUT_DIR}`);
      console.log(`📸 Screenshots: ${SCREENSHOT_DIR}`);
      console.log(`📋 Logs: ${LOGS_DIR}`);
      
    } catch (error) {
      await this.log(`Debug session failed: ${error.message}`, 'error');
      console.error('❌ Debug session failed:', error.message);
    } finally {
      await this.cleanup();
    }
  }
}

// Run the debug session
const debug = new WebUIDebugger();
await debug.run();