/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        rustlinux: {
          "primary": "#f97316",        // Modern accent orange
          "primary-content": "#0b0f14",
          "secondary": "#7dd3fc",      // Light blue for accents
          "accent": "#22d3ee",         // Cyan for highlights
          "neutral": "#111827",        // Dark neutral
          "base-100": "#0f172a",       // Dark background
          "base-200": "#0b1220",       // Darker background
          "base-300": "#0a0f1b",       // Darkest background
          "info": "#38bdf8",
          "success": "#22c55e",
          "warning": "#f59e0b",
          "error": "#ef4444",
        },
      },
    ],
    darkTheme: "dark",
    base: true,
    styled: true,
    utils: true,
  },
}