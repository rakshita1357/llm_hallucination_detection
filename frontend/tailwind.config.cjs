/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0a0a0a', // dark charcoal background
        accentRed: '#ff4d4d',
        accentBlue: '#4da6ff',
      },
      boxShadow: {
        'glow-red': '0 0 8px #ff4d4d',
        'glow-blue': '0 0 8px #4da6ff',
      },
    },
  },
  plugins: [],
};
