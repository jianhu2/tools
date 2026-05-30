## 项目介绍

搞这个项目主要是因为之前的 `MS_OAuth2API` 代码质量有点问题，维护起来越来越麻烦。  
所以在它的基础上做了优化，修复了一些bug，提升了代码质量和可维护性，这就是 `MS_OAuth2API_Next` 啦。  
有任何问题或建议，欢迎在项目仓库中提交 `issue`。  
或联系我: [z@unix.xin](mailto:z@unix.xin)  
体验地址: [https://mon.unix.xin/](https://mon.unix.xin/)

## 当前服务器部署说明

当前生产访问地址：`https://ms.eto.ccwu.cc/home`

当前默认工作台入口：`https://ms.eto.ccwu.cc/`

当前服务器项目路径：`/root/app/ms-oauth2-api/app`

当前部署方式：

- 后端：Node.js + Koa，入口文件 `main.js`
- 前端：Vue + Element Plus，构建产物位于 `web/MS_OAuth2API_Next_Web/dist`
- 容器：Docker Compose 服务 `ms-oauth2api`
- 对外代理：nginx 将 `ms.eto.ccwu.cc` 代理到 `127.0.0.1:3000`
- 容器端口：`127.0.0.1:3000->3000`

## 功能概览

本项目用于 Outlook / Microsoft 邮箱 OAuth2 取件和邮箱管理，主要功能如下：

- 支持通过网页导入邮箱账号数据，导入格式为：`邮箱----密码----client_id----refresh_token`
- 支持文件导入和粘贴导入，导入后的数据保存在浏览器 `localStorage`
- 支持查看邮箱列表、分页、批量删除、全部删除、批量导出、全部导出
- 支持三栏邮箱工作台：左侧账号列表、中间邮件列表、右侧邮件正文预览
- 支持点击邮箱后直接收取收件箱邮件，减少原来的“收件箱 -> 查看”两步操作
- 支持读取 `INBOX` 收件箱和 `Junk` 垃圾箱
- 支持获取全部邮件：`/api/mail_all`
- 支持获取最新一封邮件：`/api/mail_new`
- 支持清空邮箱文件夹：`/api/process-mailbox`
- 支持代理测试：`/api/test-proxy`
- 支持 socks5/http 代理参数，降低服务器 IP 访问 Microsoft 服务被限制的风险
- 支持可选 Redis 缓存 access token，避免频繁请求 Microsoft token 接口
- 支持 Microsoft Graph API 和 IMAP OAuth2 两种取件协议

## 当前版本协议行为

当前版本优先尝试 Microsoft Graph API：

- Graph scope：`https://graph.microsoft.com/Mail.Read offline_access`
- Graph 成功时直接通过 Graph 读取邮件

如果 Graph token 换取失败或 refresh token 未授权 Graph `Mail.Read`，服务会自动回退到 IMAP OAuth2：

- IMAP scope：`https://outlook.office.com/IMAP.AccessAsUser.All offline_access`
- IMAP 使用 XOAUTH2 连接 `outlook.office365.com:993`

因此，只授权了 IMAP scope 的长效邮箱也可以继续取件；如果 Graph 和 IMAP 都失败，通常说明 refresh token 已过期、授权租户不匹配、scope 未授权，或导入字段不正确。

## 2026-05-25 修复记录

本次在 `ms.eto.ccwu.cc` 生产服务上完成以下修复：

1. 修复 Graph 失败后不回退 IMAP 的问题

   修改文件：`services/api.js`

   原逻辑是先调用 Graph API 换取 access token；如果 Microsoft 返回 `invalid_grant`、`AADSTS70000` 或 scope 未授权错误，接口会直接返回 500，导致只授权 IMAP 的长效邮箱无法取件。

   新逻辑是：

   - `/api/mail_all`、`/api/mail_new`、`/api/process-mailbox` 都先尝试 Graph
   - Graph 失败时记录 warning 日志
   - 继续使用原始 refresh token 尝试 IMAP OAuth2
   - 只有 Graph 和 IMAP 都失败时才返回失败

2. 修复邮箱导入分隔符解析风险

   修改文件：`web/MS_OAuth2API_Next_Web/src/views/email/index.vue`

   原逻辑直接使用 `item.split(splitSymbol)`。如果分隔符被设置为单个 `-`，会把 UUID 格式的 `client_id` 或 token 内容拆坏。

   新逻辑只按前三个分隔符切分：

   - 第一段：邮箱
   - 第二段：密码
   - 第三段：client_id
   - 第四段：refresh_token，保留剩余全部内容

3. 重新构建并重启生产容器

   已执行前端构建和 Docker Compose 重建，当前容器 `ms-oauth2api` 已运行新版本。

4. 优化邮箱管理工作台 UI

   修改文件：

   - `web/MS_OAuth2API_Next_Web/src/views/email/index.vue`
   - `web/MS_OAuth2API_Next_Web/src/views/layout/index.vue`
   - `web/MS_OAuth2API_Next_Web/src/router/index.ts`
   - `web/MS_OAuth2API_Next_Web/src/App.vue`

   调整内容：

   - 根路径 `/` 默认进入邮箱管理工作台
   - 邮箱管理页改为三栏布局：账号列表、邮件列表、邮件正文预览
   - 点击左侧邮箱后直接拉取并展示收件箱邮件
   - 邮件列表点击邮件后在右侧直接预览正文
   - 顶部导航改为 `邮箱管理 / 说明`
   - 修复搜索或分页状态下编辑、删除邮箱时可能按错误索引操作的问题

5. 优化说明页面 UI

   修改文件：`web/MS_OAuth2API_Next_Web/src/views/home/index.vue`

   调整内容：

   - `/home` 改为服务说明和运维手册页面
   - 增加当前服务入口、部署信息、协议行为、使用流程、导入格式、API 列表、故障判断、最近修复记录
   - 与邮箱工作台保持统一的蓝白灰视觉风格

## 使用注意

- 推荐导入格式仍然使用默认分隔符 `----`
- 如果浏览器里已经导入过被错误解析的数据，需要删除旧记录后重新导入
- 如果日志中 Graph 失败后已经出现 `falling back to IMAP`，说明回退逻辑生效
- 如果 IMAP 仍然失败，需要重新检查 refresh token 是否有效，以及是否授权 `IMAP.AccessAsUser.All`
- 新版前端默认打开 `/` 即进入邮箱工作台，说明页位于 `/home`

## 2026-05-28 修复记录

本次在 `ms.eto.ccwu.cc` 生产服务上修复部分 Outlook 长效邮箱无法通过 IMAP fallback 收信的问题。

问题现象：

- 部分账号调用 Graph API 返回 `invalid_grant` / `AADSTS70000`
- 服务按预期回退到 IMAP OAuth2
- IMAP access token 可以换取成功，但 `node-imap` 在认证阶段报 `Timed out while authenticating with server`
- 少数情况下 Outlook IMAP 后端返回 `User is authenticated but not connected.`

排查结论：

- 服务器网络、nginx、Docker 容器和 `outlook.office365.com:993` 连通性正常
- 受影响账号的 IMAP XOAUTH2 底层握手可以通过
- 失败原因主要是 `node-imap` 默认认证超时时间偏短，以及 Outlook IMAP 后端偶发连接状态异常

修复内容：

1. 延长 IMAP 连接和认证超时

   修改文件：`services/MailService.js`

   在读取邮件和清空邮箱两个 IMAP 连接配置中增加：

   ```js
   authTimeout: 30000,
   connTimeout: 20000,
   ```

2. 增加 IMAP fallback 重试

   修改文件：`services/api.js`

   `fetchViaImap` 现在最多尝试 3 次。遇到 Outlook IMAP 偶发认证后未连接、认证超时等临时异常时，会短暂等待后重试。

3. 重新构建并重启生产容器

   已执行：

   ```bash
   cd /root/app/tools/ms-oauth2-api
   docker compose up -d --build ms-oauth2api
   ```

验证结果：

- `ms-oauth2api` 容器重建后运行正常，`RestartCount=0`
- `https://ms.eto.ccwu.cc/` 返回 `200 OK`
- 已验证受影响的两个 Outlook 长效邮箱均可通过 `/api/mail_new` 走 IMAP fallback 成功取到最新邮件

## 2026-05-28 浏览器缓存与重复导入修复

本次继续修复旧浏览器中垃圾箱邮件无法按新数据收取的问题。

问题现象：

- 换一个浏览器访问可以正常收取垃圾箱邮件
- 原浏览器即使强制刷新页面，仍然可能读取旧账号数据或旧邮件缓存
- 部分用户重新导入同一个邮箱时，前端会因为邮箱已存在而跳过导入，导致旧 `refresh_token` 和旧邮件缓存继续生效

排查结论：

- 后端接口和 IMAP fallback 正常
- 旧浏览器问题主要来自两处：
  - `index.html` 之前跟随静态资源使用了一年缓存，旧入口文件可能长期不更新
  - 前端账号和邮件列表保存在浏览器 `localStorage`，重复导入同邮箱不会覆盖旧记录

修复内容：

1. 禁止 HTML 入口缓存

   修改文件：`main.js`

   - 静态资源中 HTML 响应统一设置为不缓存
   - `/home` 等前端 history fallback 页面也设置为不缓存
   - hashed 静态资源 `/assets/*` 继续允许长期缓存

   当前 HTML 响应头包含：

   ```text
   Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate
   Pragma: no-cache
   Expires: 0
   ```

2. 重复导入同邮箱时覆盖旧记录

   修改文件：`web/MS_OAuth2API_Next_Web/src/views/email/index.vue`

   新逻辑：

   - 新邮箱：追加到邮箱列表
   - 已存在邮箱：使用新导入的数据覆盖旧记录
   - 覆盖时清理该邮箱本地邮件缓存：
     - `<email>INBOX`
     - `<email>Junk`
   - 导入成功提示改为显示新增和更新数量

3. 重新构建前端并重启生产容器

   已使用 Node 容器构建前端产物，并执行：

   ```bash
   cd /root/app/tools/ms-oauth2-api
   docker compose up -d --build ms-oauth2api
   ```

验证结果：

- `/` 和 `/home` 均返回 `Cache-Control: no-store`
- 新前端入口已切换到新的 hashed JS 文件
- `ms-oauth2api` 容器重建后运行正常，`RestartCount=0`


### 版本说明
- `MS_OAuth2API_Next` 只用来部署在服务器上
- `MS_OAuth2API` 后续只针对于 Vercel 版本更新

### 维护计划
- 要是微软更新了 OAuth2 的规则，`MS_OAuth2API` 的 Vercel 版本会同步维护
- 服务器版本的功能更新和bug修复，都会在 `MS_OAuth2API_Next` 里进行

下面是 `MS_OAuth2API_Next` 的一些功能和优势：

- 自动判断使用graph协议还是imap协议
    - graph协议: 微软的新协议，支持更多的功能，比如获取邮件附件、发送邮件等
    - imap协议: 微软的旧协议，支持的功能比较少
- 支持redis缓存，避免重复请求微软服务器，提高响应速度
- 支持传入proxy代理，防止服务器IP受限
    - 支持socks5代理(格式: `socks5://username:password@ip:port`)
    - 支持http代理(格式: `http://ip:port`)
    - 查询代理是否使用成功，可以通过`/api/test-proxy`接口，通过返回的IP是否与代理IP一致来判断
    - 支持默认代理池, 可以在API不传入代理的情况下，使用默认代理池中的代理（TODO 待实现）
- 支持邮箱验证，两种方式(TODO 待实现)
    - 规则验证(通过判断邮箱格式)
    - 精确验证(需要配合数据库，判断邮箱是否存在)
- 配套使用页面 + 客户端
    - 支持邮箱导入
    - 支持邮箱验证
    - 支持邮箱清空
    - 支持邮件查看
- 支持Docker部署(TODO 待实现)

### 使用说明
- 部署流程
    - 克隆项目到服务器 ` git clone https://github.com/HChaoHui/MS_OAuth2API_Next`
    - 进入项目目录 `cd MS_OAuth2API_Next`
    - 安装依赖 `npm install`
    - 配置环境变量 见`.env`
    - 启动项目 `npm run start`
    - 配套资源文件在 `web/MS_OAuth2API_Next_Web` 目录下，如需自定义，修改后打包即可，项目会读取`web/MS_OAuth2API_Next_Web/dist`目录下的文件
    - 修改请保留作者信息，谢谢

- Redis 配置
    - `USE_REDIS` 为 `1` 时，开启 Redis 缓存
    - `USE_REDIS` 为 `0` 时，关闭 Redis 缓存
    - `REDIS_HOST` 为 Redis 服务器地址
    - `REDIS_PORT` 为 Redis 服务器端口

## 📚 API 文档

### 获取最新的一封邮件

- **方法**: `GET/POST`
- **URL**: `/api/mail_new`
- **描述**: 获取最新的一封邮件。
- **参数说明**:
  - `refresh_token` (必填): 用于身份验证的 refresh_token。
  - `client_id` (必填): 客户端 ID。
  - `email` (必填): 邮箱地址。
  - `mailbox` (必填): 邮箱文件夹，支持的值为 `INBOX` 或 `Junk`。
  - `socks5` (可选): socks5 代理地址，格式为 `socks5://username:password@ip:port`。
  - `http` (可选): http 代理地址，格式为 `http://ip:port`。

### 获取全部邮件

- **方法**: `GET/POST`
- **URL**: `/api/mail_all`
- **描述**: 获取全部邮件。
- **参数说明**:
  - `refresh_token` (必填): 用于身份验证的 refresh_token。
  - `client_id` (必填): 客户端 ID。
  - `email` (必填): 邮箱地址。
  - `mailbox` (必填): 邮箱文件夹，支持的值为 `INBOX` 或 `Junk`。
  - `socks5` (可选): socks5 代理地址，格式为 `socks5://username:password@ip:port`。
  - `http` (可选): http 代理地址，格式为 `http://ip:port`。

### 清空收件箱

- **方法**: `GET/POST`
- **URL**: `/api/process-mailbox`
- **描述**: 清空收件箱。
- **参数说明**:
  - `refresh_token` (必填): 用于身份验证的 refresh_token。
  - `client_id` (必填): 客户端 ID。
  - `email` (必填): 邮箱地址。
  - `mailbox` (必填): 邮箱文件夹，支持的值为 `INBOX` 或 `Junk`。
  - `socks5` (可选): socks5 代理地址，格式为 `socks5://username:password@ip:port`。
  - `http` (可选): http 代理地址，格式为 `http://ip:port`。

### 代理测试

- **方法**: `GET/POST`
- **URL**: `/api/test-proxy`
- **描述**: 测试代理是否生效。
- **参数说明**:
  - `refresh_token` (必填): `任意字符串即可`。
  - `client_id` (必填): `任意字符串即可`。
  - `email` (必填): `任意字符串即可`。
  - `mailbox` (必填): `任意字符串即可`。
  - `socks5` (可选): socks5 代理地址，格式为 `socks5://username:password@ip:port`。
  - `http` (可选): http 代理地址，格式为 `http://ip:port`。
