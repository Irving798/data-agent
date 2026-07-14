<template>
  <!-- 页面分为可折叠侧边栏与主工作区，移动端通过遮罩层控制导航。 -->
  <div class="app-shell" :class="{ 'sidebar-open': sidebarOpen }">
    <button
      class="sidebar-scrim"
      type="button"
      aria-label="关闭侧边栏"
      @click="sidebarOpen = false"
    ></button>

    <aside class="sidebar">
      <div class="sidebar-head">
        <div class="brand-mark" aria-hidden="true">D</div>
        <div class="brand-copy">
          <strong>Data Agent</strong>
          <span>智能问数工作台</span>
        </div>
        <button
          class="icon-button sidebar-close"
          type="button"
          title="关闭侧边栏"
          aria-label="关闭侧边栏"
          @click="sidebarOpen = false"
        >
          ×
        </button>
      </div>

      <section class="dataset-block" aria-labelledby="dataset-title">
        <div class="section-caption">当前数据集</div>
        <div class="dataset-title-row">
          <span class="database-symbol" aria-hidden="true"></span>
          <div>
            <h2 id="dataset-title">订单分析 Demo</h2>
            <p>电商订单主题数据</p>
          </div>
        </div>
        <div class="dataset-tags" aria-label="可分析维度">
          <span>地区</span>
          <span>商品</span>
          <span>客户</span>
          <span>时间</span>
        </div>
      </section>

      <nav class="prompt-nav" aria-label="快捷问题">
        <div class="section-caption">快捷问题</div>
        <button
          v-for="(item, index) in examples"
          :key="item.query"
          class="prompt-link"
          type="button"
          :disabled="loading"
          @click="askExample(item.query)"
        >
          <span class="prompt-index">0{{ index + 1 }}</span>
          <span>{{ item.short }}</span>
          <span class="prompt-arrow" aria-hidden="true">›</span>
        </button>
      </nav>

      <div class="sidebar-status">
        <div class="status-line">
          <span class="status-dot" :class="healthState.status" aria-hidden="true"></span>
          <strong>{{ healthTitle }}</strong>
          <button
            class="health-refresh"
            type="button"
            :disabled="healthLoading"
            title="刷新服务状态"
            aria-label="刷新服务状态"
            @click="fetchHealth"
          >
            ↻
          </button>
        </div>
        <div class="service-status-list">
          <span v-for="service in serviceStatuses" :key="service.key">
            <i :class="service.status" aria-hidden="true"></i>
            {{ service.label }}
          </span>
        </div>
      </div>
    </aside>

    <main class="workspace">
      <header class="workspace-header">
        <div class="header-title-group">
          <button
            class="icon-button menu-button"
            type="button"
            title="打开侧边栏"
            aria-label="打开侧边栏"
            @click="sidebarOpen = true"
          >
            ☰
          </button>
          <div>
            <span class="breadcrumb">订单分析 Demo / 自然语言查询</span>
            <h1>问数分析</h1>
          </div>
        </div>

        <div class="header-actions">
          <span class="connection-state">
            <span class="status-dot" :class="healthState.status" aria-hidden="true"></span>
            {{ connectionLabel }}
          </span>
          <button
            class="new-session-button"
            type="button"
            :disabled="messages.length === 0 || loading"
            @click="clearConversation"
          >
            <span aria-hidden="true">＋</span>
            新会话
          </button>
        </div>
      </header>

      <section ref="messagesEl" class="conversation" aria-live="polite">
        <div class="conversation-inner">
          <div v-if="messages.length === 0" class="empty-state">
            <div class="welcome-copy">
              <p class="eyebrow">ASK YOUR DATA</p>
              <h2>从一个业务问题开始</h2>
              <p>
                描述你想了解的指标和维度，Data Agent 会完成元数据召回、SQL
                生成和结果查询。
              </p>
            </div>

            <div class="data-flow" aria-label="问数处理流程">
              <div class="flow-step">
                <span>01</span>
                <strong>自然语言</strong>
              </div>
              <i aria-hidden="true">→</i>
              <div class="flow-step">
                <span>02</span>
                <strong>语义召回</strong>
              </div>
              <i aria-hidden="true">→</i>
              <div class="flow-step">
                <span>03</span>
                <strong>生成 SQL</strong>
              </div>
              <i aria-hidden="true">→</i>
              <div class="flow-step">
                <span>04</span>
                <strong>返回结果</strong>
              </div>
            </div>

            <section class="starter-section" aria-labelledby="starter-title">
              <div class="starter-heading">
                <h3 id="starter-title">试试这样问</h3>
                <span>基于当前订单数据集</span>
              </div>
              <div class="starter-grid">
                <button
                  v-for="item in examples"
                  :key="item.query"
                  type="button"
                  :disabled="loading"
                  @click="askExample(item.query)"
                >
                  <span class="starter-meta">{{ item.meta }}</span>
                  <strong>{{ item.query }}</strong>
                  <span class="starter-action">使用此问题 <b aria-hidden="true">→</b></span>
                </button>
              </div>
            </section>
          </div>

          <div v-else class="message-list">
            <article
              v-for="msg in messages"
              :key="msg.id"
              :class="['message', `message-${msg.role}`]"
            >
              <div class="message-avatar" aria-hidden="true">
                {{ msg.role === "assistant" ? "D" : "你" }}
              </div>

              <div class="message-body">
                <div class="message-label">
                  {{ msg.role === "assistant" ? "Data Agent" : "你" }}
                </div>

                <div v-if="msg.type === 'text'" class="message-text">
                  {{ msg.content }}
                </div>

                <details v-else-if="msg.type === 'steps'" class="analysis-trace" open>
                  <summary>
                    <span class="trace-summary-left">
                      <span class="trace-pulse" :class="{ active: msg.active }"></span>
                      <strong>{{ msg.active ? "正在分析" : "分析过程" }}</strong>
                    </span>
                    <span>{{ completedSteps(msg.steps) }}/{{ msg.steps.length || 1 }} 完成</span>
                  </summary>
                  <div class="trace-list">
                    <div v-if="msg.steps.length === 0" class="trace-item">
                      <span class="trace-state running"></span>
                      <span>正在理解问题并准备分析</span>
                    </div>
                    <div
                      v-for="(step, index) in msg.steps"
                      :key="step.text"
                      class="trace-item"
                    >
                      <span class="trace-order">{{ String(index + 1).padStart(2, "0") }}</span>
                      <span class="trace-state" :class="step.status"></span>
                      <span>{{ step.text }}</span>
                      <span class="trace-status">{{ stepStatusLabel(step.status) }}</span>
                    </div>
                  </div>
                </details>

                <section v-else-if="msg.type === 'table'" class="result-panel">
                  <header class="result-header">
                    <div>
                      <span class="result-kicker">QUERY RESULT</span>
                      <h3>查询结果</h3>
                    </div>
                    <span class="row-count">
                      {{ msg.rows.length }} 行{{ msg.truncated ? "（已截断）" : "" }}
                    </span>
                  </header>

                  <p v-if="msg.truncated" class="result-limit-notice">
                    结果超过单次查询限制，仅展示前 {{ msg.rows.length }} 行。请增加筛选条件后重新查询。
                  </p>

                  <div v-if="msg.rows.length" class="table-wrap">
                    <table class="result-table">
                      <thead>
                        <tr>
                          <th v-for="col in msg.columns" :key="col">{{ col }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, rowIndex) in msg.rows" :key="rowIndex">
                          <td v-for="col in msg.columns" :key="col">{{ row[col] }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div v-else class="empty-result">查询成功，但没有匹配到数据。</div>
                </section>

                <div v-else-if="msg.type === 'error'" class="error-box" role="alert">
                  <strong>请求失败</strong>
                  <span>{{ msg.content }}</span>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>

      <footer class="composer-area">
        <form class="composer" @submit.prevent="sendQuestion">
          <textarea
            ref="textareaEl"
            v-model="question"
            rows="1"
            :disabled="loading"
            placeholder="输入一个业务问题，例如：各省销售额是多少？"
            aria-label="输入业务问题"
            @input="resizeTextarea"
            @keydown.enter.exact.prevent="sendQuestion"
          ></textarea>
          <div class="composer-actions">
            <span>{{ loading ? "正在处理当前问题…" : "Enter 发送 · Shift + Enter 换行" }}</span>
            <button
              class="send-button"
              type="submit"
              :disabled="loading || !question.trim()"
              title="发送问题"
              aria-label="发送问题"
            >
              <span v-if="loading" class="button-loader" aria-hidden="true"></span>
              <span v-else aria-hidden="true">↑</span>
            </button>
          </div>
        </form>
        <p>回答基于当前演示数据集生成，请结合实际业务口径核验。</p>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";

// 接口地址保持相对路径，由开发代理或生产环境 Nginx 统一转发。
const API_URL = "/api/query";
const HEALTH_URL = "/api/health";
const HEALTH_REFRESH_INTERVAL = 30_000;

// 示例问题同时服务于侧边栏快捷入口和空状态引导卡片。
const examples = [
  {
    short: "各省销售额",
    meta: "地区 × 销售额",
    query: "各省销售额是多少？",
  },
  {
    short: "品类销量",
    meta: "商品 × 销量",
    query: "不同商品品类的销量是多少？",
  },
  {
    short: "会员订单金额",
    meta: "客户 × 订单金额",
    query: "各会员等级的订单金额是多少？",
  },
  {
    short: "华东地区 GMV",
    meta: "地区 × GMV",
    query: "华东地区的 GMV 是多少？",
  },
];

const question = ref("");
const loading = ref(false);
const messages = ref([]);
const messagesEl = ref(null);
const textareaEl = ref(null);
const sidebarOpen = ref(false);
const healthLoading = ref(false);
const healthState = ref({ status: "checking", services: {} });
let nextMessageId = 1;
let healthTimer;

// 前端只展示直接影响问数链路的核心依赖，后端负责汇总详细状态。
const serviceDefinitions = [
  { key: "mysql", label: "MySQL" },
  { key: "elasticsearch", label: "Elasticsearch" },
  { key: "qdrant", label: "Qdrant" },
];

const healthTitle = computed(() => ({
  checking: "正在检查数据服务",
  healthy: "数据服务正常",
  degraded: "部分数据服务异常",
  unavailable: "无法获取服务状态",
}[healthState.value.status]));

const connectionLabel = computed(() => ({
  checking: "检查中",
  healthy: "已连接",
  degraded: "连接异常",
  unavailable: "后端不可达",
}[healthState.value.status]));

const serviceStatuses = computed(() => serviceDefinitions.map((service) => ({
  ...service,
  status: healthState.value.services?.[service.key]?.status || "unknown",
})));

async function fetchHealth() {
  if (healthLoading.value) return;
  healthLoading.value = true;
  try {
    const response = await fetch(HEALTH_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`健康检查返回 ${response.status}`);
    const data = await response.json();
    healthState.value = {
      status: data.status,
      services: data.services || {},
    };
  } catch {
    healthState.value = { status: "unavailable", services: {} };
  } finally {
    healthLoading.value = false;
  }
}

onMounted(() => {
  fetchHealth();
  healthTimer = window.setInterval(fetchHealth, HEALTH_REFRESH_INTERVAL);
});

onUnmounted(() => {
  if (healthTimer) window.clearInterval(healthTimer);
});

function createMessage(message) {
  return { id: nextMessageId++, ...message };
}

function scrollToBottom() {
  const el = messagesEl.value;
  if (el) el.scrollTop = el.scrollHeight;
}

function resizeTextarea() {
  const el = textareaEl.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 132)}px`;
}

function clearConversation() {
  if (loading.value) return;
  messages.value = [];
  question.value = "";
  nextTick(() => {
    resizeTextarea();
    textareaEl.value?.focus();
  });
}

function askExample(text) {
  if (loading.value) return;
  question.value = text;
  sidebarOpen.value = false;
  sendQuestion();
}

function completedSteps(steps) {
  return steps.filter((step) => step.status === "success").length;
}

function stepStatusLabel(status) {
  return {
    running: "进行中",
    success: "完成",
    error: "失败",
  }[status] || "等待";
}

async function processEvent(rawEvent, stepMessageId) {
  // 后端按 SSE 约定发送 data 行；无法解析的心跳或残缺事件直接忽略。
  const line = rawEvent.trim();
  if (!line.startsWith("data:")) return;

  let data;
  try {
    data = JSON.parse(line.replace(/^data:\s*/, ""));
  } catch {
    return;
  }

  const stepMessage = messages.value.find((message) => message.id === stepMessageId);

  if (data.type === "progress" && stepMessage?.type === "steps") {
    let step = stepMessage.steps.find((item) => item.text === data.step);
    if (!step) {
      step = { text: data.step, status: data.status };
      stepMessage.steps.push(step);
    } else {
      step.status = data.status;
    }
  } else if (data.type === "text") {
    const index = messages.value.findIndex((message) => message.id === stepMessageId);
    if (index !== -1) {
      messages.value.splice(
        index,
        1,
        createMessage({ role: "assistant", type: "text", content: data.content || "" }),
      );
    }
  } else if (data.type === "result" && Array.isArray(data.data)) {
    messages.value.push(
      createMessage({
        role: "assistant",
        type: "table",
        columns: Object.keys(data.data[0] || {}),
        rows: data.data,
        truncated: Boolean(data.truncated),
      }),
    );
  } else if (data.type === "error") {
    messages.value.push(
      createMessage({
        role: "assistant",
        type: "error",
        content: data.message || "发生错误",
      }),
    );
  }

  await nextTick();
  scrollToBottom();
}

async function sendQuestion() {
  if (!question.value.trim() || loading.value) return;

  const query = question.value.trim();
  question.value = "";
  loading.value = true;
  messages.value.push(createMessage({ role: "user", type: "text", content: query }));

  const stepMessage = createMessage({
    role: "assistant",
    type: "steps",
    steps: [],
    active: true,
  });
  messages.value.push(stepMessage);

  await nextTick();
  resizeTextarea();
  scrollToBottom();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) throw new Error(`服务器返回 ${response.status}`);
    if (!response.body) throw new Error("服务器未返回流式响应");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    // 网络分片不保证事件边界，因此先累计缓冲区，再按空行拆分完整事件。
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split(/\r?\n\r?\n/);
      buffer = events.pop() || "";

      for (const event of events) {
        await processEvent(event, stepMessage.id);
      }
    }

    buffer += decoder.decode();
    if (buffer.trim()) await processEvent(buffer, stepMessage.id);
  } catch (error) {
    const currentStepIndex = messages.value.findIndex(
      (message) => message.id === stepMessage.id,
    );
    const errorMessage = createMessage({
      role: "assistant",
      type: "error",
      content: error?.message || "请求失败",
    });

    if (currentStepIndex !== -1 && stepMessage.steps.length === 0) {
      messages.value.splice(currentStepIndex, 1, errorMessage);
    } else {
      messages.value.push(errorMessage);
    }
  } finally {
    const currentStepMessage = messages.value.find(
      (message) => message.id === stepMessage.id && message.type === "steps",
    );
    if (currentStepMessage) currentStepMessage.active = false;
    loading.value = false;
    await nextTick();
    scrollToBottom();
    textareaEl.value?.focus();
  }
}
</script>

<style scoped>
/* 全局尺寸由根容器接管，组件内部再组织侧边栏、内容区和响应式布局。 */
:global(html),
:global(body),
:global(#app) {
  width: 100%;
  height: 100%;
  margin: 0;
}

:global(body) {
  min-width: 320px;
  background: #f4f6f8;
}

button,
textarea {
  font: inherit;
}

button:focus-visible,
textarea:focus-visible,
summary:focus-visible {
  outline: 3px solid rgba(37, 99, 235, 0.2);
  outline-offset: 2px;
}

.app-shell {
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: 264px minmax(0, 1fr);
  overflow: hidden;
  color: #18212f;
  background: #f4f6f8;
}

.sidebar {
  min-width: 0;
  height: 100%;
  padding: 22px 18px 18px;
  border-right: 1px solid #dfe4ea;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 22px;
  z-index: 20;
}

.sidebar-head {
  min-height: 44px;
  display: flex;
  align-items: center;
  gap: 11px;
}

.brand-mark,
.message-avatar {
  display: grid;
  place-items: center;
  font-weight: 800;
}

.brand-mark {
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  border-radius: 8px;
  color: #ffffff;
  background: #137f75;
  box-shadow: 0 7px 18px rgba(19, 127, 117, 0.22);
}

.brand-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.brand-copy strong {
  font-size: 16px;
}

.brand-copy span {
  margin-top: 2px;
  color: #718096;
  font-size: 12px;
}

.icon-button {
  width: 36px;
  height: 36px;
  border: 1px solid #dfe4ea;
  border-radius: 7px;
  color: #394457;
  background: #ffffff;
  cursor: pointer;
}

.sidebar-close,
.menu-button,
.sidebar-scrim {
  display: none;
}

.section-caption {
  margin-bottom: 10px;
  color: #7a8699;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0;
}

.dataset-block {
  padding: 15px;
  border: 1px solid #e2e7ec;
  border-radius: 8px;
  background: #f7f9fa;
}

.dataset-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.database-symbol {
  position: relative;
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  border: 2px solid #137f75;
  border-radius: 50% / 28%;
}

.database-symbol::after {
  content: "";
  position: absolute;
  left: -2px;
  right: -2px;
  top: 7px;
  height: 6px;
  border-top: 2px solid #137f75;
  border-bottom: 2px solid #137f75;
  border-radius: 50%;
}

.dataset-block h2 {
  margin: 0;
  font-size: 15px;
}

.dataset-block p {
  margin: 3px 0 0;
  color: #718096;
  font-size: 12px;
}

.dataset-tags {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.dataset-tags span {
  padding: 4px 7px;
  border: 1px solid #dbe2e8;
  border-radius: 5px;
  color: #566174;
  background: #ffffff;
  font-size: 11px;
}

.prompt-nav {
  min-height: 0;
}

.prompt-link {
  width: 100%;
  min-height: 42px;
  padding: 8px 6px;
  border: 0;
  border-bottom: 1px solid #edf0f3;
  color: #384456;
  background: transparent;
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 7px;
  text-align: left;
  cursor: pointer;
}

.prompt-link:hover:not(:disabled) {
  color: #0f6f67;
  background: #f1f7f6;
}

.prompt-link:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.prompt-index {
  color: #98a3b3;
  font-size: 10px;
  font-variant-numeric: tabular-nums;
}

.prompt-arrow {
  color: #98a3b3;
  font-size: 20px;
  text-align: right;
}

.sidebar-status {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #e5e9ed;
}

.status-line {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 50%;
  background: #9aa4b2;
  box-shadow: 0 0 0 4px rgba(154, 164, 178, 0.12);
}

.status-dot.healthy,
.service-status-list i.healthy {
  background: #20a66a;
}

.status-dot.healthy {
  box-shadow: 0 0 0 4px rgba(32, 166, 106, 0.12);
}

.status-dot.degraded,
.service-status-list i.unhealthy {
  background: #d99716;
}

.status-dot.degraded {
  box-shadow: 0 0 0 4px rgba(217, 151, 22, 0.12);
}

.status-dot.unavailable {
  background: #cf4b4b;
  box-shadow: 0 0 0 4px rgba(207, 75, 75, 0.12);
}

.status-dot.checking {
  animation: pulse 1.2s ease-in-out infinite;
}

.health-refresh {
  width: 24px;
  height: 24px;
  margin-left: auto;
  border: 0;
  border-radius: 5px;
  color: #718096;
  background: transparent;
  cursor: pointer;
}

.health-refresh:hover:not(:disabled) {
  color: #137f75;
  background: #edf5f4;
}

.health-refresh:disabled {
  cursor: wait;
  opacity: 0.45;
}

.service-status-list {
  margin: 8px 0 0 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  color: #7a8699;
  font-size: 11px;
}

.service-status-list span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.service-status-list i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a7b0bc;
}

.workspace {
  min-width: 0;
  height: 100%;
  display: grid;
  grid-template-rows: 68px minmax(0, 1fr) auto;
  overflow: hidden;
}

.workspace-header {
  padding: 0 28px;
  border-bottom: 1px solid #dfe4ea;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.header-title-group,
.header-actions {
  display: flex;
  align-items: center;
}

.header-title-group {
  min-width: 0;
  gap: 10px;
}

.breadcrumb {
  display: block;
  margin-bottom: 2px;
  color: #7a8699;
  font-size: 10px;
}

.workspace-header h1 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
  letter-spacing: 0;
}

.header-actions {
  gap: 12px;
}

.connection-state {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #637083;
  font-size: 12px;
}

.new-session-button {
  min-height: 36px;
  padding: 0 12px;
  border: 1px solid #d6dce3;
  border-radius: 7px;
  color: #354052;
  background: #ffffff;
  font-weight: 650;
  cursor: pointer;
}

.new-session-button:hover:not(:disabled) {
  border-color: #9ca8b7;
  background: #f7f9fa;
}

.new-session-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.conversation {
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.conversation-inner {
  width: min(100%, 980px);
  min-height: 100%;
  margin: 0 auto;
  padding: 34px 28px 48px;
}

.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.welcome-copy {
  max-width: 620px;
}

.eyebrow,
.result-kicker,
.starter-meta {
  color: #137f75;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
}

.welcome-copy .eyebrow {
  margin: 0 0 10px;
}

.welcome-copy h2 {
  margin: 0;
  font-size: 30px;
  line-height: 1.25;
  letter-spacing: 0;
}

.welcome-copy > p:last-child {
  margin: 12px 0 0;
  color: #667386;
  font-size: 14px;
  line-height: 1.75;
}

.data-flow {
  margin: 28px 0 32px;
  padding: 16px 0;
  border-top: 1px solid #dfe4ea;
  border-bottom: 1px solid #dfe4ea;
  display: grid;
  grid-template-columns: repeat(7, auto);
  align-items: center;
  justify-content: start;
  gap: 18px;
}

.flow-step {
  display: flex;
  align-items: center;
  gap: 8px;
}

.flow-step span {
  width: 27px;
  height: 27px;
  border: 1px solid #cfd6de;
  border-radius: 6px;
  display: grid;
  place-items: center;
  color: #687589;
  background: #ffffff;
  font-size: 9px;
  font-weight: 800;
}

.flow-step strong {
  font-size: 12px;
  white-space: nowrap;
}

.data-flow i {
  color: #a6afbb;
  font-style: normal;
}

.starter-heading {
  margin-bottom: 13px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 20px;
}

.starter-heading h3 {
  margin: 0;
  font-size: 15px;
}

.starter-heading span {
  color: #8490a0;
  font-size: 11px;
}

.starter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.starter-grid button {
  min-height: 112px;
  padding: 15px;
  border: 1px solid #dfe4ea;
  border-radius: 8px;
  color: #1e2938;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  cursor: pointer;
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.starter-grid button:hover:not(:disabled) {
  transform: translateY(-2px);
  border-color: #8fb8b3;
  box-shadow: 0 10px 24px rgba(30, 41, 56, 0.08);
}

.starter-grid button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.starter-grid strong {
  margin-top: 7px;
  font-size: 14px;
  line-height: 1.5;
}

.starter-action {
  margin-top: auto;
  color: #758195;
  font-size: 10px;
}

.starter-action b {
  margin-left: 4px;
  color: #137f75;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.message {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
  align-items: flex-start;
}

.message-user {
  width: min(100%, 720px);
  margin-left: auto;
  grid-template-columns: minmax(0, 1fr) 34px;
}

.message-user .message-avatar {
  grid-column: 2;
  grid-row: 1;
  color: #ffffff;
  background: #3157a5;
}

.message-user .message-body {
  grid-column: 1;
  grid-row: 1;
  align-items: flex-end;
}

.message-avatar {
  width: 34px;
  height: 34px;
  border-radius: 7px;
  color: #0f6f67;
  background: #dcefeb;
  font-size: 11px;
}

.message-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.message-label {
  margin: 0 0 7px;
  color: #7a8699;
  font-size: 10px;
  font-weight: 700;
}

.message-text {
  max-width: 760px;
  color: #273244;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
}

.message-user .message-text {
  padding: 11px 14px;
  border-radius: 8px 2px 8px 8px;
  color: #ffffff;
  background: #3157a5;
  box-shadow: 0 8px 22px rgba(49, 87, 165, 0.16);
}

.analysis-trace,
.result-panel,
.error-box {
  width: 100%;
  border: 1px solid #dfe4ea;
  border-radius: 8px;
  background: #ffffff;
}

.analysis-trace summary {
  min-height: 49px;
  padding: 0 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  color: #657286;
  font-size: 11px;
  cursor: pointer;
  list-style: none;
}

.analysis-trace summary::-webkit-details-marker {
  display: none;
}

.trace-summary-left {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #283446;
  font-size: 13px;
}

.trace-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #20a66a;
}

.trace-pulse.active {
  background: #d99716;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(217, 151, 22, 0.16);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(217, 151, 22, 0.16);
  }
}

.trace-list {
  padding: 4px 15px 12px;
  border-top: 1px solid #edf0f3;
}

.trace-item {
  min-height: 34px;
  display: grid;
  grid-template-columns: 22px 9px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  color: #485568;
  font-size: 12px;
}

.trace-order,
.trace-status {
  color: #94a0af;
  font-size: 9px;
}

.trace-state {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a7b0bc;
}

.trace-state.running {
  background: #d99716;
}

.trace-state.success {
  background: #20a66a;
}

.trace-state.error {
  background: #cf4b4b;
}

.result-panel {
  overflow: hidden;
}

.result-header {
  min-height: 65px;
  padding: 13px 16px;
  border-bottom: 1px solid #e6eaee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.result-kicker {
  display: block;
  margin-bottom: 4px;
}

.result-header h3 {
  margin: 0;
  font-size: 15px;
}

.row-count {
  padding: 5px 8px;
  border-radius: 5px;
  color: #566174;
  background: #edf1f4;
  font-size: 10px;
  font-weight: 700;
}

.result-limit-notice {
  margin: 0;
  padding: 10px 14px;
  border-bottom: 1px solid #e2e7ec;
  color: #8a5a12;
  background: #fff8e8;
  font-size: 13px;
}

.table-wrap {
  max-width: 100%;
  overflow-x: auto;
}

.result-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  background: #ffffff;
}

.result-table th,
.result-table td {
  padding: 11px 15px;
  border-bottom: 1px solid #edf0f3;
  color: #344054;
  font-size: 12px;
  text-align: left;
  white-space: nowrap;
}

.result-table th {
  color: #687589;
  background: #f7f9fa;
  font-size: 10px;
  font-weight: 800;
}

.result-table tbody tr:hover {
  background: #f7fbfa;
}

.result-table tbody tr:last-child td {
  border-bottom: 0;
}

.empty-result {
  padding: 28px 16px;
  color: #7a8699;
  font-size: 12px;
  text-align: center;
}

.error-box {
  padding: 14px 15px;
  border-color: #eccaca;
  color: #8f3535;
  background: #fff7f7;
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 12px;
}

.composer-area {
  padding: 12px 28px 14px;
  border-top: 1px solid #dfe4ea;
  background: #ffffff;
}

.composer {
  width: min(100%, 924px);
  margin: 0 auto;
  padding: 10px 11px 8px 14px;
  border: 1px solid #cfd6de;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(30, 41, 56, 0.08);
}

.composer:focus-within {
  border-color: #6f9f99;
  box-shadow: 0 0 0 3px rgba(19, 127, 117, 0.09), 0 8px 24px rgba(30, 41, 56, 0.08);
}

.composer textarea {
  width: 100%;
  min-height: 27px;
  max-height: 132px;
  padding: 3px 0;
  border: 0;
  outline: 0;
  resize: none;
  overflow-y: auto;
  color: #1f2938;
  background: transparent;
  font-size: 14px;
  line-height: 1.5;
}

.composer textarea::placeholder {
  color: #9aa4b2;
}

.composer-actions {
  min-height: 36px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.composer-actions > span {
  padding-bottom: 5px;
  color: #98a3b3;
  font-size: 9px;
}

.send-button {
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  border: 0;
  border-radius: 7px;
  color: #ffffff;
  background: #137f75;
  display: grid;
  place-items: center;
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
}

.send-button:hover:not(:disabled) {
  background: #0f6f67;
}

.send-button:disabled {
  color: #aeb7c2;
  background: #e8ecef;
  cursor: not-allowed;
}

.button-loader {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.composer-area > p {
  margin: 7px auto 0;
  color: #9aa4b2;
  font-size: 9px;
  text-align: center;
}

@media (max-width: 900px) {
  .app-shell {
    grid-template-columns: minmax(0, 1fr);
  }

  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: min(290px, 86vw);
    transform: translateX(-102%);
    transition: transform 180ms ease;
  }

  .sidebar-open .sidebar {
    transform: translateX(0);
  }

  .sidebar-scrim {
    position: fixed;
    inset: 0;
    width: 100%;
    height: 100%;
    border: 0;
    background: rgba(24, 33, 47, 0.4);
    z-index: 15;
  }

  .sidebar-open .sidebar-scrim,
  .menu-button,
  .sidebar-close {
    display: block;
  }

  .sidebar-close {
    margin-left: auto;
  }

  .workspace-header {
    padding: 0 18px;
  }

  .conversation-inner {
    padding: 28px 20px 40px;
  }

  .composer-area {
    padding: 11px 18px 12px;
  }
}

@media (max-width: 640px) {
  .workspace {
    grid-template-rows: 62px minmax(0, 1fr) auto;
  }

  .workspace-header {
    padding: 0 12px;
  }

  .breadcrumb,
  .connection-state,
  .new-session-button span:first-child {
    display: none;
  }

  .workspace-header h1 {
    font-size: 16px;
  }

  .new-session-button {
    padding: 0 9px;
    font-size: 11px;
  }

  .conversation-inner {
    padding: 24px 14px 34px;
  }

  .welcome-copy h2 {
    font-size: 25px;
  }

  .data-flow {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 7px;
  }

  .data-flow i {
    display: none;
  }

  .flow-step {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .flow-step strong {
    font-size: 10px;
  }

  .starter-heading span {
    display: none;
  }

  .starter-grid {
    grid-template-columns: 1fr;
  }

  .starter-grid button {
    min-height: 96px;
  }

  .message-list {
    gap: 24px;
  }

  .message,
  .message-user {
    width: 100%;
    grid-template-columns: 28px minmax(0, 1fr);
    gap: 9px;
  }

  .message-user {
    grid-template-columns: minmax(0, 1fr) 28px;
  }

  .message-avatar {
    width: 28px;
    height: 28px;
    font-size: 9px;
  }

  .analysis-trace summary {
    padding: 0 11px;
  }

  .trace-list {
    padding: 4px 11px 11px;
  }

  .trace-item {
    grid-template-columns: 9px minmax(0, 1fr) auto;
  }

  .trace-order {
    display: none;
  }

  .composer-area {
    padding: 9px 10px 10px;
  }

  .composer-actions > span {
    max-width: 210px;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
