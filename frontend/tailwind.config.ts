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
          sidebar: "#0b1120",
          "sidebar-hover": "#161f35",
          "sidebar-active": "#1e2d50",
          accent: "#4f46e5",
          "accent-light": "#6366f1",
          "accent-muted": "#eef2ff",
        },
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)",
        "card-hover": "0 4px 12px 0 rgb(0 0 0 / 0.08), 0 2px 4px -1px rgb(0 0 0 / 0.04)",
        "card-lg": "0 8px 24px 0 rgb(0 0 0 / 0.08), 0 4px 8px -2px rgb(0 0 0 / 0.06)",
        topbar: "0 1px 0 0 rgb(0 0 0 / 0.06)",
        sidebar: "1px 0 0 0 rgb(0 0 0 / 0.15)",
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
        lg: "0.5rem",
      },
      backgroundImage: {
        "sidebar-gradient": "linear-gradient(180deg, #0b1120 0%, #111827 100%)",
        "accent-gradient": "linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)",
        "card-gradient": "linear-gradient(135deg, #f8faff 0%, #ffffff 100%)",
      },
      animation: {
        "fade-in": "fadeIn 0.15s ease-out",
        "slide-in": "slideIn 0.2s ease-out",
        "pulse-soft": "pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(-8px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [],
} satisfies Config;
