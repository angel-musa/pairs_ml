/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#050509",
        surface: "#0b0b1a",
        primary: "#7c3aed",
        secondary: "#a855f7",
      },
    },
  },
  plugins: [],
}
