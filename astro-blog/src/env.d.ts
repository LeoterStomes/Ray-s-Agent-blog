/// <reference types="astro/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

interface ImportMetaEnv {
  readonly PUBLIC_API_BASE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
