<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 pt-8 pb-12">
    <!-- Not logged in -->
    <div v-if="!loggedIn" class="text-center py-20">
      <p class="text-gray-400 text-lg mb-4">请先登录</p>
      <a href="/auth/login" class="px-6 py-2.5 rounded-button bg-brand-600 text-white font-medium">去登录</a>
    </div>

    <div v-else>
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <a href="/" class="text-sm text-gray-400 hover:text-gray-600">← 返回</a>
        <div class="flex gap-2">
          <button @click="saveDraft" :disabled="saving" class="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50">存草稿</button>
          <button @click="publishArticle" :disabled="saving" class="px-4 py-2 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 disabled:opacity-50">
            {{ saving ? '发布中...' : '发布' }}
          </button>
        </div>
      </div>

      <!-- Title -->
      <input v-model="title" placeholder="文章标题..." class="w-full text-3xl font-bold text-gray-800 mb-4 outline-none border-none bg-transparent placeholder-gray-300" />

      <!-- Category + Tags -->
      <div class="flex gap-3 mb-6">
        <select v-model="categoryId" class="px-3 py-2 border rounded-lg text-sm outline-none text-gray-600">
          <option :value="0">选择分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.categoryName }}</option>
        </select>
        <input v-model="tags" placeholder="标签 (逗号分隔)" class="flex-1 px-3 py-2 border rounded-lg text-sm outline-none text-gray-600" />
      </div>

      <!-- Toolbar -->
      <div class="flex items-center gap-1 mb-3 p-2 bg-gray-50 rounded-xl border flex-wrap">
        <button v-for="t in tools" :key="t.cmd" @click="execCmd(t.cmd, t.arg)" class="w-8 h-8 rounded-lg hover:bg-white hover:shadow-sm transition-colors flex items-center justify-center text-gray-500" :title="t.title">
          <span v-html="t.icon" />
        </button>
        <span class="w-px h-5 bg-gray-200 mx-1" />
        <label class="w-8 h-8 rounded-lg hover:bg-white hover:shadow-sm transition-colors flex items-center justify-center text-gray-500 cursor-pointer" title="插入图片">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          <input type="file" accept="image/*" class="hidden" @change="uploadImage" />
        </label>
      </div>

      <!-- Editor -->
      <div
        ref="editorRef"
        class="editor-area min-h-[400px] border border-gray-200 rounded-xl p-6 prose prose-lg max-w-none focus:outline-none"
        contenteditable="true"
        @input="onContentInput"
        @paste="onPaste"
        @keydown="onKeydown"
        @keydown.tab.prevent="onTab"
        @keydown.shift.tab.prevent="onShiftTab"
        @keydown.shift.enter.prevent="onShiftEnter"
        placeholder="开始写文章..."
      />

      <!-- Slash Menu -->
      <div v-if="slashOpen" class="fixed z-50 w-64 glass-card p-1 shadow-2xl" :style="slashPos">
        <button v-for="(opt, i) in slashOptions" :key="opt.label"
          @click="applySlash(opt)"
          :class="['flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-left transition-colors', i === slashIndex ? 'bg-brand-50 text-brand-600' : 'hover:bg-brand-50 hover:text-brand-600']">
          <span class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold" :class="opt.bg">{{ opt.icon }}</span>
          <div>
            <div class="text-xs font-medium text-gray-700">{{ opt.label }}</div>
            <div class="text-[10px] text-gray-400">{{ opt.desc }}</div>
          </div>
        </button>
      </div>

      <!-- Success toast -->
      <div v-if="success" class="fixed top-20 left-1/2 -translate-x-1/2 bg-green-500 text-white px-6 py-3 rounded-xl shadow-lg z-50 text-sm">{{ success }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { $isLoggedIn } from '@lib/store';
import { getToken } from '@lib/auth';

const loggedIn = ref(false);
const title = ref('');
const categoryId = ref(0);
const tags = ref('');
const saving = ref(false);
const success = ref('');
const categories = ref<any[]>([]);
const editorRef = ref<HTMLElement>();

onMounted(async () => {
  loggedIn.value = $isLoggedIn.get();
  try {
    const r = await fetch('/api/knowledge/category/tree');
    const j = await r.json();
    if (j.code === '200') categories.value = j.data;
  } catch { /* */ }
});

function execCmd(cmd: string, arg?: string) {
  document.execCommand(cmd, false, arg);
  editorRef.value?.focus();
  setPlaceholder();
}

function insertImageAtCursor(url: string) {
  const editor = editorRef.value;
  if (!editor) return;
  editor.focus();
  // Restore selection or insert at end
  const sel = window.getSelection();
  if (sel && sel.rangeCount > 0 && editor.contains(sel.anchorNode)) {
    const range = sel.getRangeAt(0);
    const img = document.createElement('img');
    img.src = url;
    img.className = 'rounded-xl shadow-lg my-4 max-w-full';
    img.style.maxWidth = '100%';
    range.insertNode(img);
    range.collapse(false);
    // Add a line break after image
    const br = document.createElement('br');
    range.insertNode(br);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
  } else {
    // Fallback: append at end
    const img = document.createElement('img');
    img.src = url;
    img.className = 'rounded-xl shadow-lg my-4 max-w-full';
    img.style.maxWidth = '100%';
    editor.appendChild(img);
    editor.appendChild(document.createElement('br'));
  }
  editor.focus();
}

const slashOpen = ref(false);
const slashPos = ref({ left: '0px', top: '0px' });
const slashFilter = ref('');
const slashIndex = ref(0);
const slashOptions = [
  { label: '一级标题', desc: '大标题', icon: 'H1', bg: 'bg-red-100 text-red-600', cmd: 'h1' },
  { label: '二级标题', desc: '中等标题', icon: 'H2', bg: 'bg-orange-100 text-orange-600', cmd: 'h2' },
  { label: '三级标题', desc: '小标题', icon: 'H3', bg: 'bg-amber-100 text-amber-600', cmd: 'h3' },
  { label: '四级标题', desc: '细标题', icon: 'H4', bg: 'bg-green-100 text-green-600', cmd: 'h4' },
  { label: '五级标题', desc: '更小标题', icon: 'H5', bg: 'bg-teal-100 text-teal-600', cmd: 'h5' },
  { label: '六级标题', desc: '最小标题', icon: 'H6', bg: 'bg-blue-100 text-blue-600', cmd: 'h6' },
  { label: '标注模块', desc: '高亮提示框', icon: '!', bg: 'bg-purple-100 text-purple-600', cmd: 'callout' },
  { label: '编号列表', desc: '1. 2. 3. 自动排序', icon: '1.', bg: 'bg-gray-100 text-gray-600', cmd: 'ol' },
  { label: '无序列表', desc: '• 项目符号', icon: '•', bg: 'bg-gray-100 text-gray-600', cmd: 'ul' },
  { label: '引用', desc: '引用文字', icon: '"', bg: 'bg-gray-100 text-gray-600', cmd: 'blockquote' },
  { label: '分隔线', desc: '视觉分割', icon: '—', bg: 'bg-gray-100 text-gray-600', cmd: 'hr' },
  { label: '代码块', desc: '代码片段', icon: '<>', bg: 'bg-gray-100 text-gray-600', cmd: 'pre' },
];

function checkSlash() {
  const sel = window.getSelection();
  if (!sel?.rangeCount) { slashOpen.value = false; return; }
  const node = sel.anchorNode;
  if (!node) { slashOpen.value = false; return; }
  let block = node.nodeType === 3 ? node.parentElement : node as Element;
  while (block && !['P','DIV','H1','H2','H3','H4','H5','H6','LI','BLOCKQUOTE'].includes(block.tagName)) {
    block = block.parentElement;
  }
  const text = block?.textContent || '';
  const slashIdx = text.lastIndexOf('/');
  if (slashIdx >= 0 && (slashIdx === 0 || text[slashIdx - 1] === ' ')) {
    slashFilter.value = text.slice(slashIdx + 1).toLowerCase();
    const sel = window.getSelection();
    if (sel?.rangeCount) {
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      slashPos.value = { left: rect.left + 'px', top: (rect.bottom + 6) + 'px' };
    }
    slashOpen.value = true;
    slashIndex.value = 0;
  } else {
    slashOpen.value = false;
  }
}

function applySlash(opt: typeof slashOptions[0]) {
  const sel = window.getSelection();
  if (!sel?.rangeCount) return;
  const node = sel.anchorNode;
  if (!node) return;

  // Get current block
  let block = node.nodeType === 3 ? node.parentElement : node as Element;
  while (block && !['P','DIV','H1','H2','H3','H4','H5','H6','LI','BLOCKQUOTE'].includes(block.tagName)) {
    block = block.parentElement;
  }
  if (!block) return;

  // Get text up to cursor, find last /
  const fullText = block.textContent || '';
  let slashIdx = fullText.lastIndexOf('/');
  const textBeforeSlash = fullText.slice(0, slashIdx);
  const cleanText = textBeforeSlash.trim();

  // Remove the /command text from current block
  block.textContent = cleanText || '​'; // zero-width space to keep block alive

  if (opt.cmd === 'callout') {
    // Insert a callout box at cursor position, AFTER current block
    // Transform current block INTO a callout, wrapping existing content
    const existingContent = block.innerHTML && block.innerHTML !== '<br>' ? block.innerHTML : '写标注内容...';
    block.innerHTML = '💡 <span>' + existingContent + '</span>';
    block.setAttribute('data-callout', 'true');
    (block as HTMLElement).style.cssText = 'background:rgba(91,123,255,0.06);border:1px solid rgba(91,123,255,0.15);border-radius:10px;padding:12px 16px;margin:8px 0;outline:none;font-size:14px;color:#374151;';
    // Insert empty paragraph after callout
    const afterP = document.createElement('p');
    afterP.innerHTML = '<br>';
    block.parentNode?.insertBefore(afterP, block.nextSibling);
    // Focus inside the span
    const span = block.querySelector('span');
    if (span) {
      const sel = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(span);
      sel?.removeAllRanges();
      sel?.addRange(range);
    }
  } else if (opt.cmd === 'ol') {
    document.execCommand('insertOrderedList');
  } else if (opt.cmd === 'ul') {
    document.execCommand('insertUnorderedList');
  } else if (opt.cmd === 'hr') {
    document.execCommand('insertHorizontalRule');
  } else if (opt.cmd === 'pre') {
    document.execCommand('formatBlock', false, 'pre');
    // Auto-indent: insert 2 spaces at start
    setTimeout(() => {
      const pres = editorRef.value?.querySelectorAll('pre');
      const lastPre = pres?.[pres.length - 1];
      if (lastPre && !lastPre.textContent?.trim()) {
        lastPre.textContent = '  ';
        const sel = window.getSelection();
        const r = document.createRange();
        r.setStart(lastPre.firstChild || lastPre, 2);
        r.collapse(true);
        sel?.removeAllRanges();
        sel?.addRange(r);
      }
    }, 20);
    editorRef.value?.focus();
  } else {
    // h1-h6 or blockquote: apply style to current block
    document.execCommand('formatBlock', false, opt.cmd);
    editorRef.value?.focus();
  }
  slashOpen.value = false;
}

function onContentInput() { setPlaceholder(); checkSlash(); }

function onTab() {
  const sel = window.getSelection();
  if (!sel?.rangeCount) return;
  let block = sel.anchorNode?.nodeType === 3 ? sel.anchorNode.parentElement : sel.anchorNode as Element;
  while (block && !['P','DIV','H1','H2','H3','H4','H5','H6','LI','BLOCKQUOTE','PRE'].includes(block.tagName)) {
    block = block?.parentElement as Element;
  }
  // Only indent list items
  if (block?.tagName === 'LI') {
    document.execCommand('indent');
  } else {
    // Insert 2 spaces as tab
    document.execCommand('insertText', false, '  ');
  }
}
function onShiftEnter() {
  const sel = window.getSelection();
  if (!sel?.rangeCount) return;
  let block = sel.anchorNode?.nodeType === 3 ? sel.anchorNode.parentElement : sel.anchorNode as Element;
  while (block && !['PRE','P','DIV','H1','H2','H3','H4','H5','H6','LI','BLOCKQUOTE'].includes(block.tagName)) {
    block = block?.parentElement as Element;
  }
  if (block?.tagName === 'PRE') {
    // Exit code block: insert paragraph after
    const p = document.createElement('p');
    p.innerHTML = '<br>';
    block.parentNode?.insertBefore(p, block.nextSibling);
    p.focus();
    const r = document.createRange();
    r.setStart(p, 0);
    r.collapse(true);
    sel.removeAllRanges();
    sel.addRange(r);
  }
}

function onShiftTab() {
  const sel = window.getSelection();
  if (!sel?.rangeCount) return;
  let block = sel.anchorNode?.nodeType === 3 ? sel.anchorNode.parentElement : sel.anchorNode as Element;
  while (block && !['P','DIV','H1','H2','H3','H4','H5','H6','LI','BLOCKQUOTE','PRE'].includes(block.tagName)) {
    block = block?.parentElement as Element;
  }
  if (block?.tagName === 'LI') {
    document.execCommand('outdent');
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') { slashOpen.value = false; return; }
  if (slashOpen.value && e.key === 'ArrowDown') { e.preventDefault(); slashIndex.value = Math.min(slashIndex.value + 1, slashOptions.length - 1); return; }
  if (slashOpen.value && e.key === 'ArrowUp') { e.preventDefault(); slashIndex.value = Math.max(slashIndex.value - 1, 0); return; }
  if (slashOpen.value && e.key === 'Enter') { e.preventDefault(); applySlash(slashOptions[slashIndex.value]); return; }
  if (e.key !== 'Enter') { checkSlash(); return; }
  if (slashOpen.value) { slashOpen.value = false; return; }
  setTimeout(() => {
    autoFormat();
    // After Enter: headings/blockquote → paragraph (first Enter)
    setTimeout(() => {
      // Delay to let browser finish creating new block
      const sel = window.getSelection();
      if (!sel?.rangeCount || !sel.anchorNode) return;
      let block = sel.anchorNode.nodeType === 3 ? sel.anchorNode.parentElement : sel.anchorNode as Element;
      while (block && !['P','DIV','H1','H2','H3','H4','H5','H6','LI','BLOCKQUOTE','PRE'].includes(block.tagName)) {
        block = block.parentElement;
      }
      if (!block) return;

      // If in heading, callout, blockquote, or pre → new line should be paragraph
      // Pre/code blocks: Enter stays inside (browser native newline)
      // For other styled blocks: empty → revert to paragraph
      if (['H1','H2','H3','H4','H5','H6','BLOCKQUOTE'].includes(block.tagName)) {
        document.execCommand('formatBlock', false, 'p');
      }
      // If in empty li → break out of list
      if (block.tagName === 'LI' && !block.textContent?.trim()) {
        const listParent = block.closest('ul,ol');
        if (listParent) {
          const p = document.createElement('p');
          p.innerHTML = '<br>';
          listParent.parentNode?.insertBefore(p, listParent.nextSibling);
          block.remove();
          const range = document.createRange();
          range.setStart(p, 0);
          range.collapse(true);
          sel.removeAllRanges();
          sel.addRange(range);
        }
      }
      // If in callout and callout is now empty → convert back to paragraph
      if (block.getAttribute?.('data-callout') === 'true') {
        const text = block.textContent?.replace('💡', '').trim() || '';
        if (!text) {
          block.removeAttribute('data-callout');
          (block as HTMLElement).style.cssText = '';
          block.innerHTML = '<br>';
          document.execCommand('formatBlock', false, 'p');
        }
      }
    });
  }, 10);
}

function autoFormat() {
  const editor = editorRef.value;
  if (!editor) return;
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount) return;
  const node = sel.anchorNode;
  if (!node) return;

  // Find the current block
  let block = node.nodeType === 3 ? node.parentElement : node as Element;
  while (block && !['P','DIV','H1','H2','H3','H4','H5','H6','LI','BLOCKQUOTE','PRE'].includes(block.tagName)) {
    block = block.parentElement;
  }
  if (!block || block.tagName === 'PRE') return;

  const text = block.textContent?.trim() || '';

  // Select the block's text
  const range = document.createRange();
  range.selectNodeContents(block);
  sel.removeAllRanges();
  sel.addRange(range);

  // Headings via execCommand (preserves undo)
  const headingMatch = text.match(/^(#{1,6})\s+(.+)$/);
  if (headingMatch) {
    const level = headingMatch[1].length;
    if (level >= 1 && level <= 6) {
      document.execCommand('formatBlock', false, `h${level}`);
      block.textContent = headingMatch[2];
    }
    return;
  }

  // --- → hr (execCommand)
  if (/^(-{3,})$/.test(text)) {
    document.execCommand('insertHorizontalRule');
    block.textContent = '';
    return;
  }

  // > text → blockquote
  const quoteMatch = text.match(/^>\s+(.+)$/);
  if (quoteMatch) {
    document.execCommand('formatBlock', false, 'blockquote');
    block.textContent = quoteMatch[1];
    return;
  }

  // - item or * item → unordered list
  const ulMatch = text.match(/^[-*]\s+(.+)$/);
  if (ulMatch) {
    document.execCommand('insertUnorderedList');
    block.textContent = ulMatch[1];
    return;
  }

  // 1. item → ordered list
  const olMatch = text.match(/^\d+\.\s+(.+)$/);
  if (olMatch) {
    document.execCommand('insertOrderedList');
    block.textContent = olMatch[1];
    return;
  }

  // ``` → code block
  if (/^```$/.test(text)) {
    document.execCommand('formatBlock', false, 'pre');
    block.textContent = '';
    block.appendChild(document.createElement('br'));
    return;
  }

  // Inline formatting
  processInlineFormatting(block);
}

function processInlineFormatting(el: Element) {
  if (el.tagName === 'PRE') return;
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const textNodes: Text[] = [];
  let n;
  while ((n = walker.nextNode())) textNodes.push(n as Text);

  for (const tn of textNodes) {
    let t = tn.textContent || '';
    if (!/(\*\*|__|~~|`|\*|_)/.test(t)) continue;

    const parent = tn.parentElement;
    if (!parent || parent.tagName === 'PRE') continue;

    const frag = document.createDocumentFragment();
    const regex = /(\*\*(.+?)\*\*|__(.+?)__|~~(.+?)~~|`(.+?)`|\*(.+?)\*|_(.+?)_)/g;
    let lastIdx = 0;
    let match;

    while ((match = regex.exec(t)) !== null) {
      // Text before match
      if (match.index > lastIdx) {
        frag.appendChild(document.createTextNode(t.slice(lastIdx, match.index)));
      }
      if (match[2] !== undefined) {
        const strong = document.createElement('strong');
        strong.textContent = match[2];
        frag.appendChild(strong);
      } else if (match[3] !== undefined) {
        const strong = document.createElement('strong');
        strong.textContent = match[3];
        frag.appendChild(strong);
      } else if (match[4] !== undefined) {
        const del = document.createElement('s');
        del.textContent = match[4];
        frag.appendChild(del);
      } else if (match[5] !== undefined) {
        const code = document.createElement('code');
        code.textContent = match[5];
        frag.appendChild(code);
      } else if (match[6] !== undefined) {
        const em = document.createElement('em');
        em.textContent = match[6];
        frag.appendChild(em);
      } else if (match[7] !== undefined) {
        const em = document.createElement('em');
        em.textContent = match[7];
        frag.appendChild(em);
      }
      lastIdx = match.index + match[0].length;
    }

    if (lastIdx < t.length) {
      frag.appendChild(document.createTextNode(t.slice(lastIdx)));
    }

    if (frag.childNodes.length > 0) {
      parent.replaceChild(frag, tn);
    }
  }
}

function formatAllBlocks() {
  const editor = editorRef.value;
  if (!editor) return;
  // Process all paragraph-like blocks for markdown patterns
  const blocks = editor.querySelectorAll('p, div, h1, h2, h3, h4, h5, h6, li, blockquote');
  blocks.forEach(block => {
    const text = (block as HTMLElement).textContent?.trim() || '';
    // Headings
    const hm = text.match(/^(#{1,6})\s+(.+)$/);
    if (hm) {
      const level = hm[1].length;
      const h = document.createElement(`h${level}`);
      h.textContent = hm[2];
      h.style.outline = 'none';
      block.replaceWith(h);
      return;
    }
    // HR
    if (/^(-{3,})$/.test(text)) {
      const hr = document.createElement('hr');
      hr.style.cssText = 'border:none;height:1px;background:#e5e7eb;margin:1.5em 0;';
      block.replaceWith(hr);
      return;
    }
    // Blockquote
    const qm = text.match(/^>\s+(.+)$/);
    if (qm) {
      const bq = document.createElement('blockquote');
      bq.textContent = qm[1];
      bq.style.outline = 'none';
      block.replaceWith(bq);
      return;
    }
    // Unordered list
    const ulm = text.match(/^[-*]\s+(.+)$/);
    if (ulm) {
      const ul = document.createElement('ul');
      const li = document.createElement('li');
      li.textContent = ulm[1];
      li.style.outline = 'none';
      ul.appendChild(li);
      block.replaceWith(ul);
      return;
    }
    // Ordered list
    const olm = text.match(/^\d+\.\s+(.+)$/);
    if (olm) {
      const ol = document.createElement('ol');
      const li = document.createElement('li');
      li.textContent = olm[1];
      li.style.outline = 'none';
      ol.appendChild(li);
      block.replaceWith(ol);
    }
  });
}

function setCursorAtStart(el: Element) {
  const sel = window.getSelection();
  if (!sel) return;
  const range = document.createRange();
  range.setStart(el, 0);
  range.collapse(true);
  sel.removeAllRanges();
  sel.addRange(range);
}

function setCursorAfter(el: Element) {
  const sel = window.getSelection();
  if (!sel) return;
  const range = document.createRange();
  range.setStartAfter(el);
  range.collapse(true);
  sel.removeAllRanges();
  sel.addRange(range);
}

async function onPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of Array.from(items)) {
    if (item.type.startsWith('image/')) {
      e.preventDefault();
      const file = item.getAsFile();
      if (!file) continue;
      const fd = new FormData();
      fd.append('file', file);
      try {
        const res = await fetch('/api/file/simple/upload/image', {
          method: 'POST', headers: { token: getToken() || '' }, body: fd,
        });
        const j = await res.json();
        if (j.code === '200' && j.data?.url) {
          insertImageAtCursor(j.data.url);
        }
      } catch { /* */ }
      return;
    }
  }

  // Get plain text from clipboard
  const text = e.clipboardData?.getData('text/plain');
  if (!text) return;

  // Prevent default paste, insert formatted version instead
  e.preventDefault();

  // Convert markdown to HTML
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Block-level patterns
  const lines = html.split('\n');
  const result: string[] = [];
  let inCodeBlock = false;
  let inUl = false, inOl = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block toggle
    if (/^```/.test(line)) {
      if (inCodeBlock) { result.push('</pre>'); inCodeBlock = false; continue; }
      else { inCodeBlock = true; result.push('<pre>'); continue; }
    }
    if (inCodeBlock) { result.push(line); continue; }

    // Close open lists
    if (inUl && !/^[-*]\s/.test(line)) { result.push('</ul>'); inUl = false; }
    if (inOl && !/^\d+\.\s/.test(line)) { result.push('</ol>'); inOl = false; }

    // HR
    if (/^(-{3,})$/.test(line.trim())) { result.push('<hr>'); continue; }

    // Heading
    let hm = line.trim().match(/^(#{1,6})\s+(.+)$/);
    if (hm) {
      const lv = hm[1].length;
      result.push(`<h${lv}>${processInline(hm[2])}</h${lv}>`);
      continue;
    }

    // Blockquote
    let qm = line.trim().match(/^>\s+(.+)$/);
    if (qm) { result.push(`<blockquote>${processInline(qm[1])}</blockquote>`); continue; }

    // Unordered list
    let um = line.trim().match(/^[-*]\s+(.+)$/);
    if (um) {
      if (!inUl) { result.push('<ul>'); inUl = true; }
      result.push(`<li>${processInline(um[1])}</li>`);
      continue;
    }

    // Ordered list
    let om = line.trim().match(/^\d+\.\s+(.+)$/);
    if (om) {
      if (!inOl) { result.push('<ol>'); inOl = true; }
      result.push(`<li>${processInline(om[1])}</li>`);
      continue;
    }

    // Regular paragraph
    if (line.trim()) {
      result.push(`<p>${processInline(line)}</p>`);
    } else {
      result.push('<br>');
      if (inUl) { result.push('</ul>'); inUl = false; }
      if (inOl) { result.push('</ol>'); inOl = false; }
    }
  }

  if (inUl) result.push('</ul>');
  if (inOl) result.push('</ol>');
  if (inCodeBlock) result.push('</pre>');

  // Insert as one atomic operation (Ctrl+Z undoable)
  document.execCommand('insertHTML', false, result.join('\n'));
}

function processInline(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/~~(.+?)~~/g, '<s>$1</s>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>');
}

function setPlaceholder() {
  if (editorRef.value && !editorRef.value.textContent?.trim()) {
    editorRef.value.innerHTML = '';
  }
}

async function uploadImage(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res = await fetch('/api/file/simple/upload/image', {
      method: 'POST',
      headers: { token: getToken() || '' },
      body: fd,
    });
    const j = await res.json();
    if (j.code === '200' && j.data?.url) {
      insertImageAtCursor(j.data.url);
    }
  } catch { /* */ }
}

async function saveArticle(status: number) {
  const content = editorRef.value?.innerHTML || '';
  if (!title.value.trim()) {
    showToast('请输入标题');
    return;
  }
  saving.value = true;
  try {
    const body = JSON.stringify({
      title: title.value, content, categoryId: categoryId.value,
      summary: editorRef.value?.textContent?.trim().slice(0, 200) || '',
      tags: tags.value.split(/[,，]/).map(t => t.trim()).filter(Boolean).join(','),
    });
    const res = await fetch('/api/knowledge/article', {
      method: 'POST', headers: { 'Content-Type': 'application/json', token: getToken() || '' }, body,
    });
    const j = await res.json();
    if (j.code === '200') {
      const articleId = j.data?.id;
      if (status === 1) {
        await fetch(`/api/knowledge/article/${articleId}/publish`, {
          method: 'POST', headers: { token: getToken() || '' },
        });
        showToast('发布成功！');
        setTimeout(() => { window.location.href = `/blog/${articleId}`; }, 800);
      } else {
        showToast('草稿已保存');
      }
    } else {
      showToast('保存失败');
    }
  } catch { /* */ }
  saving.value = false;
}

function saveDraft() { saveArticle(0); }
function publishArticle() { saveArticle(1); }

function showToast(msg: string) {
  success.value = msg;
  setTimeout(() => { success.value = ''; }, 2000);
}

const tools = [
  { cmd: 'bold', title: '粗体', icon: '<b class="text-xs">B</b>' },
  { cmd: 'italic', title: '斜体', icon: '<i class="text-xs">I</i>' },
  { cmd: 'underline', title: '下划线', icon: '<u class="text-xs">U</u>' },
  { cmd: 'strikeThrough', title: '删除线', icon: '<s class="text-xs">S</s>' },
  { cmd: 'formatBlock', arg: 'h2', title: '标题2', icon: '<span class="text-[10px] font-bold">H2</span>' },
  { cmd: 'formatBlock', arg: 'h3', title: '标题3', icon: '<span class="text-[10px] font-bold">H3</span>' },
  { cmd: 'insertUnorderedList', title: '无序列表', icon: '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>' },
  { cmd: 'insertOrderedList', title: '有序列表', icon: '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20h14M7 12h14M7 4h14M3 20h.01M3 12h.01M3 4h.01"/></svg>' },
  { cmd: 'formatBlock', arg: 'blockquote', title: '引用', icon: '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>' },
  { cmd: 'formatBlock', arg: 'pre', title: '代码块', icon: '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>' },
  { cmd: 'removeFormat', title: '清除格式', icon: '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' },
];
</script>

<style>
.editor-area,
.editor-area > * {
  background-color: #f0f2f5 !important;
}
.editor-area pre,
.editor-area pre *,
.editor-area [data-codeblock],
.editor-area [data-codeblock] * {
  background-color: #1e293b !important;
  color: #e2e8f0 !important;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.6 !important;
  border-radius: 10px !important;
}
.editor-area code:not(pre code):not([data-codeblock] code) {
  background-color: #fef3c7 !important;
}
.editor-area {
  color: #374151 !important;
  caret-color: #5b7bff;
}
.editor-area:empty::before {
  content: '开始写文章...';
  color: #d1d5db;
}

/* Notion-style blocks */
.editor-area > p,
.editor-area > h1,
.editor-area > h2,
.editor-area > h3,
.editor-area > h4,
.editor-area > h5,
.editor-area > h6,
.editor-area > ul,
.editor-area > ol,
.editor-area > blockquote,
.editor-area > pre,
.editor-area > hr {
  margin: 2px 0 !important;
  padding: 6px 12px !important;
  border-radius: 6px;
  transition: background 0.15s ease;
}

.editor-area > p:hover,
.editor-area > h1:hover,
.editor-area > h2:hover,
.editor-area > h3:hover,
.editor-area > li:hover {
  background: rgba(91, 123, 255, 0.04);
}

/* Visual indent levels for nested lists */
.editor-area ul ul,
.editor-area ol ol,
.editor-area ul ol,
.editor-area ol ul {
  padding-left: 24px !important;
  border-left: 2px solid rgba(91, 123, 255, 0.15);
  margin-left: 4px !important;
}

/* Inline editing cursor color */
.editor-area:focus {
  caret-color: #5b7bff;
}
</style>