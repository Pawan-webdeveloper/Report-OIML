/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f1f8f7', 100: '#dcefeb', 200: '#b9ddd7', 300: '#87c3ba',
          400: '#58a69d', 500: '#388b82', 600: '#28736c', 700: '#245d58',
          800: '#214b48', 900: '#1d403e', 950: '#102b33',
        },
      },
      fontFamily: {
        sans: ['Aptos', 'Segoe UI', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['SFMono-Regular', 'Cascadia Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        panel: '0 1px 2px rgb(15 35 45 / 0.06), 0 8px 24px rgb(15 35 45 / 0.05)',
      },
    },
  },
  plugins: [],
};
