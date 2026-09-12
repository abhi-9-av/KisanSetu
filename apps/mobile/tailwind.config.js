/** @type {import('tailwindcss').Config} */
module.exports = {
  presets: [require('nativewind/preset')],
  content: ['./app/**/*.{js,jsx,ts,tsx}', './components/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#1f8a3e',
          dark: '#166b30',
          light: '#e6f5ea',
        },
        ink: '#1c1f1d',
        muted: '#6b746e',
        canvas: '#f4f5f4',
        accent: '#e08a2c',
      },
    },
  },
  plugins: [],
};
