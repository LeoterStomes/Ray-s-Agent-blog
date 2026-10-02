export interface UserInfo {
  id: number;
  username: string;
  nickname?: string;
  avatar?: string;
  email?: string;
  phone?: string;
  bio?: string;
  roleType: number;
  user_type?: number;  // API 原始字段，兼容
}

/** 获取用户类型（兼容多种字段名） */
export function getUserType(user: UserInfo | null): number {
  if (!user) return 0;
  return user.user_type ?? user.roleType ?? 0;
}

const TOKEN_KEY = 'token';
const USER_KEY = 'userInfo';

/** 将头像路径转为完整 URL（API 可能返回完整路径或纯文件名） */
export function getAvatarUrl(avatar?: string): string {
  if (!avatar) return '';
  // 已经是完整 URL
  if (avatar.startsWith('http')) return avatar;
  // API 可能已经带了 /uploads 前缀，避免重复拼接
  if (avatar.startsWith('/uploads')) return avatar;
  // 纯文件名：补充前缀
  return `/uploads/avatars/${avatar}`;
}

export function getToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
}

export function getUser(): UserInfo | null {
  if (typeof localStorage === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserInfo;
  } catch {
    return null;
  }
}

export function setUser(user: UserInfo): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function removeUser(): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken() && !!getUser();
}

export function clearAuth(): void {
  removeToken();
  removeUser();
}
