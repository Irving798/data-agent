<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">D</div>
        <div>
          <div class="brand-title">Data Agent</div>
          <div class="brand-subtitle">智能问数助手</div>
        </div>
      </div>

      <section class="panel">
        <div class="panel-label">当前数据集</div>
        <div class="dataset-name">订单分析 Demo</div>
        <div class="dataset-desc">支持按地区、商品、客户、时间维度查询销售额和销量。</div>
      </section>

      <section class="panel">
        <div class="panel-label">示例问题</div>
        <button
          v-for="item in examples"
          :key="item"
          class="example-button"
          type="button"
          @click="askExample(item)"
        >
          {{ item }}
        </button>
      </section>

      <section class="status-panel">
        <div class="status-dot"></div>
        <div>
          <div class="status-title">服务在线</div>
          <div class="status-text">MySQL / ES / Qdrant 已接入</div>
        </div>
      </section>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">Natural Language BI</p>
          <h1>用自然语言查询业务数据</h1>
          <p class="intro">输入问题后，系统会自动召回指标、字段和值，并生成 SQL 返回表格结果。</p>
        </div>
        <div class="metrics">
          <div class="metric">
            <span>2</span>
            <small>核心指标</small>
          </div>
          <div class="metric">
            <span>5</span>
            <small>数据表</small>
          </div>
          <div class="metric">
            <span>3</span>
            <small>检索引擎</small>
          </div>
        </div>
      </header>

      <section ref="messagesEl" class="conversation">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-card">
            <p class="empty-label">开始一次分析</p>
            <h2>问一个和订单、地区、商品或销售额有关的问题</h2>
            <div class="quick-grid">
              <button
                v-for="item in examples"
                :key="item"
                type="button"
                @click="askExample(item)"
              >
                {{ item }}
              </button>
            </div>
          </div>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message-row', msg.role]"
        >
          <div v-if="msg.role === 'assistant'" class="avatar assistant-avatar">AI</div>

          <article class="bubble">
            <div v-if="msg.type === 'text'" class="message-text">
              {{ msg.content }}
            </div>

            <div v-else-if="msg.type === 'steps'" class="steps">
              <div v-if="msg.steps.length === 0" class="step muted">
                <span class="dot running"></span>
                <span>正在理解问题并准备分析...</span>
              </div>
              <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="step">
                <span class="dot" :class="step.status"></span>
                <span>{{ step.text }}</span>
              </div>
            </div>

            <div v-else-if="msg.type === 'table'" class="result-card">
              <div class="result-header">
                <div>
                  <div class="result-title">查询结果</div>
                  <div class="result-meta">{{ msg.rows.length }} 行数据</div>
                </div>
              </div>
              <div class="table-wrap">
                <table class="result-table">
                  <thead>
                    <tr>
                      <th v-for="col in msg.columns" :key="col">
                        {{ col }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, rIdx) in msg.rows" :key="rIdx">
                      <td v-for="col in msg.columns" :key="col">
                        {{ row[col] }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-else-if="msg.type === 'error'" class="error-box">
              <div class="error-title">请求失败</div>
              <div>{{ msg.content }}</div>
            </div>
          </article>

          <div v-if="msg.role === 'user'" class="avatar user-avatar">你</div>
        </div>
      </section>

      <form class="composer" @submit.prevent="sendQuestion">
        <input
          v-model="question"
          :disabled="loading"
          placeholder="例如：各省销售额是多少？"
        />
        <button type="submit" :disabled="loading || !question.trim()">
          {{ loading ? "分析中" : "发送" }}
        </button>
      </form>
    </main>
  </div>
</template>

<script setup>
import { nextTick, ref } from "vue";

const API_URL = "/api/query";

const examples = [
  "各省销售额是多少？",
  "不同商品品类的销量是多少？",
  "各会员等级的订单金额是多少？",
  "华东地区的 GMV 是多少？",
];

const question = ref("");
const loading = ref(false);
const messages = ref([]);
const messagesEl = ref(null);

function scrollToBottom() {
  const el = messagesEl.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

function askExample(text) {
  if (loading.value) return;
  question.value = text;
  sendQuestion();
}

async function sendQuestion() {
  if (!question.value.trim() || loading.value) return;

  const q = question.value.trim();
  question.value = "";
  loading.value = true;

  messages.value.push({ role: "user", type: "text", content: q });

  const stepIndex =
    messages.value.push({
      role: "assistant",
      type: "steps",
      steps: [],
    }) - 1;

  await nextTick();
  scrollToBottom();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q }),
    });

    if (!response.body) throw new Error("服务器未返回流");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const evt of events) {
        const line = evt.trim();
        if (!line.startsWith("data:")) continue;

        let data;
        try {
          data = JSON.parse(line.replace(/^data:\s*/, ""));
        } catch {
          continue;
        }

        const steps = messages.value[stepIndex].steps;

        if (data.type === "progress") {
          let step = steps.find((s) => s.text === data.step);

          if (!step) {
            step = {
              text: data.step,
              status: data.status,
            };
            steps.push(step);
          } else {
            step.status = data.status;
          }
        } else if (data.type === "text") {
          messages.value.splice(stepIndex, 1, {
            role: "assistant",
            type: "text",
            content: data.content || "",
          });
        } else if (data.type === "result" && Array.isArray(data.data)) {
          messages.value.push({
            role: "assistant",
            type: "table",
            columns: Object.keys(data.data[0] || {}),
            rows: data.data,
          });
        } else if (data.type === "error") {
          messages.value.push({
            role: "assistant",
            type: "error",
            content: data.message || "发生错误",
          });
        }

        await nextTick();
        scrollToBottom();
      }
    }
  } catch (e) {
    messages.value.push({
      role: "assistant",
      type: "error",
      content: e?.message || "请求失败",
    });
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
}
</script>

<style scoped>
:global(html),
:global(body) {
  width: 100%;
  height: 100%;
  margin: 0;
}

:global(body) {
  display: block !important;
  min-width: 320px;
  background: #eef3f8;
}

:global(#app) {
  width: 100%;
  height: 100%;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

button,
input {
  font: inherit;
}

.app-shell {
  min-height: 100%;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  background:
    radial-gradient(circle at 8% 12%, rgba(56, 189, 248, 0.16), transparent 26%),
    radial-gradient(circle at 82% 8%, rgba(34, 197, 94, 0.12), transparent 24%),
    #eef3f8;
  color: #172033;
}

.sidebar {
  min-height: 100vh;
  padding: 28px 22px;
  border-right: 1px solid rgba(31, 41, 55, 0.08);
  background: rgba(255, 255, 255, 0.76);
  backdrop-filter: blur(18px);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 2px 10px;
}

.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
  background: linear-gradient(145deg, #0f766e, #2563eb);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.24);
}

.brand-title {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0;
}

.brand-subtitle,
.dataset-desc,
.status-text,
.intro,
.result-meta {
  color: #64748b;
}

.panel,
.status-panel {
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
}

.panel {
  padding: 18px;
}

.panel-label,
.eyebrow,
.empty-label {
  margin: 0 0 10px;
  color: #0f766e;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.dataset-name {
  margin-bottom: 8px;
  font-size: 17px;
  font-weight: 800;
}

.dataset-desc {
  font-size: 14px;
  line-height: 1.7;
}

.example-button,
.quick-grid button {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.32);
  border-radius: 8px;
  background: #fff;
  color: #243044;
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.example-button {
  margin-top: 10px;
  padding: 11px 12px;
  font-size: 14px;
}

.example-button:hover,
.quick-grid button:hover {
  transform: translateY(-1px);
  border-color: rgba(15, 118, 110, 0.5);
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
}

.status-panel {
  margin-top: auto;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.12);
}

.status-title {
  font-weight: 800;
}

.workspace {
  height: 100vh;
  min-width: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
}

.topbar {
  padding: 34px 42px 18px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.topbar h1 {
  margin: 0;
  font-size: clamp(28px, 4vw, 46px);
  line-height: 1.12;
  letter-spacing: 0;
}

.intro {
  max-width: 720px;
  margin: 12px 0 0;
  font-size: 15px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(3, 92px);
  gap: 10px;
}

.metric {
  min-height: 74px;
  padding: 12px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.78);
}

.metric span {
  display: block;
  font-size: 22px;
  font-weight: 850;
}

.metric small {
  color: #64748b;
}

.conversation {
  min-height: 0;
  overflow-y: auto;
  padding: 18px 42px 28px;
}

.empty-state {
  min-height: 100%;
  display: grid;
  place-items: center;
}

.empty-card {
  width: min(760px, 100%);
  padding: 34px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 22px 70px rgba(15, 23, 42, 0.08);
}

.empty-card h2 {
  margin: 0 0 22px;
  font-size: clamp(24px, 3vw, 34px);
  line-height: 1.22;
  letter-spacing: 0;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.quick-grid button {
  min-height: 54px;
  padding: 13px 14px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 18px;
}

.message-row.user {
  justify-content: flex-end;
}

.avatar {
  flex: 0 0 auto;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 800;
}

.assistant-avatar {
  color: #0f766e;
  background: #dff7f2;
}

.user-avatar {
  color: #1d4ed8;
  background: #dbeafe;
}

.bubble {
  max-width: min(860px, 76%);
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 34px rgba(15, 23, 42, 0.06);
}

.message-row.user .bubble {
  border-color: rgba(37, 99, 235, 0.2);
  background: #2563eb;
  color: #fff;
  box-shadow: 0 12px 34px rgba(37, 99, 235, 0.2);
}

.message-text {
  white-space: pre-wrap;
  line-height: 1.7;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.step {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #334155;
  font-size: 14px;
}

.step.muted {
  color: #64748b;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #94a3b8;
}

.dot.running {
  background: #f59e0b;
  box-shadow: 0 0 0 5px rgba(245, 158, 11, 0.12);
}

.dot.success {
  background: #22c55e;
}

.dot.error {
  background: #ef4444;
}

.result-card {
  min-width: min(760px, 100%);
}

.result-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.result-title {
  font-weight: 850;
}

.table-wrap {
  max-width: 100%;
  overflow-x: auto;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
}

.result-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  background: #fff;
}

.result-table th,
.result-table td {
  padding: 10px 14px;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
  font-size: 13px;
  text-align: left;
}

.result-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  color: #475569;
  background: #f8fafc;
  font-weight: 800;
}

.result-table tr:last-child td {
  border-bottom: none;
}

.error-box {
  padding: 12px 14px;
  border: 1px solid rgba(239, 68, 68, 0.22);
  border-radius: 8px;
  color: #991b1b;
  background: #fef2f2;
}

.error-title {
  margin-bottom: 4px;
  font-weight: 850;
}

.composer {
  margin: 0 42px 28px;
  padding: 12px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(18px);
  box-shadow: 0 20px 58px rgba(15, 23, 42, 0.12);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.composer input {
  min-width: 0;
  height: 48px;
  border: none;
  outline: none;
  padding: 0 14px;
  border-radius: 8px;
  color: #172033;
  background: #f8fafc;
}

.composer input:disabled {
  color: #94a3b8;
}

.composer button {
  min-width: 96px;
  height: 48px;
  border: none;
  border-radius: 8px;
  color: #fff;
  font-weight: 800;
  background: linear-gradient(135deg, #0f766e, #2563eb);
  cursor: pointer;
}

.composer button:disabled {
  cursor: not-allowed;
  opacity: 0.56;
}

@media (max-width: 980px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    min-height: auto;
    padding: 20px;
  }

  .status-panel {
    margin-top: 0;
  }

  .workspace {
    height: auto;
    min-height: 100vh;
  }

  .topbar {
    align-items: stretch;
    flex-direction: column;
    padding: 24px 20px 12px;
  }

  .metrics {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .conversation {
    padding: 12px 20px 24px;
  }

  .composer {
    margin: 0 20px 20px;
  }
}

@media (max-width: 640px) {
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .metrics {
    grid-template-columns: 1fr;
  }

  .bubble {
    max-width: calc(100% - 50px);
  }

  .composer {
    grid-template-columns: 1fr;
  }

  .composer button {
    width: 100%;
  }
}
</style>


