import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        bg: '#080c14',
        panel: '#101826',
        ink: '#e7edf8',
        mute: '#8fa2c2',
        accent: '#23d3a1',
        warning: '#f3a447',
        danger: '#f45b69'
      },
      boxShadow: {
        glow: '0 12px 40px rgba(15, 209, 160, 0.15)'
      }
    }
  },
  plugins: []
};

export default config;
