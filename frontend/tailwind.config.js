/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Clash Display'", "sans-serif"],
        body: ["'Cabinet Grotesk'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        ink: "#0A0A0F",
        surface: "#111118",
        card: "#16161F",
        border: "#1E1E2E",
        accent: "#6EE7B7",
        accentDim: "#34D399",
        accentGlow: "#10B981",
        warn: "#FBBF24",
        danger: "#F87171",
        muted: "#4B5563",
        subtle: "#6B7280",
        light: "#D1FAE5",
      },
      boxShadow: {
        glow: "0 0 40px rgba(110, 231, 183, 0.15)",
        glowSm: "0 0 20px rgba(110, 231, 183, 0.1)",
        card: "0 4px 24px rgba(0,0,0,0.4)",
      },
      animation: {
        "fade-up": "fadeUp 0.6s ease forwards",
        "fade-in": "fadeIn 0.4s ease forwards",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 2s infinite",
        "spin-slow": "spin 3s linear infinite",
        "score-fill": "scoreFill 1.5s ease forwards",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        scoreFill: {
          "0%": { "stroke-dashoffset": "283" },
          "100%": { "stroke-dashoffset": "var(--target-offset)" },
        },
      },
    },
  },
  plugins: [],
};
