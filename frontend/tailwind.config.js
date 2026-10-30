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
        krishi: {
          bg: '#07101F',
          sidebar: '#0C1728',
          surface: '#111E31',
          elevated: '#17263A',
          border: '#26374D',
          'border-subtle': '#1B2B3F',
          primary: '#08A873',
          'primary-hover': '#09C486',
          'primary-soft': '#103C38',
          'text-primary': '#F5F8FC',
          'text-secondary': '#A9B7C8',
          'text-muted': '#718197',
          warning: '#F4B740',
          danger: '#EF6B73',
          info: '#55A9E8',
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#08A873',
          600: '#079264',
          700: '#067a53',
          800: '#056242',
          900: '#044c33',
          950: '#022e1f',
        }
      },
      fontFamily: {
        display: ['Outfit', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'glow-primary': '0 0 20px -3px rgba(5, 150, 105, 0.35)',
        'panel': '0 10px 30px -5px rgba(0, 0, 0, 0.08), 0 0 1px 1px rgba(0, 0, 0, 0.04)',
        'depth': '0 20px 40px -15px rgba(5, 150, 105, 0.18), 0 0 2px 1px rgba(0, 0, 0, 0.04)',
      }
    },
  },
  plugins: [],
}

