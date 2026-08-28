import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07111f",
          900: "#0b1728",
          800: "#122033",
          700: "#1b2b43",
          600: "#2a3d58",
        },
        mist: {
          50: "#f4f7fb",
          100: "#e8eef6",
          300: "#9db0c8",
          400: "#7c93ae",
        },
        accent: {
          400: "#3d9cf0",
          500: "#2f7de1",
          600: "#1f63c4",
        },
        gain: {
          400: "#3dbe8c",
          500: "#1f9d6e",
        },
        warn: {
          400: "#e0a454",
          500: "#c9842a",
        },
        danger: {
          400: "#e06b6b",
          500: "#c44a4a",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Segoe UI", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      boxShadow: {
        panel: "0 1px 2px rgba(7,17,31,0.06), 0 12px 32px rgba(7,17,31,0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
