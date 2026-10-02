export const SITE = {
  title: "Ray的垃圾站",
  subtitle: '个人博客',
  description: '技术、设计、生活与产品思考',
  lang: 'zh-CN',
  author: 'Ray',
} as const;

export const API = {
  BASE: '/api',
  TIMEOUT: 15000,
  ENDPOINTS: {
    LOGIN: '/user/login',
    REGISTER: '/user/add',
    CURRENT_USER: '/user/current',
    UPDATE_PROFILE: '/user/profile',
    UPDATE_PASSWORD: '/user/password',
    ARTICLES: '/knowledge/article/page',
    ARTICLE_DETAIL: (id: string) => `/knowledge/article/${id}`,
    ARTICLE_READ: (id: string) => `/knowledge/article/${id}/read`,
    CATEGORIES: '/knowledge/category/tree',
    FAVORITES: '/knowledge/favorite/page',
    FAVORITE_STATUS: (id: string) => `/knowledge/favorite/${id}/status`,
    FAVORITE_TOGGLE: (id: string) => `/knowledge/favorite/${id}`,
    CHAT_STREAM: '/psychological-chat/stream',
    CHAT_SESSION_START: '/psychological-chat/session/start',
    UPLOAD_IMAGE: '/file/simple/upload/image',
  },
} as const;

export const NAV_LINKS = [
  { href: '/', label: '首页' },
  { href: '/blog', label: '文章' },
  { href: '/projects', label: '项目' },
  { href: '/about', label: '关于' },
] as const;
