// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://teg.github.io',
  base: '/rust-patch-monitor/',
  vite: {
    plugins: [tailwindcss()]
  }
});