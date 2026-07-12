import typography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef1ff',
          100: '#e0e4ff',
          200: '#c7ccfe',
          300: '#a4a8fd',
          400: '#7f7cf9',
          500: '#6b5ff2',
          600: '#5b7bff',
          700: '#4f46e5',
          800: '#423cc4',
          900: '#39359f',
        },
        accent: {
          green: '#22c55e',
          'green-light': '#7ED321',
          orange: '#f97316',
          red: '#ef4444',
        },
        surface: {
          glass: 'rgba(255, 255, 255, 0.72)',
          'glass-hover': 'rgba(255, 255, 255, 0.88)',
          card: 'rgba(255, 255, 255, 0.85)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans SC', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '16px',
        button: '10px',
      },
      boxShadow: {
        card: '0 2px 12px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 8px 28px rgba(0, 0, 0, 0.10)',
        glass: '0 8px 32px rgba(0, 0, 0, 0.06)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
    },
  },
  plugins: [typography],
};
