/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        panel: "rgb(var(--color-panel) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        signal: "rgb(var(--color-signal) / <alpha-value>)"
      }
    }
  },
  plugins: []
};
