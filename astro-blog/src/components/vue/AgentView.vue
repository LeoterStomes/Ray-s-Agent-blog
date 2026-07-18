<template>
  <div class="agent-page">
    <!-- Header -->
    <header class="agent-header glass">
      <a href="/" class="back-btn">&larr; 返回首页</a>
      <h1 class="agent-title">AI 助手</h1>
      <div class="header-actions">
        <button @click="showHistory = !showHistory" class="action-btn">{{ showHistory ? '隐藏历史' : '历史' }}</button>
        <button @click="newSession" class="action-btn">新对话</button>
        <button v-if="sessionId" @click="exportChat" class="action-btn">导出</button>
      </div>
    </header>

    <!-- Body: three columns (history + chat + tools) -->
    <div class="agent-body">
      <!-- History sidebar -->
      <div class="history-sidebar" :class="{ open: showHistory }">
        <div class="history-header">
          <span class="history-title">历史对话</span>
          <button @click="newSession" class="history-new-btn">+ 新对话</button>
        </div>
        <div v-if="loadingHistory" class="history-loading">加载中...</div>
        <div v-else-if="sessions.length === 0" class="history-empty">暂无历史</div>
        <div
          v-for="s in sessions" :key="s.id"
          class="history-item"
          :class="{ active: s.id === sessionId }"
        >
          <div class="history-item-main" @click="loadSession(s.id)">
            <div class="history-item-title">{{ s.title }}</div>
            <div class="history-item-preview">{{ s.preview || '新对话' }}</div>
          </div>
          <button class="history-delete" @click.stop="deleteSession(s.id)" title="删除">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      </div>
      <!-- History toggle -->
      <button class="history-toggle-btn" @click="showHistory = !showHistory" :title="showHistory ? '收起' : '展开历史'">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
      </button>

      <!-- Left: Chat -->
      <div class="chat-panel">
        <div ref="msgContainer" class="chat-messages">
          <div v-if="!loggedIn" class="login-prompt">
            <p>登录后即可使用 AI 助手</p>
            <a href="/auth/login" class="btn-login">去登录</a>
          </div>

          <template v-else>
            <template v-for="(msg, i) in messages" :key="i">
              <!-- User -->
              <div v-if="msg.role === 'user'" class="msg-row user-row">
                <div class="msg-bubble user-bubble">{{ msg.content }}</div>
                <div class="avatar-circle avatar-user">🐼</div>
              </div>
              <!-- AI -->
              <div v-else class="msg-row ai-row">
                <div class="avatar-circle avatar-ai">🐱</div>
                <div class="msg-blocks">
                  <ThinkingTyping v-if="msg.streaming && (!msg.blocks || msg.blocks.length === 0 || (msg.blocks.length === 1 && msg.blocks[0].content === '...'))" />
                  <template v-for="(block, bi) in msg.blocks" :key="bi">
                    <ThinkingCard v-if="block.type === 'thinking'" :text="block.text || ''" :streaming="block.streaming" />
                    <ToolCallCard
                      v-else-if="block.type === 'tool_call'"
                      :tool="block.tool || ''"
                      :args="block.args"
                      :status="fixStatus(block.status)"
                      @click="selectTool(bi, block)"
                    />
                    <!-- 导出文件内联卡 -->
                    <div v-if="block.type === 'tool_result' && isExportResult(block.result)" class="export-inline-card">
                      <svg class="w-5 h-5" fill="none" stroke="#16a34a" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                      <div class="flex-1 min-w-0"><div class="text-xs font-semibold truncate">{{ block.result.filename }}</div><div class="text-[10px] text-gray-500">{{ (block.result.format||'').toUpperCase() }}</div></div>
                      <a :href="encodeURI(block.result.url)" :download="block.result.filename" class="inline-dl-btn">下载</a>
                    </div>
                    <ToolResultCard
                      v-else-if="block.type === 'tool_result'"
                      :result="block.result"
                    />
                    <div v-else-if="block.type === 'text'" class="msg-bubble ai-bubble">
                      <div v-html="renderMarkdown(block.content || '')" />
                    </div>
                  </template>
                </div>
              </div>
            </template>
          </template>

          <div v-if="messages.length === 0 && !streaming && loggedIn" class="empty-state">
            <p>我是 Ray 的 AI 助手，可以帮你搜索文章、查看分类、联网搜索。</p>
            <p class="hint">试试问："推荐几篇技术文章" 或 "JS 概念那篇讲了什么"</p>
          </div>
        </div>

        <!-- Input -->
        <div v-if="loggedIn" class="chat-input-area">
          <!-- 拖拽上传区 -->
          <div
            class="drop-zone"
            :class="{ dragging: isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
            v-if="uploadedFiles.length === 0"
          >
            <span v-if="uploading">上传中...</span>
            <span v-else>拖拽文件到此处，或 <label class="upload-link">选择文件<input type="file" class="hidden-input" @change="onFileSelect" multiple accept=".pdf,.doc,.docx,.txt,.md,.jpg,.png,.webp" /></label></span>
          </div>
          <!-- 已上传文件预览 -->
          <div v-if="uploadedFiles.length > 0" class="upload-preview">
            <span v-for="(f,i) in uploadedFiles" :key="i" class="file-tag">
              {{ f.name }}
              <button @click="uploadedFiles.splice(i,1)" class="file-remove">&times;</button>
            </span>
          </div>

          <form @submit.prevent="sendMsg" class="input-row">
            <textarea
              v-model="input"
              :disabled="streaming"
              placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
              class="chat-textarea"
              rows="1"
              @keydown.enter.exact.prevent="sendMsg"
              @input="autoResize"
              ref="textareaRef"
            />
            <!-- 终止按钮 -->
            <button v-if="streaming" type="button" @click="stopStreaming" class="stop-btn" title="终止">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
            </button>
            <button v-else type="submit" :disabled="!input.trim()" class="send-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
        </div>
      </div>

      <!-- Right: Tool Panel -->
      <div class="tool-panel">
        <h3 class="panel-title">工具面板</h3>
        <div v-if="toolHistory.length === 0" class="panel-empty">
          <p>工具调用记录将显示在这里</p>
        </div>
        <div v-else class="tool-history">
          <div
            v-for="(t, i) in visibleToolHistory"
            :key="t.idx"
            class="tool-history-item"
            :class="{ active: t.idx === selectedToolIdx, newest: i === 0 }"
            @click="selectedToolIdx = t.idx; selectedTool = toolHistory[t.idx]"
          >
            <span class="tool-dot" :class="t.status" />
            <span class="tool-name">{{ t.displayName }}</span>
            <span v-if="i === 0 && t.status === 'running'" class="tool-running-badge">执行中</span>
          </div>
          <button v-if="toolHistory.length > MAX_VISIBLE_TOOLS" @click="showAllTools = !showAllTools" class="toggle-tools-btn">
            {{ showAllTools ? '收起' : `展开更多 (${toolHistory.length - MAX_VISIBLE_TOOLS} 项)` }}
          </button>
        </div>

        <!-- Expanded result -->
        <div v-if="selectedTool && selectedTool.result" class="tool-detail">
          <h4>{{ selectedTool.displayName }}</h4>
          <div v-if="selectedTool.result.articles" class="article-list">
            <a
              v-for="a in selectedTool.result.articles"
              :key="a.id"
              :href="a.url || `/blog/${a.id}`"
              target="_blank"
              class="article-card-detailed"
            >
              <div class="art-title">{{ a.title }}</div>
              <div class="art-meta">
                <span v-if="a.category" class="art-cat">{{ a.category }}</span>
                <span class="art-date">{{ (a.published_at || '').slice(0, 10) }}</span>
              </div>
              <div class="art-summary">{{ a.summary || '' }}</div>
            </a>
          </div>
          <div v-else-if="selectedTool.result.categories" class="cat-list">
            <div v-for="c in selectedTool.result.categories" :key="c.id" class="cat-item">
              <span class="cat-name">{{ c.name }}</span>
              <span class="cat-count">{{ c.article_count }} 篇</span>
            </div>
          </div>
          <div v-else class="tool-raw">{{ JSON.stringify(selectedTool.result, null, 2) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue';
import { $isLoggedIn } from '@lib/store';
import { getToken } from '@lib/auth';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { marked } from 'marked';
import ThinkingCard from './ThinkingCard.vue';
import ToolCallCard from './ToolCallCard.vue';
import ToolResultCard from './ToolResultCard.vue';
import ThinkingTyping from './ThinkingTyping.vue';
import { TOOL_NAMES } from '@lib/toolNames';

interface AgentBlock {
  type: string; text?: string; content?: string;
  tool?: string; args?: Record<string, any>; status?: string; result?: any; streaming?: boolean;
}
interface UIMessage {
  role: 'user' | 'assistant'; content: string; blocks?: AgentBlock[]; streaming?: boolean;
}
interface ToolRecord {
  displayName: string; tool: string; status: string;
  args?: Record<string, any>; result?: any;
}

const loggedIn = ref(false);
const input = ref('');
const streaming = ref(false);
const isDragging = ref(false);
const uploadedFiles = ref<{name:string,url:string}[]>([]);
const uploading = ref(false);

async function onFileSelect(e: Event) {
  const files = (e.target as HTMLInputElement).files;
  if (files) { for (let i=0;i<files.length;i++) await uploadFile(files[i]); }
}
async function onDrop(e: DragEvent) {
  isDragging.value = false;
  if (e.dataTransfer?.files) { for (let i=0;i<e.dataTransfer.files.length;i++) await uploadFile(e.dataTransfer.files[i]); }
}
async function uploadFile(file: File) {
  uploading.value = true;
  try {
    const form = new FormData(); form.append('file', file);
    const r = await fetch('/api/file/upload/agent', { method: 'POST', body: form });
    const j = await r.json();
    if (j.code==='200') uploadedFiles.value.push({ name: j.data.name, url: j.data.url });
  } catch {}
  uploading.value = false;
}
const streamCtrl = ref<AbortController | null>(null);

function stopStreaming() {
  streamCtrl.value?.abort();
  streamCtrl.value = null;
  streaming.value = false;
}
const messages = ref<UIMessage[]>([]);
const sessionId = ref<string | null>(null);
watch(sessionId, (id) => { if (id) localStorage.setItem('agentSessionId', id); });

// 历史
const showHistory = ref(true);
const sessions = ref<{ id: string; title: string; preview: string }[]>([]);
const loadingHistory = ref(false);

async function fetchSessions() {
  loadingHistory.value = true;
  try {
    const r = await fetch('/api/psychological-chat/session/list', { headers: { token: getToken() || '' } });
    const json = await r.json();
    if (json.code === '200') sessions.value = json.data;
  } catch {}
  loadingHistory.value = false;
}

async function loadSession(id: string) {
  if (id === sessionId.value) return;
  try {
    const r = await fetch(`/api/psychological-chat/session/${id}/messages`, { headers: { token: getToken() || '' } });
    const json = await r.json();
    if (json.code === '200') {
      sessionId.value = id;
      localStorage.setItem('agentSessionId', id);
      messages.value = json.data.map((m: any) => {
        const blocks: AgentBlock[] = [];
        if (m.role === 'assistant') {
          const fileRe = /((?:\/|https?:\/\/[^\s]*)\/uploads\/export\/[^\s]*\.(pdf|docx|txt))/gi;
          let match; let lastIdx = 0;
          while ((match = fileRe.exec(m.content)) !== null) {
            if (match.index > lastIdx) blocks.push({ type: 'text', content: m.content.slice(lastIdx, match.index) });
            blocks.push({ type: 'tool_result', result: { url: match[1], filename: match[1].split('/').pop(), format: match[2] } });
            lastIdx = match.index + match[0].length;
          }
          if (blocks.length === 0) blocks.push({ type: 'text', content: m.content });
          else if (lastIdx < m.content.length) blocks.push({ type: 'text', content: m.content.slice(lastIdx) });
        }
        return { role: m.role, content: m.content, blocks: blocks.length > 0 ? blocks : undefined };
      });
    }
  } catch {}
}

const msgContainer = ref<HTMLElement>();
const textareaRef = ref<HTMLTextAreaElement>();
const toolHistory = ref<ToolRecord[]>([]);
const selectedToolIdx = ref(-1);
const showAllTools = ref(false);
const MAX_VISIBLE_TOOLS = 6;

const visibleToolHistory = computed(() => {
  // 反转：最新的在最前面
  const reversed = toolHistory.value.map((t, i) => ({ ...t, idx: i })).reverse();
  return showAllTools.value ? reversed : reversed.slice(0, MAX_VISIBLE_TOOLS);
});

const selectedTool = ref<ToolRecord | null>(null);

onMounted(() => {
  // 隐藏 Footer
  const footer = document.querySelector('body > footer');
  if (footer) (footer as HTMLElement).style.display = 'none';

  loggedIn.value = $isLoggedIn.get();
  $isLoggedIn.listen(v => { loggedIn.value = v; });
  fetchSessions();
  // 优先 URL 参数，其次 localStorage
  const params = new URLSearchParams(window.location.search);
  const urlSid = params.get('session');
  if (urlSid) {
    sessionId.value = urlSid;
    localStorage.setItem('agentSessionId', urlSid);
  } else {
    const saved = localStorage.getItem('agentSessionId');
    if (saved) { sessionId.value = saved; localStorage.removeItem('agentSessionId'); }
  }
});

onUnmounted(() => {
  const footer = document.querySelector('body > footer');
  if (footer) (footer as HTMLElement).style.display = '';
});

function selectTool(idx: number, block: AgentBlock) {
  selectedToolIdx.value = idx;
  // 找到对应的 tool_result (同一个 tool 名且后面最近的那个)
  // 简化：从 toolHistory 中取
  if (idx < toolHistory.value.length) {
    selectedTool.value = toolHistory.value[idx];
  }
}

function newSession() {
  sessionId.value = null;
  messages.value = [];
  toolHistory.value = [];
  selectedToolIdx.value = -1;
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
async function exportChat() {
  if (!sessionId.value) return;
  try {
    const token = getToken();
    const resp = await fetch('/api/psychological-chat/export/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', token: token || '' },
      body: JSON.stringify({ sessionId: sessionId.value, format: 'txt' }),
    });
    const j = await resp.json();
    if (j.code === '200' && j.data?.downloadToken) {
      window.open(`/api/psychological-chat/export?sessionId=${sessionId.value}&format=txt&dt=${j.data.downloadToken}`, '_blank');
    }
  } catch { /* */ }
}

function autoResize() {
  if (!textareaRef.value) return;
  const el = textareaRef.value;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}

function isExportResult(r: any): boolean {
  if (!r) return false;
  const fmt = (r.format || '').toLowerCase().trim();
  return !!(r.url && r.filename && ['pdf','docx','txt'].includes(fmt));
}

function renderMarkdown(content: string): string {
  if (!content) return '';
  return marked.parse(content, { breaks: true }) as string;
}
function fixStatus(s: string | undefined): 'done' | 'running' | 'error' | undefined {
  if (s === 'done' || s === 'running' || s === 'error') return s;
  return undefined;
}

async function sendMsg() {
  const text = input.value.trim();
  if (!text || streaming.value) return;
  // 附加上传文件
  let fullText = text;
  if (uploadedFiles.value.length > 0) {
    fullText += '\n\n[上传文件]';
    uploadedFiles.value.forEach(f => { fullText += `\n- ${f.name}: ${window.location.origin}${f.url}`; });
    uploadedFiles.value = [];
  }
  messages.value.push({ role: 'user', content: fullText });
  input.value = '';
  const token = getToken();
  streaming.value = true;

  const aiMsg: UIMessage = { role: 'assistant', content: '', streaming: true };
  messages.value.push(aiMsg);
  await nextTick();
  scrollDown();

  try {
    if (!sessionId.value) {
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
        messages.value.pop();
        streaming.value = false;
        return;
      }
    }

    const blocks: AgentBlock[] = [];
    blocks.push({ type: 'text', content: '...', streaming: true });
    aiMsg.blocks = blocks;
    let fullContent = '';
    streamCtrl.value = new AbortController();

    await fetchEventSource('/api/psychological-chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream', token: token || '' },
      body: JSON.stringify({ sessionId: sessionId.value, userMessage: fullText }),
      signal: streamCtrl.value.signal,
      openWhenHidden: true,
      onmessage(event) {
        const evt = event.event || 'message';
        const raw = event.data || '';
        if (evt === 'tool_call') {
          try {
            const d = JSON.parse(raw);
            blocks.push({ type: 'tool_call', tool: d.tool, args: d.args, status: 'running' });
            const rec: ToolRecord = { displayName: TOOL_NAMES[d.tool] || d.tool, tool: d.tool, status: 'running', args: d.args };
            toolHistory.value.push(rec);
            if (selectedToolIdx.value < 0) selectedToolIdx.value = toolHistory.value.length - 1;
          } catch {}
          scrollDown();
        } else if (evt === 'tool_result') {
          try {
            const d = JSON.parse(raw);
            // 强制响应式更新
            for (let i = blocks.length - 1; i >= 0; i--) {
              if (blocks[i].type === 'tool_call' && blocks[i].tool === d.tool) {
                blocks.splice(i, 1, { ...blocks[i], status: 'done' });
                break;
              }
            }
            blocks.push({ type: 'tool_result', result: d.result });
            // update tool history
            const lastRec = [...toolHistory.value].reverse().find(r => r.tool === d.tool);
            if (lastRec) { lastRec.status = 'done'; lastRec.result = d.result; }
            selectedTool.value = [...toolHistory.value].reverse().find(r => r.tool === d.tool) || null;
          } catch {}
          scrollDown();
        } else if (evt === 'message') {
          try {
            const d = JSON.parse(raw);
            const t = d.text || '';
            fullContent += t;
            const lastText = blocks.length > 0 && blocks[blocks.length - 1].type === 'text' ? blocks[blocks.length - 1] : null;
            if (lastText && lastText.streaming && lastText.content === '...') lastText.content = t;
            else if (lastText && lastText.streaming) lastText.content = (lastText.content || '') + t;
            else blocks.push({ type: 'text', content: t, streaming: true });
          } catch {
            fullContent += raw;
            const lastText = blocks.length > 0 && blocks[blocks.length - 1].type === 'text' ? blocks[blocks.length - 1] : null;
            if (lastText && lastText.streaming && lastText.content === '...') lastText.content = raw;
            else if (lastText && lastText.streaming) lastText.content = (lastText.content || '') + raw;
            else blocks.push({ type: 'text', content: raw, streaming: true });
          }
          aiMsg.content = fullContent;
          scrollDown();
        } else if (evt === 'done') {
          blocks.forEach(b => { if (b.streaming !== undefined) b.streaming = false; });
          streaming.value = false;
        } else if (evt === 'error') {
          streaming.value = false;
        }
      },
      onerror(err) {
        streaming.value = false;
        streamCtrl.value?.abort();
        throw err;
      },
      onclose() { streaming.value = false; },
    });
  } catch {
    streaming.value = false;
  }
}

async function scrollDown() {
  await nextTick();
  if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
}
</script>

<style scoped>
.agent-page { display: flex; flex-direction: column; position: fixed; inset: 64px 0 0 0; z-index: 1; background: #fff; }
.agent-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0;
}
.back-btn { color: #6b7280; text-decoration: none; font-size: 14px; }
.back-btn:hover { color: #5b7bff; }
.agent-title { font-size: 18px; font-weight: 700; color: #1e293b; }
.header-actions { display: flex; gap: 8px; }
.action-btn { padding: 6px 14px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; cursor: pointer; font-size: 13px; color: #6b7280; }
.action-btn:hover { border-color: #5b7bff; color: #5b7bff; }

.agent-body { display: flex; flex: 1; overflow: hidden; }
.chat-panel { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px 24px; }
.chat-input-area { padding: 16px 24px; border-top: 1px solid #e5e7eb; }
.input-row { display: flex; gap: 10px; align-items: flex-end; }
.export-inline-card { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; margin: 4px 0; }
.inline-dl-btn { padding: 5px 14px; background: #16a34a; color: #fff; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 600; }
.inline-dl-btn:hover { background: #15803d; }

.chat-textarea {
  flex: 1; padding: 10px 16px; border: 1px solid #e5e7eb; border-radius: 12px;
  font-size: 14px; resize: none; outline: none; font-family: inherit; line-height: 1.5;
  color: #1e293b !important; -webkit-text-fill-color: #1e293b !important;
  background: #fff;
}
.chat-textarea::placeholder { color: #9ca3af !important; }
.chat-textarea:focus { border-color: #5b7bff; box-shadow: 0 0 0 2px rgba(91,123,255,0.15); }
.send-btn {
  width: 42px; height: 42px; border-radius: 12px; background: #5b7bff;
  border: none; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.stop-btn {
  width: 42px; height: 42px; border-radius: 12px; background: #ef4444;
  border: none; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.stop-btn:hover { background: #dc2626; }

/* Drop zone */
.drop-zone {
  border: 2px dashed #cbd5e1; border-radius: 8px; padding: 10px 16px;
  text-align: center; font-size: 13px; color: #94a3b8; margin-bottom: 8px;
  transition: border-color .2s, background .2s;
}
.drop-zone.dragging { border-color: #5b7bff; background: #eff6ff; color: #5b7bff; }
.upload-link { color: #5b7bff; cursor: pointer; text-decoration: underline; }
.hidden-input { display: none; }
.upload-preview { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.file-tag {
  display: flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 14px; background: #eff6ff;
  color: #3b82f6; font-size: 12px;
}
.file-remove { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; }
.file-remove:hover { color: #ef4444; }

.tool-panel {
  width: 360px; border-left: 1px solid #e5e7eb; flex-shrink: 0;
  display: flex; flex-direction: column; overflow-y: auto; padding: 16px;
}
.panel-title { font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 12px; }
.panel-empty { color: #94a3b8; font-size: 13px; text-align: center; padding: 40px 0; }
.tool-history { margin-bottom: 16px; }
.tool-history-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 8px; cursor: pointer; font-size: 13px; color: #475569;
}
.tool-history-item:hover { background: #f1f5f9; }
.tool-history-item.active { background: #eff6ff; color: #3b82f6; }
.tool-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.tool-dot.running { background: #f59e0b; animation: pulse 1s infinite; }
.tool-dot.done { background: #16a34a; }
.tool-history-item.newest { background: #fffbeb; }
.tool-running-badge { font-size: 10px; padding: 1px 6px; border-radius: 10px; background: #fef3c7; color: #d97706; margin-left: auto; }
.toggle-tools-btn { width: 100%; border: 1px dashed #e2e8f0; background: none; padding: 6px; border-radius: 8px; font-size: 12px; color: #94a3b8; cursor: pointer; }
.toggle-tools-btn:hover { background: #f8fafc; color: #64748b; }
@keyframes pulse { 50% { opacity: 0.5; } }
.tool-detail { flex: 1; overflow-y: auto; border-top: 1px solid #e5e7eb; padding-top: 12px; }
.tool-detail h4 { font-size: 13px; color: #475569; margin-bottom: 8px; }
.article-card-detailed {
  display: block; padding: 10px; margin-bottom: 8px; border-radius: 8px;
  background: #f8fafc; text-decoration: none; color: inherit; border: 1px solid #e2e8f0;
}
.article-card-detailed:hover { border-color: #5b7bff; }
.art-title { font-weight: 600; font-size: 14px; color: #1e293b; }
.art-meta { display: flex; gap: 8px; margin-top: 4px; }
.art-cat { font-size: 11px; color: #5b7bff; }
.art-date { font-size: 11px; color: #94a3b8; }
.art-summary { font-size: 12px; color: #64748b; margin-top: 4px; line-height: 1.4; }
.cat-list { display: flex; flex-wrap: wrap; gap: 6px; }
.cat-item { padding: 4px 10px; background: #eff6ff; border-radius: 16px; font-size: 12px; color: #3b82f6; }
.cat-count { color: #93c5fd; margin-left: 4px; }
.tool-raw { font-size: 11px; color: #94a3b8; white-space: pre-wrap; }

.msg-row { margin-bottom: 12px; align-items: flex-start; }
.user-row { display: flex; justify-content: flex-end; gap: 8px; }
.ai-row { display: flex; justify-content: flex-start; gap: 8px; }
.avatar-circle {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 16px;
  margin-top: 4px;
}
.avatar-ai { background: linear-gradient(135deg, #818cf8, #6366f1); }
.avatar-user { background: linear-gradient(135deg, #fbbf24, #f97316); }
.user-bubble { background: #5b7bff; color: #fff; border-radius: 16px 16px 4px 16px; padding: 10px 16px; font-size: 14px; max-width: 70%; }
.msg-blocks { max-width: 100%; display: flex; flex-direction: column; gap: 2px; }
.ai-bubble { background: #fff; color: #1e293b; border-radius: 4px 16px 16px 16px; padding: 10px 16px; font-size: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

.login-prompt { text-align: center; padding: 60px 0; }
.login-prompt p { color: #6b7280; margin-bottom: 16px; }
.btn-login { display: inline-block; padding: 10px 24px; background: #5b7bff; color: #fff; border-radius: 8px; text-decoration: none; }
.empty-state { text-align: center; padding: 60px 0; color: #94a3b8; }
.empty-state .hint { font-size: 13px; margin-top: 8px; }

@media (max-width: 768px) {
  .tool-panel { display: none; }
  .history-sidebar { width: 0; }
}

/* History sidebar */
.history-sidebar {
  width: 0; overflow-y: auto; overflow-x: hidden;
  border-right: 1px solid #e5e7eb; background: #fafafa;
  transition: width 0.25s; flex-shrink: 0;
}
.history-sidebar.open { width: 220px; }
.history-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px; border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; background: #fafafa;
}
.history-title { font-size: 13px; font-weight: 600; color: #475569; }
.history-new-btn { font-size: 11px; color: #5b7bff; background: none; border: none; cursor: pointer; }
.history-loading, .history-empty { padding: 24px; text-align: center; font-size: 12px; color: #94a3b8; }
.history-item {
  display: flex; align-items: center; border-bottom: 1px solid #f1f5f9; transition: background 0.15s;
}
.history-item:hover { background: #f1f5f9; }
.history-item.active { background: #eff6ff; }
.history-item-main { flex: 1; min-width: 0; padding: 10px 0 10px 12px; cursor: pointer; }
.history-item-title { font-size: 12px; font-weight: 500; color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.history-item-preview { font-size: 10px; color: #94a3b8; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.history-delete {
  flex-shrink: 0; padding: 8px; color: #d1d5db; background: none; border: none; cursor: pointer;
  opacity: 0; transition: opacity 0.15s, color 0.15s;
}
.history-item:hover .history-delete { opacity: 1; }
.history-delete:hover { color: #ef4444; }
.history-toggle-btn {
  flex-shrink: 0; width: 32px;
  background: #f8fafc; border: 1px solid #e5e7eb; border-left: none;
  cursor: pointer; color: #94a3b8; display: flex; align-items: center; justify-content: center;
}
.history-toggle-btn:hover { color: #5b7bff; background: #f1f5f9; }

/* ── Markdown 表格样式 ── */
:deep(table) { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 12px; }
:deep(th) { background: #f1f5f9; color: #475569; padding: 6px 10px; border: 1px solid #e2e8f0; text-align: left; font-weight: 600; }
:deep(td) { padding: 5px 10px; border: 1px solid #e2e8f0; color: #334155; }
:deep(tr:nth-child(even) td) { background: #f8fafc; }
</style>
