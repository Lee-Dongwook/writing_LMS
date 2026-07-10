/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fbf1f2",
          100: "#f5dcdf",
          200: "#eabbc0",
          300: "#db8f97",
          400: "#c85f6a",
          500: "#b23a45",
          600: "#a81d2d",
          700: "#8c1824",
          800: "#74161f",
          900: "#61151c",
        },
        // 먹(墨) — 제목·본문·주요 버튼
        ink: {
          DEFAULT: "#1a1a1a",
          soft: "#2c2c2c",
        },
        // 중립면·구분선(따뜻한 오프화이트 계열)
        surface: "#f6f5f3",
        line: "#e9e6e1",
      },
      borderRadius: {
        card: "22px",
        cta: "28px",
      },
      boxShadow: {
        lift: "0 16px 38px rgba(20,20,30,.08)",
      },
      fontFamily: {
        sans: [
          "Pretendard",
          "-apple-system",
          "BlinkMacSystemFont",
          "Apple SD Gothic Neo",
          "Malgun Gothic",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
