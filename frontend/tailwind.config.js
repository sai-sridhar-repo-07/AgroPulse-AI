/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        agro: {
          green: {
            50:  "#f0fdf4",
            100: "#dcfce7",
            200: "#bbf7d0",
            300: "#86efac",
            400: "#4ade80",
            500: "#22c55e",
            600: "#16a34a",
            700: "#15803d",
            800: "#166534",
            900: "#14532d",
          },
          earth: {
            50:  "#fdf8f0",
            100: "#faefd8",
            200: "#f5ddb0",
            300: "#ecc578",
            400: "#e0a840",
            500: "#d4901a",
            600: "#b87312",
            700: "#8f5410",
            800: "#6b3d0f",
            900: "#4a2908",
          },
          sky: {
            500: "#0ea5e9",
            600: "#0284c7",
          },
          risk: {
            low:      "#22c55e",
            medium:   "#f59e0b",
            high:     "#ef4444",
            critical: "#7c3aed",
          }
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in":       "fadeIn 0.6s ease-out both",
        "fade-in-up":    "fadeInUp 0.6s ease-out both",
        "slide-up":      "slideUp 0.5s ease-out both",
        "scale-in":      "scaleIn 0.4s ease-out both",
        "float":         "float 6s ease-in-out infinite",
        "shimmer":       "shimmer 2s linear infinite",
        "pulse-slow":    "pulse 3s ease-in-out infinite",
        "bar-fill":      "barFill 1s ease-out both",
        "bounce-subtle": "bounceSub 0.5s ease-out both",
        "glow":          "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn:     { "0%": { opacity: "0" },                                              "100%": { opacity: "1" } },
        fadeInUp:   { "0%": { opacity: "0", transform: "translateY(24px)" },               "100%": { opacity: "1", transform: "translateY(0)" } },
        slideUp:    { "0%": { opacity: "0", transform: "translateY(32px)" },               "100%": { opacity: "1", transform: "translateY(0)" } },
        scaleIn:    { "0%": { opacity: "0", transform: "scale(0.92)" },                    "100%": { opacity: "1", transform: "scale(1)" } },
        float:      { "0%,100%": { transform: "translateY(0px)" },                         "50%": { transform: "translateY(-8px)" } },
        shimmer:    { "0%": { backgroundPosition: "-200% 0" },                             "100%": { backgroundPosition: "200% 0" } },
        barFill:    { "0%": { width: "0%" },                                               "100%": { width: "var(--bar-width)" } },
        bounceSub:  { "0%": { transform: "scale(0.95)" }, "60%": { transform: "scale(1.03)" }, "100%": { transform: "scale(1)" } },
        glow:       { "0%": { boxShadow: "0 0 5px rgba(34,197,94,0.3)" },                  "100%": { boxShadow: "0 0 20px rgba(34,197,94,0.6)" } },
      },
      animationDelay: {
        "100": "100ms",
        "200": "200ms",
        "300": "300ms",
        "400": "400ms",
        "500": "500ms",
        "600": "600ms",
        "700": "700ms",
      },
      backdropBlur: { xs: "2px" },
      boxShadow: {
        "card":    "0 4px 24px -4px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)",
        "card-lg": "0 12px 40px -8px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.04)",
        "glow-green": "0 0 24px rgba(34,197,94,0.25)",
        "glow-blue":  "0 0 24px rgba(14,165,233,0.25)",
        "glow-amber": "0 0 24px rgba(245,158,11,0.25)",
        "glow-purple":"0 0 24px rgba(139,92,246,0.25)",
      },
    },
  },
  plugins: [],
};
