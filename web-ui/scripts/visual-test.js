#!/usr/bin/env node

/**
 * Visual regression testing script for Web UI
 * Captures various page states for comparison
 */

import puppeteer from 'puppeteer';
import fs from 'fs/promises';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const TEST_OUTPUT_DIR = path.join(__dirname, '..', 'visual-tests');
const BASELINE_DIR = path.join(TEST_OUTPUT_DIR, 'baseline');
const CURRENT_DIR = path.join(TEST_OUTPUT_DIR, 'current');

// Test scenarios to capture
const TEST_SCENARIOS = [
  {
    name: 'default-state',
    description: 'Default page load state',
    viewport: { width: 1920, height: 1080 },
    actions: []
  },
  {
    name: 'prompt-expanded',
    description: 'Prompt template section expanded',
    viewport: { width: 1920, height: 1080 },
    actions: [
      { type: 'click', selector: '#toggle-prompt' },
      { type: 'wait', duration: 500 }
    ]
  },
  {
    name: 'mobile-view',
    description: 'Mobile responsive layout',
    viewport: { width: 375, height: 667 },
    actions: []
  },
  {
    name: 'tablet-view',
    description: 'Tablet responsive layout', 
    viewport: { width: 768, height: 1024 },
    actions: []
  },
  {
    name: 'first-patch-selected',
    description: 'First patch series selected',
    viewport: { width: 1920, height: 1080 },
    actions: [
      { type: 'click', selector: '.patch-series-card:first-child' },
      { type: 'wait', duration: 500 }
    ]
  }
];

class VisualTester {
  constructor() {
    this.browser = null;
    this.serverProcess = null;
  }

  async startServer() {
    console.log('🚀 Starting development server...');
    
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
            console.log('✅ Server ready');
            resolve();
          }
        }
      });

      setTimeout(() => {
        if (!serverReady) {
          reject(new Error('Server timeout'));
        }
      }, 30000);
    });
  }

  async setupBrowser() {
    console.log('🌐 Launching browser...');
    
    this.browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  }

  async runScenario(scenario, outputDir) {
    console.log(`📸 Running scenario: ${scenario.name}`);
    
    const page = await this.browser.newPage();
    await page.setViewport(scenario.viewport);
    
    // Navigate to the page
    await page.goto('http://localhost:4321/rust-patch-monitor/', {
      waitUntil: 'networkidle2',
      timeout: 10000
    });

    // Execute any required actions
    for (const action of scenario.actions) {
      try {
        switch (action.type) {
          case 'click':
            const element = await page.$(action.selector);
            if (element) {
              await element.click();
            } else {
              console.log(`⚠️  Element not found: ${action.selector}`);
            }
            break;
            
          case 'wait':
            await page.waitForTimeout(action.duration);
            break;
        }
      } catch (error) {
        console.log(`⚠️  Action failed: ${error.message}`);
      }
    }

    // Take screenshot
    const screenshotPath = path.join(outputDir, `${scenario.name}.png`);
    await page.screenshot({
      path: screenshotPath,
      fullPage: true
    });

    await page.close();
    console.log(`  ✓ ${scenario.name}.png`);
  }

  async generateReport(mode) {
    const reportPath = path.join(TEST_OUTPUT_DIR, `report-${mode}.json`);
    const report = {
      timestamp: new Date().toISOString(),
      mode: mode,
      scenarios: TEST_SCENARIOS.map(s => ({
        name: s.name,
        description: s.description,
        viewport: s.viewport,
        screenshot: `${s.name}.png`
      })),
      summary: `Generated ${TEST_SCENARIOS.length} visual test screenshots in ${mode} mode`
    };

    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    console.log(`📋 Report saved: report-${mode}.json`);
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
    if (this.serverProcess) {
      this.serverProcess.kill();
    }
  }

  async run(mode = 'current') {
    const outputDir = mode === 'baseline' ? BASELINE_DIR : CURRENT_DIR;
    
    try {
      // Ensure output directory exists
      await fs.mkdir(outputDir, { recursive: true });
      
      console.log(`🧪 Visual testing mode: ${mode}`);
      
      await this.startServer();
      await this.setupBrowser();
      
      // Wait for server to be fully ready
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Run all scenarios
      for (const scenario of TEST_SCENARIOS) {
        await this.runScenario(scenario, outputDir);
      }
      
      await this.generateReport(mode);
      
      console.log('\n✅ Visual testing completed!');
      console.log(`📁 Screenshots saved to: ${outputDir}`);
      
    } catch (error) {
      console.error('❌ Visual testing failed:', error.message);
    } finally {
      await this.cleanup();
    }
  }
}

// Parse command line arguments
const mode = process.argv[2] || 'current';

if (!['baseline', 'current'].includes(mode)) {
  console.log('Usage: npm run test:visual [baseline|current]');
  console.log('  baseline - Create baseline screenshots');
  console.log('  current  - Create current screenshots (default)');
  process.exit(1);
}

const tester = new VisualTester();
await tester.run(mode);