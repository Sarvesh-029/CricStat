/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#0a1628",
        charcoal: "#111827",
        card: "#1a2333",
        accent: "#3b82f6",
        green: "#22c55e",
        gold: "#f59e0b",
      },
    },
  },
  plugins: [],
}

