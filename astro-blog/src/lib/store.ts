import { atom } from 'nanostores';
import type { UserInfo } from './auth';
import { getUser, isLoggedIn, getAvatarUrl } from './auth';

export const $isLoggedIn = atom<boolean>(isLoggedIn());
export const $currentUser = atom<UserInfo | null>(getUser());
export const $showAuthModal = atom<boolean>(false);
export const $authMode = atom<'login' | 'register'>('login');

/** 派生：当前用户头像完整 URL */
export const $avatarUrl = atom<string>('');
{
  const u = getUser();
  if (u) $avatarUrl.set(getAvatarUrl(u.avatar));
}

export function login(user: UserInfo, token: string) {
  localStorage.setItem('token', token);
  localStorage.setItem('userInfo', JSON.stringify(user));
  $isLoggedIn.set(true);
  $currentUser.set(user);
  $avatarUrl.set(getAvatarUrl(user.avatar));
  $showAuthModal.set(false);
}

export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('userInfo');
  $isLoggedIn.set(false);
  $currentUser.set(null);
  $avatarUrl.set('');
}

export function openAuth(mode: 'login' | 'register' = 'login') {
  $authMode.set(mode);
  $showAuthModal.set(true);
}

export function closeAuth() {
  $showAuthModal.set(false);
}

export function updateUser(user: UserInfo) {
  localStorage.setItem('userInfo', JSON.stringify(user));
  $currentUser.set({ ...user });
  $avatarUrl.set(getAvatarUrl(user.avatar));
}

// ── Agent 会话共享 ──
export const $agentSessionId = atom<string | null>(null);
