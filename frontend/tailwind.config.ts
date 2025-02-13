import type { Config } from "tailwindcss";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // Twisty theme colors
        twisty: {
          primary: "#FF4D00",
          secondary: "#1A1D1F",
          gray: {
            50: "#F8F9FA",
            100: "#F4F5F6",
            200: "#E7E9EB",
            300: "#DFE2E4",
            400: "#B9BEC1",
            500: "#989EA2",
            600: "#6B7075",
            700: "#4A4E52",
            800: "#1A1D1F",
            900: "#0D0F10",
          },
          success: "#2DC96F",
          warning: "#FFB547",
          error: "#FF4747",
          info: "#3E7BFA",
        },
      },
      fontFamily: {
        twisty: [
          'Inter',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'sans-serif'
        ],
      },
      fontSize: {
        'twisty-xs': ['0.75rem', { lineHeight: '1rem' }],
        'twisty-sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'twisty-base': ['1rem', { lineHeight: '1.5rem' }],
        'twisty-lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'twisty-xl': ['1.25rem', { lineHeight: '1.75rem' }],
        'twisty-2xl': ['1.5rem', { lineHeight: '2rem' }],
        'twisty-3xl': ['1.875rem', { lineHeight: '2.25rem' }],
      },
      borderRadius: {
        'twisty-sm': '0.375rem',
        'twisty-md': '0.5rem',
        'twisty-lg': '0.75rem',
      },
      boxShadow: {
        'twisty-sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'twisty-md': '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        'twisty-lg': '0 10px 15px -3px rgb(0 0 0 / 0.1)',
      },
    },
  },
  plugins: [],
} satisfies Config;
