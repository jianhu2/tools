# 服务器巡检与 DDoS 应急处理记录

**日期**：2026-05-24  
**涉及服务器**：
- 主服务器：prod.bbroot.com（Oracle Cloud ARM64，4 核 24G）
- 备用服务器：ai.jianhu.cc（Oracle Cloud ARM64，2 核 12G）

---

## 一、初始巡检发现的问题

### 1. 注册邮箱验证功能丢失

**现象**：用户反馈 prod.bbroot.com 注册时没有邮箱验证步骤。

**排查过程**：
- 检查 nginx 配置，未见邮件相关路由
- 检查 sub2api Docker 环境变量，无 SMTP 相关配置
- 查询数据库 `settings` 表，发现：

```sql
SELECT key, value FROM settings WHERE key LIKE '%smtp%' OR key LIKE '%email%';
```

| key | value |
|-----|-------|
| email_verify_enabled | **false** |
| smtp_host | mail.seek.li |
| smtp_port | 465 |
| smtp_username | sub2@seek.li |
| smtp_use_tls | true |

**根因**：SMTP 配置完整，但 `email_verify_enabled` 被重置为 `false`。  
推测是容器重建或版本升级时该数据库字段被覆盖为默认值。

**解决方案**（待执行）：在 sub2api 管理后台开启"注册邮箱验证"，或执行：
```sql
UPDATE settings SET value = 'true' WHERE key = 'email_verify_enabled';
```

---

### 2. nginx worker_connections 严重不足

**现象**：nginx error.log 大量报错：
```
768 worker_connections are not enough while connecting to upstream
```

**根因**：Ubuntu 默认 `worker_connections = 768`，从未调整。4 个 worker 进程 × 768 = 理论上限 3072，而实际 TCP 连接数已超过该值。

---

### 3. DDoS 攻击（紧急）

**发现时间**：05:36 左右  
**现象**：
- CPU 负载从正常的 ~1 飙升至 **19.12**（4 核机器，满载为 4.0）
- TCP 连接数达 **5750**
- nginx access.log 当天已写入 **327MB**（前一天全天仅 5MB）
- error.log 当天 **50MB**
- 大量请求返回 HTTP 500
- nginx 报 `socket() failed (24: Too many open files)`

**攻击特征**：
- 分布式僵尸网络，数十个 IP 同时发起
- 主力攻击 IP：`45.174.243.20`（轮换 User-Agent，全部 GET /）
- 其他参与 IP：62.60.230.214、66.63.163.48、213.14.144.16 等
- 每个 IP 请求量在 100~800 之间，规避单 IP 限速

---

## 二、应急处理过程

### 阶段一：紧急封锁攻击 IP

临时用 iptables 封锁当时最活跃的 17 个攻击 IP：
```bash
iptables -I INPUT -s 45.174.243.20 -j DROP
# ... 共 17 个 IP
```

效果有限——僵尸网络持续换 IP，新 IP 接替攻击。

### 阶段二：停止 nginx 止血

攻击持续，文件句柄耗尽，服务完全不可用，临时停止 nginx：
```bash
systemctl stop nginx
```
TCP 连接数从 5750 骤降至 5，负载开始回落。

### 阶段三：部署系统性防护

---

## 三、防护配置详情

### 3.1 nginx 主配置优化（/etc/nginx/nginx.conf）

| 配置项 | 原值 | 新值 | 说明 |
|--------|------|------|------|
| worker_connections | 768 | **65536** | 提升 85 倍 |
| use epoll | 无 | **开启** | Linux 高性能 I/O 模型 |
| multi_accept | 无 | **开启** | 一次接受所有新连接 |
| ssl_protocols | TLSv1/1.1/1.2/1.3 | **TLSv1.2/1.3** | 去掉不安全版本 |

新增 rate limit zone：
```nginx
limit_req_zone $binary_remote_addr zone=general:20m rate=30r/s;
limit_req_status 429;
limit_conn_zone $binary_remote_addr zone=conn_limit:20m;
```

### 3.2 站点配置限速（prod.bbroot.com / ai.jianhu.cc）

在 HTTPS server 块中加入：
```nginx
limit_conn conn_limit 50;       # 每 IP 最多同时 50 个连接
limit_req zone=general burst=60 nodelay;  # 每 IP 30 req/s，burst 60
```

### 3.3 iptables hashlimit（内核层，最有效）

```bash
# 清空旧规则，重建
iptables -F INPUT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# HTTPS/HTTP：每 IP 每秒最多 20 个新连接，burst 40，超出丢包
iptables -A INPUT -p tcp --dport 443 -m state --state NEW \
  -m hashlimit --hashlimit-name https_new \
  --hashlimit-above 20/sec --hashlimit-mode srcip --hashlimit-burst 40 \
  -j DROP

iptables -A INPUT -p tcp --dport 80 -m state --state NEW \
  -m hashlimit --hashlimit-name http_new \
  --hashlimit-above 20/sec --hashlimit-mode srcip --hashlimit-burst 40 \
  -j DROP

iptables -A INPUT -j ACCEPT

# 持久化（重启后自动恢复）
netfilter-persistent save
```

### 3.4 fail2ban 自动封禁

```bash
apt install fail2ban
```

配置 `/etc/fail2ban/jail.local`：
```ini
[DEFAULT]
bantime  = 3600
findtime = 60
maxretry = 10
banaction = iptables-multiport
backend  = polling

[nginx-limit-req]
# nginx 429 超过 10 次 → 封禁 1 小时
enabled  = true
filter   = nginx-limit-req
logpath  = /var/log/nginx/error.log
maxretry = 10
findtime = 60
bantime  = 3600
port     = http,https

[nginx-botsearch]
# 扫描行为超过 5 次 → 封禁 24 小时
enabled  = true
filter   = nginx-botsearch
logpath  = /var/log/nginx/access.log
maxretry = 5
findtime = 60
bantime  = 86400
port     = http,https

[sshd]
# SSH 暴力破解超过 5 次 → 封禁 24 小时
enabled  = true
port     = ssh
maxretry = 5
bantime  = 86400
backend  = systemd
```

### 3.5 内核参数调优（/etc/sysctl.conf）

```bash
net.ipv4.tcp_syncookies = 1        # 防 SYN flood
net.ipv4.tcp_max_syn_backlog = 4096
net.core.somaxconn = 65535
fs.file-max = 1000000              # 解决 Too many open files
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
```

应用：`sysctl -p`

---

## 四、处理前后对比

| 指标 | DDoS 高峰 | 处理后 |
|------|-----------|--------|
| CPU 负载 | 19.12 | **0.01** |
| TCP 连接数 | 5750 | **~30** |
| HTTPS 响应时间 | 35 秒 | **~100ms** |
| nginx 状态 | 停止 | **正常运行** |
| HTTP 500 错误 | 大量 | **0** |

---

## 五、防护层次架构

```
外部流量
    │
    ▼
iptables hashlimit（内核层）
每 IP 超过 20 新连接/秒 → 直接丢包，不消耗 CPU
    │
    ▼
nginx rate limit（应用层）
每 IP 30 req/s，burst 60；每 IP 最多 50 并发连接
    │
    ▼
fail2ban（自动封禁）
监控 nginx 日志，触发 429 超限 → 自动加 iptables DROP
    │
    ▼
sub2api / payment-svc（业务层）
只有通过以上三层的合法请求才能到达
```

---

## 六、备份文件位置

| 服务器 | 文件 |
|--------|------|
| prod.bbroot.com | `/etc/nginx/nginx.conf.bak.*` |
| prod.bbroot.com | `/tmp/prod.bbroot.com.bak.*` |
| ai.jianhu.cc | `/etc/nginx/nginx.conf.bak.*` |
| ai.jianhu.cc | `/tmp/ai.jianhu.cc.bak.*` |

---

## 七、遗留待处理

- [ ] **开启注册邮箱验证**：在 sub2api 管理后台 → 系统设置 → 邮件，开启"注册邮箱验证"开关
- [ ] **定期备份 settings 表**：防止关键配置因容器重建丢失
  ```bash
  docker exec sub2api-postgres-prod pg_dump -U sub2api -t settings sub2api > settings_backup.sql
  ```
- [ ] **考虑接入上游 DDoS 清洗**：若攻击规模升级（数千 IP 慢速请求），当前方案可能不足，需考虑 Oracle Cloud 安全列表或其他上游防护

---

## 八、经验总结

1. **nginx 默认配置不适合生产**：`worker_connections 768` 是 Ubuntu 安装默认值，上线前必须调整
2. **关键配置应有持久化保障**：sub2api 的 `email_verify_enabled` 存在数据库，容器重建可能重置，应纳入备份和检查流程
3. **分布式 DDoS 无法靠封 IP 解决**：僵尸网络有大量 IP 可用，需在更底层（内核 hashlimit）限速，配合 fail2ban 自动化响应
4. **四层防护叠加是标准做法**：云层（Oracle 安全列表）→ 内核层（iptables）→ 应用层（nginx）→ 自动化（fail2ban）
