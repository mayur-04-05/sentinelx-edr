/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom security-themed dark palette
        bgDark: "#0B0E14",
        bgCard: "#131822",
        bgInput: "#1B2230",
        borderDark: "#263147",
        accentBlue: "#3B82F6",
        accentRed: "#EF4444",
        accentYellow: "#F59E0B",
        accentGreen: "#10B981",
        textPrimary: "#F3F4F6",
        textSecondary: "#9CA3AF"
      }
    },
  },
  plugins: [],
}
