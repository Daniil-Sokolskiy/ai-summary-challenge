import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#111827',
          soft: '#4b5563',
          muted: '#6b7280',
        },
        line: '#e5e7eb',
        surface: '#f8fafc',
        brand: {
          DEFAULT: '#4f46e5',
          soft: '#eef2ff',
        },
      },
      borderRadius: {
        card: '14px',
      },
      keyframes: {
        shimmer: {
          '0%': { opacity: '0.45' },
          '50%': { opacity: '1' },
          '100%': { opacity: '0.45' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}

export default config
