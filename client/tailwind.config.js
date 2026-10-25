/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          bg: "#0B0F19",       // Deep control room dark
          card: "#161E2E",     // Contrast card gray
          accent: "#2563EB",   // Electric blue active indicator
          accentHover: "#1D4ED8",
          warning: "#D97706",  // Safety orange
          critical: "#DC2626", // Danger red
          success: "#059669",  // Running green
          textMuted: "#9CA3AF" // Muted label white
        }
      }
    },
  },
  plugins: [],
}
