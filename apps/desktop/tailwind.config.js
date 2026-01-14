/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'agp': {
          'dark': '#0a0a0f',
          'darker': '#050508',
          'card': '#0d0d14',
          'border': '#1a1a2e',
          'accent': '#00ff88',
          'accent-blue': '#00b4ff',
          'danger': '#ff3366',
          'warning': '#ffaa00',
        }
      }
    },
  },
  plugins: [],
}
