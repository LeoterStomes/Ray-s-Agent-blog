<template>
  <div id="login-page">
    <!-- Left Panel: Animated Characters -->
    <div class="left-panel">
      <!-- 占位：保持 flex space-between 布局不变 -->
      <div class="logo" style="visibility:hidden"></div>

      <!-- Animated Characters -->
      <div class="characters-wrapper">
        <div class="scene" @mousemove="onSceneMouse">
          <!-- Purple character -->
          <div class="char char-purple" :class="{ shake: shaking }" :style="purpleStyle">
            <div class="eyes" :style="purpleEyeStyle">
              <AnimatedEye :size="18" :pupilSize="7" :mouseX="mx" :mouseY="my" :isBlinking="purpleBlink"
                :forceLookX="purpleLookX" :forceLookY="purpleLookY" />
              <AnimatedEye :size="18" :pupilSize="7" :mouseX="mx" :mouseY="my" :isBlinking="purpleBlink"
                :forceLookX="purpleLookX" :forceLookY="purpleLookY" />
            </div>
          </div>

          <!-- Black character -->
          <div class="char char-black" :class="{ shake: shaking }" :style="blackStyle">
            <div class="eyes" :style="blackEyeStyle">
              <AnimatedEye :size="16" :pupilSize="6" :mouseX="mx" :mouseY="my" :isBlinking="blackBlink"
                :forceLookX="blackLookX" :forceLookY="blackLookY" />
              <AnimatedEye :size="16" :pupilSize="6" :mouseX="mx" :mouseY="my" :isBlinking="blackBlink"
                :forceLookX="blackLookX" :forceLookY="blackLookY" />
            </div>
          </div>

          <!-- Orange character -->
          <div class="char char-orange" ref="orangeRef">
            <div class="eyes orange-eyes">
              <span class="bare-pupil" :style="orangePupilStyle" />
              <span class="bare-pupil" :style="orangePupilStyle" />
            </div>
          </div>

          <!-- Yellow character -->
          <div class="char char-yellow" ref="yellowRef">
            <div class="eyes yellow-eyes">
              <span class="bare-pupil" :style="yellowPupilStyle" />
              <span class="bare-pupil" :style="yellowPupilStyle" />
            </div>
            <div class="yellow-mouth" :style="yellowMouthStyle" />
          </div>
        </div>
      </div>

      <!-- 占位：保持 flex space-between 布局不变 -->
      <div class="footer-links" style="visibility:hidden"></div>
    </div>

    <!-- Right Panel: Form -->
    <div class="right-panel">
      <div class="form-container">
        <div class="sparkle-icon">
          <svg viewBox="0 0 24 24" fill="none"><path d="M12 2L13.5 9H10.5L12 2Z" fill="#1a1a2e"/><path d="M12 22L10.5 15H13.5L12 22Z" fill="#1a1a2e"/><path d="M2 12L9 10.5V13.5L2 12Z" fill="#1a1a2e"/><path d="M22 12L15 13.5V10.5L22 12Z" fill="#1a1a2e"/></svg>
        </div>

        <div class="form-header">
          <h1>{{ isLogin ? 'Welcome back!' : 'Create account' }}</h1>
          <p>{{ isLogin ? 'Please enter your details' : 'Join the blog community' }}</p>
        </div>

        <form @submit.prevent="submit">
          <div class="form-group">
            <label :class="error ? 'error-label' : ''">用户名</label>
            <div class="input-wrapper">
              <input v-model="form.username" type="text" placeholder="请输入用户名" autocomplete="off"
                @focus="onFocus" @blur="onBlur" />
            </div>
          </div>

          <div class="form-group">
            <label :class="error ? 'error-label' : ''">密码</label>
            <div class="input-wrapper">
              <input v-model="form.password" :type="showPwd ? 'text' : 'password'" placeholder="********"
                @focus="onPwdFocus" @blur="onPwdBlur" />
              <button type="button" class="toggle-password" @click="showPwd = !showPwd">
                <svg v-if="showPwd" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- ─── 注册专用字段 ─── -->
          <template v-if="!isLogin">
            <!-- 邮箱 -->
            <div class="form-group">
              <label>邮箱</label>
              <div class="input-wrapper">
                <input v-model="form.email" type="email" placeholder="your@email.com" autocomplete="off" />
              </div>
              <p class="email-hint">支持 QQ / 163 / 126 / Gmail / Outlook 邮箱</p>
            </div>

            <!-- 邮箱验证码 -->
            <div class="form-group">
              <label>邮箱验证码</label>
              <div class="captcha-row">
                <input
                  v-model="emailCode"
                  type="text"
                  maxlength="6"
                  placeholder="6位验证码"
                  autocomplete="off"
                  class="captcha-input"
                  style="flex:1;height:42px;letter-spacing:4px;text-align:center"
                />
                <button
                  type="button"
                  class="send-code-btn"
                  :disabled="countdown > 0 || sendingCode"
                  @click="sendEmailCode"
                >
                  {{ countdown > 0 ? `${countdown}s` : (sendingCode ? '发送中...' : '发送验证码') }}
                </button>
              </div>
            </div>

            <!-- 昵称 -->
            <div class="form-group">
              <label>昵称（可选）</label>
              <div class="input-wrapper">
                <input v-model="form.nickname" type="text" placeholder="给自己取个名字吧" autocomplete="off" />
              </div>
            </div>

            <!-- 图形验证码 — 仅在邮箱发送频率超限时出现 -->
            <div v-if="showCaptcha" class="form-group">
              <label>图形验证码</label>
              <div class="captcha-row">
                <img
                  v-if="captchaImg"
                  :src="captchaImg"
                  alt="验证码"
                  class="captcha-img"
                  @click="refreshCaptcha"
                  title="点击刷新"
                />
                <span v-else class="captcha-loading">加载中...</span>
                <button type="button" class="captcha-refresh" @click="refreshCaptcha" title="换一张">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
                  </svg>
                </button>
              </div>
              <div class="input-wrapper" style="margin-top:8px">
                <input
                  v-model="captchaCode"
                  type="text"
                  maxlength="4"
                  placeholder="请输入图形验证码"
                  autocomplete="off"
                  class="captcha-input"
                  style="height:42px;letter-spacing:6px;text-align:center;width:100%"
                />
              </div>
            </div>
          </template>

          <div v-if="errorMsg" class="error-msg show">{{ errorMsg }}</div>

          <button type="submit" class="btn-login" :disabled="loading">
            <span class="btn-text">{{ loading ? '处理中...' : (isLogin ? 'Log In' : 'Sign Up') }}</span>
            <div class="btn-hover-content">
              <span>{{ loading ? '处理中...' : (isLogin ? 'Log In' : 'Sign Up') }}</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
            </div>
          </button>
        </form>

        <div class="signup-link">
          {{ isLogin ? "Don't have an account?" : 'Already have an account?' }}
          <a href="#" @click.prevent="isLogin = !isLogin; errorMsg = ''">{{ isLogin ? 'Sign Up' : 'Log In' }}</a>
        </div>
        <div class="mt-4 text-center">
          <a href="/" class="text-xs text-gray-400 hover:text-gray-600">← 返回首页</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue';
import { request } from '@lib/api';
import { login as storeLogin } from '@lib/store';
import AnimatedEye from './AnimatedEye.vue';

// ── Form state ──
const isLogin = ref(true);
const loading = ref(false);
const errorMsg = ref('');
const error = computed(() => !!errorMsg.value);
const showPwd = ref(false);
const form = reactive({ username: '', password: '', nickname: '', email: '' });

// ── 邮箱验证码状态 ──
const emailCode = ref('');
const countdown = ref(0);
const sendingCode = ref(false);
let countdownTimer: ReturnType<typeof setInterval> | null = null;

async function sendEmailCode() {
  const email = form.email.trim();
  if (!email || !email.includes('@')) {
    errorMsg.value = '请先输入有效的邮箱地址';
    return;
  }
  if (countdown.value > 0 || sendingCode.value) return;
  errorMsg.value = '';
  sendingCode.value = true;

  try {
    const headers: Record<string, string> = {};
    // 如果需要图形验证码，带上
    if (showCaptcha.value) {
      headers['X-Captcha-Key'] = captchaKey.value;
      headers['X-Captcha-Code'] = captchaCode.value;
    }

    const res = await fetch('/api/email/send-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify({ email }),
    });
    const json = await res.json();

    if (json.code === '429' && json.data?.requireCaptcha) {
      // 触发图形验证码
      showCaptcha.value = true;
      errorMsg.value = json.msg;
      await fetchCaptcha();
    } else if (json.code === '503') {
      errorMsg.value = '邮件服务未配置，请联系管理员';
    } else if (json.code !== '200') {
      errorMsg.value = json.msg || '发送失败，请稍后重试';
    } else {
      errorMsg.value = '';
      captchaCode.value = '';
      showCaptcha.value = false;
      // 60 秒倒计时
      countdown.value = 60;
      countdownTimer = setInterval(() => {
        countdown.value--;
        if (countdown.value <= 0) {
          clearInterval(countdownTimer!);
          countdownTimer = null;
        }
      }, 1000);
    }
  } catch {
    errorMsg.value = '网络异常，请稍后重试';
  } finally {
    sendingCode.value = false;
  }
}

// ── Captcha state ──
const captchaKey = ref('');
const captchaImg = ref('');
const captchaCode = ref('');
const showCaptcha = ref(false);

async function fetchCaptcha() {
  try {
    const res = await fetch('/api/captcha/generate');
    if (!res.ok) return;
    captchaKey.value = res.headers.get('X-Captcha-Key') || '';
    const blob = await res.blob();
    captchaImg.value = URL.createObjectURL(blob);
  } catch {
    // 静默失败
  }
}

function refreshCaptcha() {
  if (captchaImg.value) URL.revokeObjectURL(captchaImg.value);
  captchaCode.value = '';
  fetchCaptcha();
}

// ── Animation state ──
const mx = ref(0);
const my = ref(0);
const typing = ref(false);
const pwdFocused = ref(false);

const purpleBlink = ref(false);
const blackBlink = ref(false);
let blinkTimers: ReturnType<typeof setTimeout>[] = [];

function startBlinks() {
  const runPurple = () => {
    const t = setTimeout(() => {
      purpleBlink.value = true;
      setTimeout(() => { purpleBlink.value = false; runPurple(); }, 150);
    }, Math.random() * 4000 + 3000);
    blinkTimers.push(t);
  };
  const runBlack = () => {
    const t = setTimeout(() => {
      blackBlink.value = true;
      setTimeout(() => { blackBlink.value = false; runBlack(); }, 150);
    }, Math.random() * 4000 + 3000);
    blinkTimers.push(t);
  };
  runPurple();
  runBlack();
}

function onSceneMouse(e: MouseEvent) { mx.value = e.clientX; my.value = e.clientY; }

let cleanup: (() => void) | null = null;
onMounted(() => {
  const handler = (e: MouseEvent) => { mx.value = e.clientX; my.value = e.clientY; };
  window.addEventListener('mousemove', handler);
  cleanup = () => window.removeEventListener('mousemove', handler);
});
onUnmounted(() => {
  cleanup?.();
  if (countdownTimer) clearInterval(countdownTimer);
});
function onFocus() { typing.value = true; }
function onBlur() { typing.value = false; }
function onPwdFocus() { pwdFocused.value = true; }
function onPwdBlur() { pwdFocused.value = false; }

startBlinks();

// ── Character positions ──
const hidePwd = computed(() => form.password.length > 0 && !showPwd.value);
const lookAway = computed(() => pwdFocused.value && !showPwd.value);

const purpleLookX = computed(() => lookAway.value ? -5 : (form.password.length > 0 && showPwd.value ? -4 : undefined));
const purpleLookY = computed(() => lookAway.value ? -5 : (form.password.length > 0 && showPwd.value ? -4 : undefined));
const blackLookX = computed(() => lookAway.value ? -4 : undefined);
const blackLookY = computed(() => lookAway.value ? -5 : undefined);
const shaking = ref(false);

const purpleStyle = computed(() => ({
  transform: lookAway.value ? 'skewX(-14deg) translateX(-20px)' : typing.value ? 'skewX(-12deg) translateX(40px)' : '',
  height: (typing.value || hidePwd.value) ? '440px' : '400px',
}));
const blackStyle = computed(() => ({
  transform: lookAway.value ? 'skewX(12deg) translateX(-10px)' : '',
}));
const purpleEyeStyle = computed(() => ({
  left: lookAway.value ? '20px' : '45px',
  top: lookAway.value ? '25px' : '40px',
  gap: '32px',
}));
const blackEyeStyle = computed(() => ({
  left: lookAway.value ? '10px' : '26px',
  top: lookAway.value ? '20px' : '32px',
  gap: '24px',
}));

function calcPupil(refEl: any) {
  if (!refEl) return { tx: 0, ty: 0 };
  const r = refEl.getBoundingClientRect();
  const cx = r.left + r.width / 2;
  const cy = r.top + r.height / 3;
  const dx = mx.value - cx;
  const dy = my.value - cy;
  const dist = Math.min(Math.sqrt(dx * dx + dy * dy), 5);
  const a = Math.atan2(dy, dx);
  return { tx: Math.cos(a) * dist, ty: Math.sin(a) * dist };
}

const orangeRef = ref<any>(null);
const yellowRef = ref<any>(null);
const orangePupilStyle = computed(() => {
  if (lookAway.value) return { transform: 'translate(-5px, -5px)' };
  const p = calcPupil(orangeRef.value);
  return { transform: `translate(${p.tx}px, ${p.ty}px)` };
});
const yellowPupilStyle = computed(() => {
  if (lookAway.value) return { transform: 'translate(-5px, -5px)' };
  const p = calcPupil(yellowRef.value);
  return { transform: `translate(${p.tx}px, ${p.ty}px)` };
});
const yellowMouthStyle = computed(() => {
  if (lookAway.value) return { left: '30px', top: '78px' };
  return { left: '55px', top: '88px' };
});

function triggerShake() {
  shaking.value = true;
  setTimeout(() => { shaking.value = false; }, 800);
}

// ── Submit ──
async function submit() {
  errorMsg.value = '';
  if (!form.username || form.password.length < 6) {
    errorMsg.value = !form.username ? '请输入用户名' : '密码至少6位';
    triggerShake();
    return;
  }
  loading.value = true;
  try {
    if (isLogin.value) {
      // 登录
      const data = await request<{ token: string; user: any }>('/user/login', {
        method: 'POST',
        body: { username: form.username, password: form.password },
      });
      storeLogin(data.user, data.token);
      window.location.href = data.user?.user_type === 2 ? '/admin' : '/';
    } else {
      // 注册 — 需邮箱 + 邮箱验证码
      if (!form.email || !form.email.includes('@')) {
        errorMsg.value = '请输入有效的邮箱地址';
        loading.value = false;
        return;
      }
      if (!emailCode.value) {
        errorMsg.value = '请输入邮箱验证码';
        loading.value = false;
        return;
      }
      const headers: Record<string, string> = {
        'X-Email-Code': emailCode.value,
      };
      await request('/user/add', {
        method: 'POST',
        body: { username: form.username, password: form.password, email: form.email, nickname: form.nickname },
        headers,
      });
      // 注册成功自动登录
      const data = await request<{ token: string; user: any }>('/user/login', {
        method: 'POST',
        body: { username: form.username, password: form.password },
      });
      storeLogin(data.user, data.token);
      window.location.href = data.user?.user_type === 2 ? '/admin' : '/';
    }
  } catch (e: any) {
    errorMsg.value = e.message || '操作失败，请重试';
  } finally {
    loading.value = false;
  }
}
</script>

<style>
#login-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  height: 100vh;
  width: 100%;
}
.left-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: linear-gradient(135deg, #d4d0dc 0%, #c8c4d0 50%, #bbb7c5 100%);
  padding: 40px 48px;
  overflow: hidden;
}
.left-panel::after {
  content: ""; position: absolute; top: 20%; right: 15%;
  width: 260px; height: 260px;
  background: rgba(180,170,200,0.25); border-radius: 50%; filter: blur(80px);
}
.left-panel::before {
  content: ""; position: absolute; bottom: 15%; left: 10%;
  width: 350px; height: 350px;
  background: rgba(200,195,210,0.2); border-radius: 50%; filter: blur(100px);
}
.left-panel .logo {
  display: flex; align-items: center; gap: 10px;
  font-size: 16px; font-weight: 600; color: #fff;
  z-index: 10; position: relative;
}
.left-panel .logo svg {
  width: 28px; height: 28px;
  background: rgba(255,255,255,0.15); backdrop-filter: blur(8px);
  padding: 4px; border-radius: 6px;
}
.characters-wrapper {
  position: relative; z-index: 10;
  display: flex; align-items: flex-end; justify-content: center;
  height: 420px;
}
.scene {
  position: relative; width: 480px; height: 360px; overflow: visible;
}
.char {
  position: absolute; bottom: 0; transition: all 0.7s ease-in-out;
  transform-origin: bottom center;
}
.char-purple {
  left: 60px; width: 170px; height: 370px;
  background: #6c3ff5; border-radius: 10px 10px 0 0; z-index: 1;
}
.char-black {
  left: 220px; width: 115px; height: 290px;
  background: #2d2d2d; border-radius: 8px 8px 0 0; z-index: 2;
}
.char-purple.shake,
.char-black.shake {
  animation: shakeHead 0.8s cubic-bezier(0.36, 0.07, 0.19, 0.97);
}
@keyframes shakeHead {
  0%, 100% { translate: 0 0; }
  10% { translate: -9px 0; }
  20% { translate: 7px 0; }
  30% { translate: -6px 0; }
  40% { translate: 5px 0; }
  50% { translate: -4px 0; }
  60% { translate: 3px 0; }
  70% { translate: -2px 0; }
  80% { translate: 1px 0; }
  90% { translate: -0.5px 0; }
}
.char-orange {
  left: 0; width: 230px; height: 190px;
  background: #ff9b6b; border-radius: 115px 115px 0 0; z-index: 3;
}
.char-yellow {
  left: 290px; width: 135px; height: 215px;
  background: #e8d754; border-radius: 68px 68px 0 0; z-index: 4;
}
.orange-eyes {
  left: 82px !important; top: 90px !important; gap: 32px !important;
}
.yellow-eyes {
  left: 52px !important; top: 40px !important; gap: 24px !important;
}
.bare-pupil {
  width: 12px; height: 12px;
  border-radius: 50%; background: #2D2D2D;
  display: inline-block;
  transition: transform 0.7s ease-in-out;
}
.yellow-mouth {
  position: absolute;
  width: 50px; height: 4px;
  background: #2D2D2D;
  border-radius: 2px;
  transition: all 0.6s ease-out;
}
.yellow-mouth.shake {
  animation: shakeHead 0.8s cubic-bezier(0.36, 0.07, 0.19, 0.97);
}
.eyes {
  position: absolute; display: flex; gap: 32px;
  transition: all 0.6s ease-out;
}
.footer-links {
  display: flex; gap: 28px; font-size: 13px;
  color: rgba(80,70,90,0.7); z-index: 10; position: relative;
}
.footer-links a { color: inherit; text-decoration: none; transition: color 0.2s; }
.footer-links a:hover { color: #333; }

.right-panel {
  display: flex; align-items: center; justify-content: center;
  background: #fff; padding: 40px;
}
.form-container { width: 100%; max-width: 400px; }
.sparkle-icon { display: flex; justify-content: center; margin-bottom: 24px; }
.sparkle-icon svg { width: 32px; height: 32px; }
.form-header { text-align: center; margin-bottom: 36px; }
.form-header h1 { font-size: 28px; font-weight: 700; color: #1a1a2e; letter-spacing: -0.5px; margin-bottom: 6px; }
.form-header p { font-size: 14px; color: #888; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; color: #333; margin-bottom: 8px; }
.form-group .input-wrapper { position: relative; }
.form-group input {
  width: 100%; height: 48px; border: none; border-bottom: 1.5px solid #e0e0e0;
  padding: 0 40px 0 0; font-size: 15px; color: #1a1a2e;
  background: transparent; outline: none; transition: border-color 0.3s;
}
.form-group input:focus { border-bottom-color: #5b21b6; }
.form-group input::placeholder { color: #ccc; }
.toggle-password {
  position: absolute; right: 0; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; color: #666; padding: 6px;
}
.toggle-password:hover { color: #333; }
.btn-login {
  position: relative; width: 100%; height: 50px; border-radius: 25px;
  font-size: 15px; font-weight: 600; cursor: pointer; overflow: hidden;
  transition: all 0.3s; border: 1.5px solid #1a1a2e;
  background: #1a1a2e; color: #fff; margin-bottom: 14px;
}
.btn-login:disabled { opacity: 0.7; cursor: not-allowed; }
.btn-login .btn-text {
  display: inline-flex; align-items: center; gap: 10px; transition: all 0.3s;
}
.btn-login .btn-hover-content {
  position: absolute; inset: 0; display: flex; align-items: center;
  justify-content: center; gap: 8px; background: #5b21b6; color: #fff;
  opacity: 0; transition: all 0.3s; border-radius: 25px;
}
.btn-login:hover .btn-text { transform: translateX(40px); opacity: 0; }
.btn-login:hover .btn-hover-content { opacity: 1; }
.signup-link {
  text-align: center; font-size: 13px; color: #888; margin-top: 32px;
}
.signup-link a { color: #1a1a2e; font-weight: 600; text-decoration: none; }
.signup-link a:hover { text-decoration: underline; }
.error-msg {
  padding: 10px 14px; font-size: 13px; color: #dc2626;
  background: rgba(220,38,38,0.08); border: 1px solid rgba(220,38,38,0.2);
  border-radius: 10px; margin-bottom: 16px;
}
.error-msg.show { display: block; }
label.error-label { color: #dc2626; }
input.error { border-bottom-color: #dc2626; }

/* ── Captcha ── */
.captcha-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.captcha-img {
  height: 42px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  cursor: pointer;
  transition: border-color 0.2s;
}
.captcha-img:hover {
  border-color: #5b21b6;
}
.captcha-refresh {
  background: none;
  border: none;
  cursor: pointer;
  color: #888;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}
.captcha-refresh:hover {
  color: #5b21b6;
  background: #f5f3ff;
}
.captcha-loading {
  font-size: 12px;
  color: #bbb;
  height: 42px;
  display: flex;
  align-items: center;
}
.email-hint {
  font-size: 11px;
  color: #bbb;
  margin-top: 4px;
}
.send-code-btn {
  flex-shrink: 0;
  height: 42px;
  padding: 0 14px;
  border-radius: 6px;
  border: 1px solid #5b7bff;
  background: #fff;
  color: #5b7bff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.send-code-btn:hover:not(:disabled) {
  background: #5b7bff;
  color: #fff;
}
.send-code-btn:disabled {
  border-color: #e0e0e0;
  color: #ccc;
  cursor: not-allowed;
}
.captcha-input {
  width: 100% !important;
  height: 42px !important;
  font-size: 16px !important;
  letter-spacing: 6px;
  text-align: center;
}

@media (max-width: 900px) {
  #login-page { grid-template-columns: 1fr; }
  .left-panel { display: none; }
}
</style>