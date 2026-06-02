import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          sidebar: "#0f172a",
          accent: "#4f46e5",
        },
      },
      borderRadius: {
        xl: "0.75rem",
        lg: "0.5rem",
      },
    },
  },
  plugins: [],
} satisfies Config;
