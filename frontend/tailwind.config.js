/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        lenny: {
          50: '#fef7ee',
          100: '#fdedd6',
          200: '#fad7ac',
          300: '#f6ba77',
          400: '#f19441',
          500: '#ee771b', // Lenny brand orange
          600: '#df5c12',
          700: '#b94311',
          800: '#933615',
          900: '#772e15',
          950: '#401509',
        },
        surface: {
          dark: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          hover: '#273549'
        }
      }
    },
  },
  plugins: [],
}
