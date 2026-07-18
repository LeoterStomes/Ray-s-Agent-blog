<template>
  <div class="comment-section" style="margin-top:32px">
    <!-- 标题栏 -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid #1e293b">
      <h3 style="color:#e2e8f0;font-size:18px;font-weight:600;margin:0">
        💬 评论 <span v-if="total > 0" style="color:#64748b;font-size:14px;font-weight:400">({{ total }})</span>
      </h3>
    </div>

    <!-- 登录提示 / 评论输入框 -->
    <div v-if="!isLoggedIn" style="background:#1e1b4b;border:1px solid #312e81;border-radius:8px;padding:16px 20px;text-align:center;color:#a5b4fc;font-size:14px;margin-bottom:20px">
      <a href="/login" style="color:#818cf8;text-decoration:underline">登录</a> 后即可评论
    </div>
    <div v-else class="comment-form" style="margin-bottom:24px">
      <div style="display:flex;gap:12px;align-items:flex-start">
        <img :src="avatarUrl" style="width:36px;height:36px;border-radius:50%;flex-shrink:0;object-fit:cover;border:1px solid #334155"
             @error="(e) => (e.target as HTMLImageElement).src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 36 36%22%3E%3Ccircle fill=%22%23334155%22 cx=%2218%22 cy=%2218%22 r=%2218%22/%3E%3Ctext fill=%22%2394a3b8%22 x=%2218%22 y=%2223%22 text-anchor=%22middle%22 font-size=%2216%22%3E%3C/text%3E%3C/svg%3E'" />
        <div style="flex:1;min-width:0">
          <textarea
            v-model="newComment"
            :placeholder="replyTarget ? `回复 @${replyTarget.nickname}...` : '写点什么...'"
            rows="3"
            style="width:100%;background:#0f172a;border:1px solid #334155;border-radius:8px;padding:10px 14px;color:#e2e8f0;font-size:14px;resize:vertical;outline:none;font-family:inherit"
            @keydown.enter.ctrl="submitComment"
          ></textarea>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">
            <span v-if="replyTarget" style="font-size:12px;color:#64748b">
              回复 <span style="color:#a5b4fc">{{ replyTarget.nickname }}</span> &nbsp;
              <button @click="cancelReply" style="background:none;border:none;color:#ef4444;cursor:pointer;font-size:12px">取消</button>
            </span>
            <span v-else></span>
            <button
              @click="submitComment"
              :disabled="!newComment.trim() || submitting"
              style="background:#6366f1;color:#fff;border:none;padding:6px 20px;border-radius:6px;font-size:13px;cursor:pointer;font-weight:500;transition:background .15s"
              :style="{ opacity: (!newComment.trim() || submitting) ? 0.5 : 1 }"
            >
              {{ submitting ? '发送中...' : '发表' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 评论列表 -->
    <div v-if="loading" style="text-align:center;padding:20px;color:#64748b;font-size:13px">加载中...</div>
    <div v-else-if="comments.length === 0" style="text-align:center;padding:24px;color:#475569;font-size:14px">
      还没有评论，来说两句吧
    </div>
    <div v-else>
      <div v-for="c in comments" :key="c.id" style="margin-bottom:20px">
        <!-- 主评论 -->
        <div style="display:flex;gap:12px">
          <img :src="getAvatar(c.user?.avatar)" style="width:34px;height:34px;border-radius:50%;flex-shrink:0;object-fit:cover;border:1px solid #334155"
               @error="(e) => (e.target as HTMLImageElement).src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 34 34%22%3E%3Ccircle fill=%22%23334155%22 cx=%2217%22 cy=%2217%22 r=%2217%22/%3E%3C/svg%3E'" />
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
              <span style="color:#e2e8f0;font-size:13px;font-weight:600">{{ c.user?.nickname || '匿名' }}</span>
              <span style="color:#475569;font-size:11px">{{ formatTime(c.createdAt) }}</span>
            </div>
            <p style="color:#cbd5e1;font-size:14px;line-height:1.6;margin:4px 0;word-break:break-word">{{ c.content }}</p>
            <div style="display:flex;gap:12px;margin-top:6px">
              <button v-if="isLoggedIn" @click="startReply(c)" style="background:none;border:none;color:#64748b;font-size:12px;cursor:pointer;padding:0">回复</button>
              <button v-if="canDelete(c)" @click="handleDelete(c.id)" style="background:none;border:none;color:#475569;font-size:12px;cursor:pointer;padding:0">删除</button>
            </div>

            <!-- 子回复 -->
            <div v-if="c.replies && c.replies.length" style="margin-top:12px;padding-left:16px;border-left:2px solid #1e293b">
              <div v-for="r in c.replies" :key="r.id" style="display:flex;gap:10px;margin-bottom:12px">
                <img :src="getAvatar(r.user?.avatar)" style="width:28px;height:28px;border-radius:50%;flex-shrink:0;object-fit:cover;border:1px solid #334155"
                     @error="(e) => (e.target as HTMLImageElement).src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 28 28%22%3E%3Ccircle fill=%22%23334155%22 cx=%2214%22 cy=%2214%22 r=%2214%22/%3E%3C/svg%3E'" />
                <div style="flex:1;min-width:0">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px">
                    <span style="color:#e2e8f0;font-size:12px;font-weight:600">{{ r.user?.nickname || '匿名' }}</span>
                    <span style="color:#475569;font-size:10px">{{ formatTime(r.createdAt) }}</span>
                  </div>
                  <p style="color:#cbd5e1;font-size:13px;line-height:1.5;margin:2px 0;word-break:break-word">{{ r.content }}</p>
                  <div style="margin-top:4px">
                    <button v-if="canDelete(r)" @click="handleDelete(r.id)" style="background:none;border:none;color:#475569;font-size:11px;cursor:pointer;padding:0">删除</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="pages > 1" style="display:flex;justify-content:center;gap:8px;margin-top:20px;padding-top:16px;border-top:1px solid #1e293b">
        <button v-for="p in pages" :key="p" @click="loadComments(p)"
                style="width:32px;height:32px;border-radius:6px;border:1px solid #334155;background:transparent;color:#94a3b8;font-size:12px;cursor:pointer"
                :style="p === current ? { background: '#6366f1', borderColor: '#6366f1', color: '#fff' } : {}">
          {{ p }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { isLoggedIn, getUser, getToken, getAvatarUrl } from '../../lib/auth';

interface UserInfo {
  id: number;
  nickname: string;
  avatar: string;
}

interface CommentItem {
  id: number;
  articleId: string;
  content: string;
  parentId: number | null;
  createdAt: string;
  updatedAt: string;
  user: UserInfo | null;
  replies: CommentItem[];
}

const props = defineProps<{ articleId: string }>();

const comments = ref<CommentItem[]>([]);
const total = ref(0);
const current = ref(1);
const pages = ref(0);
const loading = ref(false);

const newComment = ref('');
const submitting = ref(false);
const replyTarget = ref<{ id: number; nickname: string } | null>(null);

const avatarUrl = computed(() => getAvatarUrl(getUser()?.avatar));

function getAvatar(avatar?: string) {
  if (!avatar) return '';
  if (avatar.startsWith('http')) return avatar;
  if (avatar.startsWith('/uploads')) return avatar;
  return `/uploads/avatars/${avatar}`;
}

function formatTime(iso: string) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`;
  return d.toLocaleDateString('zh-CN');
}

function canDelete(c: CommentItem) {
  const me = getUser();
  if (!me) return false;
  return c.user?.id === me.id || (me.user_type ?? me.roleType) === 2;
}

function startReply(c: CommentItem) {
  replyTarget.value = { id: c.id, nickname: c.user?.nickname || '匿名' };
  newComment.value = '';
  // scroll textarea into view
}

function cancelReply() {
  replyTarget.value = null;
  newComment.value = '';
}

async function loadComments(page: number = 1) {
  loading.value = true;
  try {
    const resp = await fetch(`/api/comment/article/${props.articleId}?page=${page}&size=20`);
    const json = await resp.json();
    if (json.code === '200' && json.data) {
      comments.value = json.data.records || [];
      total.value = json.data.total || 0;
      current.value = json.data.current || 1;
      pages.value = json.data.pages || 0;
    }
  } catch { /* ignore */ }
  finally { loading.value = false; }
}

async function submitComment() {
  const content = newComment.value.trim();
  if (!content || submitting.value) return;
  submitting.value = true;
  try {
    const token = getToken();
    const resp = await fetch('/api/comment', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { token } : {}),
      },
      body: JSON.stringify({
        article_id: props.articleId,
        content,
        parent_id: replyTarget.value?.id || null,
      }),
    });
    const json = await resp.json();
    if (json.code === '200') {
      newComment.value = '';
      replyTarget.value = null;
      // 刷新当前页
      await loadComments(current.value);
    } else {
      alert(json.msg || '评论失败');
    }
  } catch {
    alert('网络错误，请稍后重试');
  } finally {
    submitting.value = false;
  }
}

async function handleDelete(commentId: number) {
  if (!confirm('确认删除这条评论？')) return;
  const token = getToken();
  try {
    const resp = await fetch(`/api/comment/${commentId}`, {
      method: 'DELETE',
      headers: { ...(token ? { token } : {}) },
    });
    const json = await resp.json();
    if (json.code === '200') {
      await loadComments(current.value);
    } else {
      alert(json.msg || '删除失败');
    }
  } catch {
    alert('网络错误');
  }
}

onMounted(() => loadComments());

// 文章切换时重新加载
watch(() => props.articleId, () => loadComments());
</script>
