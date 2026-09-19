/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        panel: "#f7f8fb",
        accent: "#0f766e",
        signal: "#b45309"
      }
    }
  },
  plugins: []
};

