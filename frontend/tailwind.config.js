/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef0fb',
          100: '#e0e3f8',
          200: '#c7ccf2',
          300: '#a5abe9',
          400: '#8387de',
          500: '#6567d4',
          600: '#5457c4',
          700: '#4749a8',
          800: '#3c3e88',
          900: '#34366d',
        },
      },
      fontFamily: {
        sans: [
          'Pretendard',
          '-apple-system',
          'BlinkMacSystemFont',
          'Apple SD Gothic Neo',
          'Malgun Gothic',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [],
}
