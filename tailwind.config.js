/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        stone: {
          50: '#fafaf9',
          100: '#f5f5f4',
          800: '#292524',
          900: '#1c1917',
        },
      },
      fontFamily: {
        korean: ['"Noto Serif KR"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
