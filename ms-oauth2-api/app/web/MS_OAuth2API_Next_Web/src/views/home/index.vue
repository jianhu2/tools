<template>
  <main class="guide-page">
    <section class="intro-band">
      <div class="intro-copy">
        <p class="eyebrow">MS.OAUTH2API</p>
        <h1>Outlook OAuth2 邮件取件服务</h1>
        <p class="summary">
          当前实例部署在 <strong>ms.eto.ccwu.cc</strong>，用于导入 Outlook 长效邮箱，通过 Graph API 或 IMAP OAuth2 获取收件箱、垃圾箱邮件。
        </p>
      </div>
      <div class="intro-actions">
        <router-link to="/email" class="primary-link">进入邮箱管理</router-link>
        <a href="https://github.com/HChaoHui/MS_OAuth2API_Next" target="_blank" rel="noreferrer" class="secondary-link">
          项目仓库
        </a>
      </div>
    </section>

    <section class="status-grid">
      <article class="status-item">
        <span class="status-label">入口</span>
        <strong>https://ms.eto.ccwu.cc/</strong>
        <p>默认进入邮箱工作台，说明页保留在 <code>/home</code>。</p>
      </article>
      <article class="status-item">
        <span class="status-label">容器</span>
        <strong>ms-oauth2api</strong>
        <p>Docker Compose 部署，nginx 代理到 <code>127.0.0.1:3000</code>。</p>
      </article>
      <article class="status-item">
        <span class="status-label">协议</span>
        <strong>Graph -> IMAP</strong>
        <p>优先 Graph，Graph scope 不可用时自动回退 IMAP OAuth2。</p>
      </article>
    </section>

    <section class="content-grid">
      <article class="info-panel wide">
        <div class="section-head">
          <span class="marker">01</span>
          <div>
            <h2>使用流程</h2>
            <p>导入账号后，点击左侧邮箱即可直接取件并预览正文。</p>
          </div>
        </div>
        <div class="steps">
          <div class="step">
            <span>1</span>
            <strong>导入邮箱</strong>
            <p>支持粘贴导入和 txt/csv 文件导入。</p>
          </div>
          <div class="step">
            <span>2</span>
            <strong>选择邮箱</strong>
            <p>左侧点击邮箱，右侧自动加载收件箱。</p>
          </div>
          <div class="step">
            <span>3</span>
            <strong>查看邮件</strong>
            <p>中间选择邮件，最右侧显示正文预览。</p>
          </div>
        </div>
      </article>

      <article class="info-panel">
        <div class="section-head">
          <span class="marker">02</span>
          <div>
            <h2>导入格式</h2>
            <p>默认分隔符为四个短横线。</p>
          </div>
        </div>
        <pre class="code-block">邮箱----密码----client_id----refresh_token</pre>
        <p class="note">refresh_token 会保留分隔符后的完整剩余内容，避免 UUID 或 token 内部字符被误拆。</p>
      </article>

      <article class="info-panel">
        <div class="section-head">
          <span class="marker">03</span>
          <div>
            <h2>协议行为</h2>
            <p>当前版本适配 Graph 和 IMAP 两类授权。</p>
          </div>
        </div>
        <div class="protocol-list">
          <div>
            <strong>Graph API</strong>
            <code>https://graph.microsoft.com/Mail.Read offline_access</code>
          </div>
          <div>
            <strong>IMAP OAuth2</strong>
            <code>https://outlook.office.com/IMAP.AccessAsUser.All offline_access</code>
          </div>
        </div>
      </article>

      <article class="info-panel wide">
        <div class="section-head">
          <span class="marker">04</span>
          <div>
            <h2>API</h2>
            <p>前端工作台调用以下接口完成取件、清空和代理测试。</p>
          </div>
        </div>
        <div class="api-table">
          <div class="api-row">
            <span>GET / POST</span>
            <strong>/api/mail_all</strong>
            <p>获取当前文件夹全部邮件。</p>
          </div>
          <div class="api-row">
            <span>GET / POST</span>
            <strong>/api/mail_new</strong>
            <p>获取最新一封邮件。</p>
          </div>
          <div class="api-row">
            <span>GET / POST</span>
            <strong>/api/process-mailbox</strong>
            <p>清空收件箱或垃圾箱。</p>
          </div>
          <div class="api-row">
            <span>GET / POST</span>
            <strong>/api/test-proxy</strong>
            <p>测试 socks5/http 代理出口。</p>
          </div>
        </div>
      </article>

      <article class="info-panel">
        <div class="section-head">
          <span class="marker">05</span>
          <div>
            <h2>失败判断</h2>
            <p>常见问题可先按日志关键字判断。</p>
          </div>
        </div>
        <ul class="issue-list">
          <li><strong>invalid_grant</strong><span>refresh token 过期、租户不匹配或 scope 未授权。</span></li>
          <li><strong>falling back to IMAP</strong><span>Graph 不可用，服务已自动尝试 IMAP。</span></li>
          <li><strong>IMAP 认证失败</strong><span>检查 token 是否具备 IMAP.AccessAsUser.All 权限。</span></li>
        </ul>
      </article>

      <article class="info-panel">
        <div class="section-head">
          <span class="marker">06</span>
          <div>
            <h2>最近修复</h2>
            <p>2026-05-25 生产实例更新。</p>
          </div>
        </div>
        <ul class="fix-list">
          <li>Graph token 换取失败后继续回退 IMAP。</li>
          <li>导入解析只切前三个分隔符，保护 refresh_token。</li>
          <li>邮箱工作台改为一屏取件和正文预览。</li>
        </ul>
      </article>
    </section>
  </main>
</template>

<script lang="ts" setup>
</script>

<style scoped>
.guide-page {
  min-height: calc(100vh - 64px);
  padding: 18px;
  background: #eef2f7;
  color: #172033;
}

.intro-band {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  max-width: 1180px;
  margin: 0 auto 16px;
  padding: 26px;
  border: 1px solid #d9e1ec;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(30, 41, 59, 0.08);
}

.intro-copy {
  max-width: 760px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
}

h1,
h2 {
  margin: 0;
  color: #172033;
  line-height: 1.25;
}

h1 {
  font-size: 30px;
}

h2 {
  font-size: 18px;
}

.summary {
  margin: 10px 0 0;
  color: #475569;
  font-size: 15px;
  line-height: 1.7;
}

.intro-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.primary-link,
.secondary-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 8px;
  font-weight: 700;
  text-decoration: none;
}

.primary-link {
  background: #2563eb;
  color: #ffffff;
}

.secondary-link {
  border: 1px solid #cbd5e1;
  color: #334155;
  background: #ffffff;
}

.status-grid,
.content-grid {
  display: grid;
  max-width: 1180px;
  margin: 0 auto;
  gap: 16px;
}

.status-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 16px;
}

.status-item,
.info-panel {
  border: 1px solid #d9e1ec;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(30, 41, 59, 0.07);
}

.status-item {
  padding: 18px;
}

.status-label {
  display: inline-flex;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.status-item strong {
  display: block;
  color: #0f172a;
  font-size: 16px;
}

.status-item p,
.info-panel p,
.note {
  margin: 8px 0 0;
  color: #64748b;
  line-height: 1.6;
}

.content-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.info-panel {
  padding: 20px;
}

.info-panel.wide {
  grid-column: 1 / -1;
}

.section-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.marker {
  display: inline-grid;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 8px;
  background: #eff6ff;
  color: #2563eb;
  font-weight: 800;
}

.steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.step {
  padding: 14px;
  border: 1px solid #e3e9f2;
  border-radius: 8px;
  background: #f8fafc;
}

.step span {
  display: inline-grid;
  width: 26px;
  height: 26px;
  margin-bottom: 10px;
  place-items: center;
  border-radius: 50%;
  background: #2563eb;
  color: #ffffff;
  font-size: 13px;
  font-weight: 800;
}

.step strong {
  display: block;
}

.code-block {
  overflow: auto;
  margin: 0;
  padding: 14px;
  border-radius: 8px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 13px;
  white-space: pre-wrap;
}

.protocol-list {
  display: grid;
  gap: 10px;
}

.protocol-list div,
.api-row {
  padding: 12px;
  border: 1px solid #e3e9f2;
  border-radius: 8px;
  background: #f8fafc;
}

.protocol-list strong,
.protocol-list code {
  display: block;
}

code {
  color: #1d4ed8;
  font-family: Consolas, Monaco, monospace;
  font-size: 12px;
}

.api-table {
  display: grid;
  gap: 10px;
}

.api-row {
  display: grid;
  grid-template-columns: 120px minmax(180px, 1fr) 1.2fr;
  align-items: center;
  gap: 12px;
}

.api-row span {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.api-row p {
  margin: 0;
}

.issue-list,
.fix-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.issue-list li,
.fix-list li {
  display: grid;
  gap: 4px;
  padding: 12px;
  border: 1px solid #e3e9f2;
  border-radius: 8px;
  background: #f8fafc;
}

.issue-list span,
.fix-list li {
  color: #64748b;
  line-height: 1.55;
}

@media (max-width: 900px) {
  .intro-band {
    align-items: stretch;
    flex-direction: column;
  }

  .status-grid,
  .content-grid,
  .steps {
    grid-template-columns: 1fr;
  }

  .api-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .guide-page {
    padding: 10px;
  }

  .intro-band,
  .info-panel,
  .status-item {
    padding: 16px;
  }

  h1 {
    font-size: 24px;
  }
}
</style>
