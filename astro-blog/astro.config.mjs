import { defineConfig } from 'astro/config';
import vue from '@astrojs/vue';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node';

export default defineConfig({
  integrations: [
    vue(),
    tailwind({ applyBaseStyles: false }),
  ],
  prefetch: true,
  devToolbar: { enabled: false },
  adapter: node({ mode: 'standalone' }),
  server: {
    port: 4321,
  },
  vite: {
    server: {
      proxy: {
        '/api': 'http://localhost:1235',
        '/uploads': 'http://localhost:1235',
      },
    },
    resolve: {
      alias: {
        '@': '/src',
        '@components': '/src/components',
        '@layouts': '/src/layouts',
        '@lib': '/src/lib',
        '@styles': '/src/styles',
      },
    },
  },
});
