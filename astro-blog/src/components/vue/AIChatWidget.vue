<template>
  <!-- Floating trigger button -->
  <button
    v-if="!open"
    @click="openChat"
    class="fixed bottom-20 right-6 z-40 w-14 h-14 rounded-full bg-brand-600 text-white shadow-lg hover:bg-brand-700 hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center animate-float"
    title="AI 助手"
  >
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
    </svg>
    <span class="absolute top-0 right-0 w-3 h-3 rounded-full bg-green-400 border-2 border-white"></span>
  </button>

  <!-- Chat panel -->
  <div
    v-if="open"
    class="fixed bottom-20 right-6 z-40 w-[380px] h-[520px] max-sm:w-[calc(100vw-2rem)] glass-card shadow-2xl flex flex-col overflow-hidden animate-slide-up"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-white/60">
      <div class="flex items-center gap-2">
        <button @click="showHistory = !showHistory" class="text-gray-400 hover:text-brand-600 transition-colors p-1" title="历史对话">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        </button>
        <div>
          <h3 class="text-sm font-semibold text-gray-700">Ray的助手</h3>
          <p class="text-xs text-green-500">在线</p>
        </div>
      </div>
      <div class="flex items-center gap-1">
        <button @click="expandToAgent" title="全屏展开" class="text-gray-400 hover:text-brand-600 transition-colors p-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/></svg>
        </button>
        <button @click="exportChat('txt')" title="导出 TXT" class="text-gray-400 hover:text-brand-600 transition-colors p-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        </button>
        <button @click="open = false" class="text-gray-400 hover:text-gray-600 transition-colors p-1">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
    </div>

    <!-- History panel -->
    <div v-if="showHistory" class="border-b border-gray-100 bg-white/80 max-h-[200px] overflow-y-auto">
      <div class="flex items-center justify-between px-4 py-2 border-b border-gray-50">
        <span class="text-xs font-semibold text-gray-500">历史对话</span>
        <button @click="newSession" class="text-xs text-brand-600 hover:text-brand-700">新对话</button>
      </div>
      <div v-if="loadingHistory" class="text-center py-4 text-xs text-gray-400">加载中...</div>
      <div v-else-if="sessions.length === 0" class="text-center py-4 text-xs text-gray-400">暂无历史</div>
      <div
        v-for="s in sessions"
        :key="s.id"
        class="flex items-center border-b border-gray-50 hover:bg-brand-50 transition-colors"
        :class="{ 'bg-brand-50': s.id === sessionId }"
      >
        <div @click="loadSession(s.id)" class="flex-1 min-w-0 px-4 py-2.5 cursor-pointer">
          <div class="text-xs font-medium text-gray-700 truncate">{{ s.title }}</div>
          <div class="text-[10px] text-gray-400 truncate mt-0.5">{{ s.preview || '新对话' }}</div>
        </div>
        <button class="widget-delete" @click.stop="deleteSession(s.id)" title="删除">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div ref="msgContainer" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-purple-50/50 to-white/50">
      <!-- Login prompt -->
      <div v-if="!loggedIn" class="text-center py-12">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-brand-100 flex items-center justify-center">
          <svg class="w-8 h-8 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <p class="text-gray-500 text-sm mb-3">登录后即可与 AI 助手对话</p>
        <button @click="goLogin" class="px-5 py-2 rounded-button bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition-colors">
          去登录
        </button>
      </div>

      <!-- Global error banner -->
      <div v-if="errorMsg" class="flex items-center justify-between bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-600">
        <span>{{ errorMsg }}</span>
        <button @click="errorMsg = ''" class="text-red-400 hover:text-red-600 ml-2">&times;</button>
      </div>

      <!-- Messages -->
      <template v-else>
        <template v-for="(msg, i) in messages" :key="i">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="max-w-[75%]">
              <div class="px-3 py-2 rounded-2xl text-sm leading-relaxed bg-brand-600 text-white rounded-br-md">{{ msg.content }}</div>
            </div>
            <div class="w-8 h-8 rounded-full flex-shrink-0 ml-2 mt-1 flex items-center justify-center text-base" style="background: linear-gradient(135deg, #fbbf24, #f97316);">
              🐼
            </div>
          </div>
          <!-- AI 消息（块级渲染） -->
          <div v-else class="flex justify-start">
            <div class="w-8 h-8 rounded-full flex-shrink-0 mr-2 mt-1 flex items-center justify-center text-base" style="background: linear-gradient(135deg, #818cf8, #6366f1);">
              🐱
            </div>
            <div class="max-w-[80%] space-y-1">
              <ThinkingTyping v-if="msg.streaming && (!msg.blocks || msg.blocks.length === 0 || (msg.blocks.length === 1 && msg.blocks[0].content === '...'))" />
              <template v-for="(block, bi) in msg.blocks" :key="bi">
                <ThinkingCard v-if="block.type === 'thinking'" :text="block.text || ''" :streaming="block.streaming" />
                <ToolCallCard v-else-if="block.type === 'tool_call'" :tool="block.tool || ''" :args="block.args" :status="(block.status as any)" />
                <!-- 导出文件内联卡（优先渲染，确保一定可见） -->
                <div v-else-if="block.type === 'tool_result' && isExportResult(block.result)" class="export-inline-card">
                  <svg class="w-5 h-5" fill="none" stroke="#16a34a" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                  <div class="flex-1 min-w-0">
                    <div class="text-xs font-semibold text-gray-700 truncate">{{ block.result.filename || block.result.title }}</div>
                    <div class="text-[10px] text-gray-400">{{ (block.result.format||'').toUpperCase() }}</div>
                  </div>
                  <a :href="encodeURI(block.result.url)" :download="block.result.filename" class="inline-dl-btn">下载</a>
                </div>
                <ToolResultCard v-else-if="block.type === 'tool_result'" :result="block.result" />
                <div v-else-if="block.type === 'text'" class="px-3 py-2 rounded-2xl text-sm leading-relaxed bg-white text-gray-700 rounded-bl-md shadow-sm">
                  <div v-html="renderMarkdown(block.content || '')" />
                  <span v-if="block.streaming" class="inline-block w-2 h-4 bg-brand-600 animate-pulse rounded-sm ml-0.5 align-middle" />
                </div>
              </template>
            </div>
          </div>
        </template>

        <!-- Empty state -->
        <div v-if="messages.length === 0 && !streaming" class="text-center py-8">
          <p class="text-gray-400 text-sm">我是 Ray 的 AI 助手，有什么想聊的？</p>
        </div>
      </template>
    </div>

    <!-- Input -->
    <div v-if="loggedIn" class="px-4 py-3 border-t border-gray-100 bg-white/60">
      <!-- Connecting indicator -->
      <div v-if="connecting" class="flex items-center gap-2 mb-2 text-xs text-gray-400">
        <span class="inline-block w-3 h-3 border-2 border-brand-400 border-t-transparent rounded-full animate-spin"></span>
        正在连接 AI 服务...
      </div>
      <form @submit.prevent="send" class="flex items-center gap-2">
        <!-- 附件按钮 -->
        <label class="attach-btn" title="上传文件">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/></svg>
          <input type="file" class="hidden" @change="onWidgetFile" accept=".pdf,.doc,.docx,.txt,.md,.jpg,.png,.webp" />
        </label>
        <input
          v-model="input"
          type="text"
          :disabled="streaming || connecting"
          placeholder="输入消息..."
          class="flex-1 px-4 py-2 border border-gray-200 rounded-full text-sm text-gray-900 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all disabled:opacity-50"
        />
        <!-- 终止按钮 -->
        <button
          v-if="streaming"
          type="button"
          @click="stopStreaming"
          class="w-9 h-9 rounded-full bg-red-500 text-white flex-shrink-0 flex items-center justify-center hover:bg-red-600 transition-colors"
          title="终止"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
        </button>
        <!-- 发送按钮 -->
        <button
          v-else
          type="submit"
          :disabled="!input.trim() || connecting"
          class="w-9 h-9 rounded-full bg-brand-600 text-white flex-shrink-0 flex items-center justify-center hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg v-if="!connecting" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
          <span v-else class="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue';
import { $isLoggedIn } from '@lib/store';
import { getToken } from '@lib/auth';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { marked } from 'marked';
import ThinkingCard from './ThinkingCard.vue';
import ToolCallCard from './ToolCallCard.vue';
import ToolResultCard from './ToolResultCard.vue';
import ThinkingTyping from './ThinkingTyping.vue';

interface AgentBlock {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'text';
  text?: string;
  content?: string;
  tool?: string;
  args?: Record<string, any>;
  status?: 'running' | 'done' | 'error';
  result?: any;
  streaming?: boolean;
}
interface UIMessage {
  role: 'user' | 'assistant';
  content: string;
  blocks?: AgentBlock[];
  streaming?: boolean;
}

const open = ref(false);
const loggedIn = ref(false);
const input = ref('');
const streaming = ref(false);
const connecting = ref(false);  // 正在建立连接（session/start）
const messages = ref<UIMessage[]>([]);
const sessionId = ref<string | null>(null);
watch(sessionId, (id) => { if (id) localStorage.setItem('agentSessionId', id); });
const msgContainer = ref<HTMLElement>();
const errorMsg = ref('');  // 全局错误提示
const streamCtrl = ref<AbortController | null>(null);  // SSE 控制器

function stopStreaming() {
  if (streamCtrl.value) {
    streamCtrl.value.abort();
    streamCtrl.value = null;
  }
  streaming.value = false;
  connecting.value = false;
}

const widgetFiles = ref<{name:string,url:string}[]>([]);
async function onWidgetFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  try {
    const form = new FormData(); form.append('file', file);
    const r = await fetch('/api/file/upload/agent', { method: 'POST', body: form });
    const j = await r.json();
    if (j.code==='200') widgetFiles.value.push({ name: j.data.name, url: j.data.url });
  } catch {}
}

// ── 历史对话 ──
const showHistory = ref(false);
const sessions = ref<{ id: string; title: string; preview: string; startedAt: string }[]>([]);
const loadingHistory = ref(false);

async function fetchSessions() {
  loadingHistory.value = true;
  try {
    const token = getToken();
    const r = await fetch('/api/psychological-chat/session/list', { headers: { token: token || '' } });
    const json = await r.json();
    if (json.code === '200') sessions.value = json.data;
  } catch { /* ignore */ }
  loadingHistory.value = false;
}

async function loadSession(id: string) {
  if (id === sessionId.value) { showHistory.value = false; return; }
  const token = getToken();
  try {
    const r = await fetch(`/api/psychological-chat/session/${id}/messages`, { headers: { token: token || '' } });
    const json = await r.json();
    if (json.code === '200') {
      sessionId.value = id;
      localStorage.setItem('agentSessionId', id);
      messages.value = json.data.map((m: any) => {
        const blocks: AgentBlock[] = [];
        if (m.role === 'assistant') {
          // 检测导出文件链接
          const fileRe = /((?:\/|https?:\/\/[^\s]*)\/uploads\/export\/[^\s]*\.(pdf|docx|txt))/gi;
          let match; let lastIdx = 0;
          while ((match = fileRe.exec(m.content)) !== null) {
            if (match.index > lastIdx) {
              blocks.push({ type: 'text', content: m.content.slice(lastIdx, match.index) });
            }
            blocks.push({ type: 'tool_result', result: { url: match[1], filename: match[1].split('/').pop(), format: match[2] } });
            lastIdx = match.index + match[0].length;
          }
          if (blocks.length === 0) {
            blocks.push({ type: 'text', content: m.content });
          } else if (lastIdx < m.content.length) {
            blocks.push({ type: 'text', content: m.content.slice(lastIdx) });
          }
        }
        return { role: m.role, content: m.content, blocks: blocks.length > 0 ? blocks : undefined };
      });
      showHistory.value = false;
    }
  } catch { /* ignore */ }
}

function newSession() {
  sessionId.value = null;
  messages.value = [];
  showHistory.value = false;
  localStorage.removeItem('agentSessionId');
}

async function deleteSession(id: string) {
  if (!confirm('确定删除这条对话？')) return;
  try {
    await fetch(`/api/psychological-chat/session/${id}`, { method: 'DELETE', headers: { token: getToken() || '' } });
    sessions.value = sessions.value.filter(s => s.id !== id);
    if (sessionId.value === id) { sessionId.value = null; messages.value = []; }
  } catch {}
}

onMounted(() => {
  loggedIn.value = $isLoggedIn.get();
  $isLoggedIn.listen((val) => { loggedIn.value = val; });
});

function isExportResult(r: any): boolean {
  if (!r) return false;
  const fmt = (r.format || '').toLowerCase().trim();
  return !!(r.url && r.filename && ['pdf','docx','txt'].includes(fmt));
}

function goLogin() {
  window.location.href = '/auth/login';
}

function expandToAgent() {
  if (sessionId.value) {
    localStorage.setItem('agentSessionId', sessionId.value);
  }
  window.open('/agent', '_blank');
}

function openChat() {
  loggedIn.value = $isLoggedIn.get();
  open.value = true;
  fetchSessions();
}

function isDocRequest(text: string): boolean {
  const kw = ['导出', '生成文档', '整理.*txt', '整理.*md', '生成.*文档', '导出.*txt', '导出.*md', '生成报告', '整理成', '汇总'];
  return kw.some(k => new RegExp(k).test(text));
}

async function send() {
  const text = input.value.trim();
  if (!text || streaming.value) return;

  // 附加上传文件
  let fullText = text;
  if (widgetFiles.value.length > 0) {
    fullText += '\n\n[上传文件]';
    widgetFiles.value.forEach(f => { fullText += `\n- ${f.name}: ${window.location.origin}${f.url}`; });
    widgetFiles.value = [];
  }
  messages.value.push({ role: 'user', content: fullText });
  input.value = '';
  errorMsg.value = '';
  const token = getToken();

  // ─── 文档生成模式 ───
  if (isDocRequest(text)) {
    streaming.value = true;
    const aiMsg: UIMessage = { role: 'assistant', content: '正在为您生成文档...', streaming: true };
    messages.value.push(aiMsg);
    await scrollDown();

    try {
      const res = await fetch('/api/psychological-chat/generate-doc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', token: token || '' },
        body: JSON.stringify({ topic: text, format: 'txt' }),
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'ai_doc.txt'; a.click();
        URL.revokeObjectURL(url);
        aiMsg.content = '文档已生成并下载，文件包含您要求的整理内容。';
      } else {
        aiMsg.content = '文档生成失败，请稍后重试。';
      }
    } catch {
      aiMsg.content = '生成失败，请检查后端是否启动。';
    }
    aiMsg.streaming = false;
    streaming.value = false;
    return;
  }

  // ─── 正常对话模式 ───
  streaming.value = true;
  connecting.value = true;
  const aiMsg: UIMessage = { role: 'assistant', content: '', streaming: true };
  messages.value.push(aiMsg);
  await scrollDown();

  try {
    // 1. 创建/获取会话（不带 initialMessage，避免与 stream 中重复保存）
    if (!sessionId.value) {
      connecting.value = true;
      try {
        const res = await fetch('/api/psychological-chat/session/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', token: token || '' },
          body: JSON.stringify({ sessionTitle: text.slice(0, 30) }),
        });
        const json = await res.json();
        if (json.code === '200' && json.data) {
          sessionId.value = String(json.data.id || json.data);
          localStorage.setItem('agentSessionId', sessionId.value);
        } else {
          errorMsg.value = '创建会话失败: ' + (json.msg || '未知错误');
          aiMsg.content = '';
          messages.value.pop();
          streaming.value = false;
          connecting.value = false;
          return;
        }
      } catch (e: any) {
        errorMsg.value = '无法连接后端服务，请确认后端已启动。';
        aiMsg.content = '';
        messages.value.pop();
        streaming.value = false;
        connecting.value = false;
        return;
      }
    }
    connecting.value = false;

    // 2. SSE 流式对话（支持 Agent 类型化事件）
    let fullContent = '';
    const blocks: AgentBlock[] = [];
    // 预填思考提示，消除空白期
    blocks.push({ type: 'text', content: '...', streaming: true });
    aiMsg.blocks = blocks;
    streamCtrl.value = new AbortController();

    await fetchEventSource('/api/psychological-chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        token: token || '',
      },
      body: JSON.stringify({
        sessionId: sessionId.value,
        userMessage: fullText,
      }),
      signal: streamCtrl.value.signal,
      openWhenHidden: true,

      onmessage(event: { event?: string; data?: string }) {
        const evt = event.event || 'message';
        const raw = event.data || '';

        if (evt === 'tool_call') {
          try {
            const d = JSON.parse(raw);
            blocks.push({ type: 'tool_call', tool: d.tool, args: d.args, status: 'running' });
          } catch { /* ignore parse error */ }
          scrollDown();
        } else if (evt === 'tool_result') {
          try {
            const d = JSON.parse(raw);
            // 更新对应的 tool_call 状态（强制响应式）
            for (let i = blocks.length - 1; i >= 0; i--) {
              if (blocks[i].type === 'tool_call' && blocks[i].tool === d.tool) {
                blocks.splice(i, 1, { ...blocks[i], status: 'done' });
                break;
              }
            }
            blocks.push({ type: 'tool_result', result: d.result });
          } catch { /* ignore */ }
          scrollDown();
        } else if (evt === 'thinking') {
          try {
            const d = JSON.parse(raw);
            const lastThink = blocks.length > 0 && blocks[blocks.length - 1].type === 'thinking'
              ? blocks[blocks.length - 1] : null;
            if (lastThink) {
              lastThink.text = (lastThink.text || '') + d.text;
            } else {
              blocks.push({ type: 'thinking', text: d.text, streaming: true });
            }
          } catch { /* ignore */ }
          scrollDown();
        } else if (evt === 'message') {
          try {
            const d = JSON.parse(raw);
            const text = d.text || '';
            fullContent += text;
            const lastText = blocks.length > 0 && blocks[blocks.length - 1].type === 'text'
              ? blocks[blocks.length - 1] : null;
            // 第一个真实文本替换预填的 "..."
            if (lastText && lastText.streaming && lastText.content === '...') {
              lastText.content = text;
            } else if (lastText && lastText.streaming) {
              lastText.content = (lastText.content || '') + text;
            } else {
              blocks.push({ type: 'text', content: text, streaming: true });
            }
          } catch {
            // 兼容旧格式（纯文本）
            fullContent += raw;
            const lastText = blocks.length > 0 && blocks[blocks.length - 1].type === 'text'
              ? blocks[blocks.length - 1] : null;
            if (lastText && lastText.streaming) {
              lastText.content = (lastText.content || '') + raw;
            } else {
              blocks.push({ type: 'text', content: raw, streaming: true });
            }
          }
          aiMsg.content = fullContent;
          scrollDown();
        } else if (evt === 'done') {
          // 标记所有 streaming 结束
          blocks.forEach(b => { if (b.streaming !== undefined) b.streaming = false; });
          if (fullContent) aiMsg.content = fullContent;
          streaming.value = false;
          streamCtrl.value?.abort();
        } else if (evt === 'error') {
          try {
            const d = JSON.parse(raw);
            errorMsg.value = d.message || 'AI 服务出错';
          } catch { errorMsg.value = 'AI 服务出错'; }
          streaming.value = false;
          streamCtrl.value?.abort();
        }
      },

      onerror(err: any) {
        if (!fullContent && blocks.length === 0) {
          messages.value.pop();
          errorMsg.value = '连接超时或后端无响应，请稍后重试。';
        } else {
          blocks.forEach(b => { if (b.streaming !== undefined) b.streaming = false; });
        }
        streaming.value = false;
        streamCtrl.value?.abort();
        throw err;
      },

      onclose() {
        blocks.forEach(b => { if (b.streaming !== undefined) b.streaming = false; });
        streaming.value = false;
      },
    });
  } catch {
    if (!aiMsg.content && (!aiMsg.blocks || aiMsg.blocks.length === 0)) {
      messages.value.pop();
      errorMsg.value = '连接失败，请确认后端服务已启动。';
    }
    streaming.value = false;
  } finally {
    connecting.value = false;
  }
}

function renderMarkdown(content: string): string {
  if (!content) return '';
  const html = marked.parse(content, { breaks: true }) as string;
  return html;
}

function downloadMessage(content: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'ai_doc.txt'; a.click();
  URL.revokeObjectURL(url);
}

async function exportChat(format: string) {
  if (!sessionId.value) return;
  try {
    const token = getToken();
    const resp = await fetch('/api/psychological-chat/export/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', token: token || '' },
      body: JSON.stringify({ sessionId: sessionId.value, format }),
    });
    const j = await resp.json();
    if (j.code === '200' && j.data?.downloadToken) {
      window.open(`/api/psychological-chat/export?sessionId=${sessionId.value}&format=${format}&dt=${j.data.downloadToken}`, '_blank');
    } else {
      alert('导出失败，请重试');
    }
  } catch { alert('导出失败'); }
}

async function scrollDown() {
  await nextTick();
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
  }
}
</script>

<style scoped>
.widget-delete {
  flex-shrink: 0; padding: 6px; color: #d1d5db; background: none; border: none; cursor: pointer;
  opacity: 0; transition: opacity 0.15s, color 0.15s; margin-right: 4px;
}
.widget-delete:hover { color: #ef4444; }
.flex.items-center:hover .widget-delete,
.bg-brand-50 .widget-delete { opacity: 1; }

/* Inline export download card */
.export-inline-card {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 10px; margin: 2px 0;
}
.inline-dl-btn {
  padding: 4px 12px; background: #16a34a; color: #fff;
  border-radius: 6px; text-decoration: none; font-size: 11px; font-weight: 600;
}

.attach-btn {
  cursor: pointer; color: #94a3b8; padding: 4px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; transition: color .15s;
}
.attach-btn:hover { color: #5b7bff; }

input, input:focus, input:disabled, input::placeholder {
  color: #1e293b !important;
  -webkit-text-fill-color: #1e293b !important;
}
input::placeholder { color: #9ca3af !important; -webkit-text-fill-color: #9ca3af !important; }
input { background: #fff; }
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-6px); }
}
.animate-float {
  animation: float 3s ease-in-out infinite;
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}

/* ── Markdown 表格样式 ── */
:deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 12px;
}
:deep(th) {
  background: #f1f5f9;
  color: #475569;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  text-align: left;
  font-weight: 600;
}
:deep(td) {
  padding: 5px 10px;
  border: 1px solid #e2e8f0;
  color: #334155;
}
:deep(tr:nth-child(even) td) {
  background: #f8fafc;
}
</style>
