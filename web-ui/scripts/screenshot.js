#!/usr/bin/env node

/**
 * Simple screenshot capture script for quick visual debugging
 */

import puppeteer from 'puppeteer';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OUTPUT_DIR = path.join(__dirname, '..', 'screenshots');

// Ensure output directory exists
await fs.mkdir(OUTPUT_DIR, { recursive: true });

console.log('📸 Taking quick screenshot...');

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox', '--disable-setuid-sandbox']
});

const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080 });

try {
  // Try to screenshot the live GitHub Pages site first
  const liveUrl = 'https://teg.github.io/rust-patch-monitor/';
  console.log(`Attempting to screenshot live site: ${liveUrl}`);
  
  await page.goto(liveUrl, { waitUntil: 'networkidle2', timeout: 10000 });
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `live-site-${timestamp}.png`;
  
  await page.screenshot({
    path: path.join(OUTPUT_DIR, filename),
    fullPage: true
  });
  
  console.log(`✅ Screenshot saved: ${filename}`);
  
} catch (error) {
  console.log(`⚠️  Live site not accessible: ${error.message}`);
  console.log('💡 Run `npm run debug` for local development server screenshots');
} finally {
  await browser.close();
}