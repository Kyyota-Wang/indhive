# INDHIVE 部署手册

最后更新：2026-08-19 · 面向接手部署工作的 AI 或开发者

读完应该能：在本地跑起来、拿到需要的凭据、部署到 Cloudflare、验证部署真的成功、出问题时回滚。

> **⚠️ 本文不包含任何密钥值，也不要往里面写。** 只写「去哪里拿」。

---

## 0. 当前状态（部署已完成）

| 项 | 值 |
|---|---|
| 正式地址 | https://indhive.com 和 https://www.indhive.com |
| 测试地址 | https://indhive.pumpkin-ai-v2.workers.dev |
| Worker 名 | `indhive` |
| Cloudflare 账号 | `<你的 Cloudflare 账号邮箱>` |
| Account ID | `<ACCOUNT_ID>`（标识符，不是密钥） |
| 当前线上 version | `23bc3e3d-d676-4512-84ac-b64de9327d6a` |
| Git 仓库 | `Kyyota-Wang/indhive`，分支 `main` |

证书 `CN=indhive.com` 于 2026-08-19 签发，有效期至 2026-11-17，由 Cloudflare 自动续期。

**这个仓库可以是 public。** 十个案例全部是虚构合成数据，不含任何真实申办方材料。唯一不能进 Git 的是 `V1/.dev.vars`。

---

## 1. 这个项目是什么

FDA IND **Module 1** 自动化准备的演示。

一个 Cloudflare Worker 同时承担两件事：

1. 托管前端静态资源（`public/`）
2. 提供 3 个端点：`/api/cases`、`/api/case/:id`、`/api/chat`

没有数据库，没有账号系统，没有服务端状态。对话上下文由客户端携带。

### 端点一览

| 端点 | 方法 | 耗时 | 成本 | 保护 |
|---|---|---:|---:|---|
| `/api/cases` | GET | <10ms | $0 | 无 |
| `/api/case/:id` | GET | <10ms | $0 | 无 |
| `/api/chat` | POST | 5–40s | ~$0.02–0.15 | 限流 |

**只有 `/api/chat` 花钱。** 它无认证、任何人有链接就能用 —— 这条线决定了限流设计。

---

## 2. 两半结构

```
inputs/partner-package/    搭档的 PMX-103 输入包 —— 不入版本库（21 CFR 312.130）
        │
        │  python build/extract_partner_package.py   映射成 case + 他自己的答案
        │  python scripts/scan_invariants.py           扫 23 个不变量（按需跑，要 API key）
        ▼
indkit/                 Python 项目 —— 全部生成逻辑的唯一实现
        │
        │  python scripts/run_pipeline.py --all        为 11 个案例生成产物
        │  python build/bundle_cases.py   汇总成 V1/src/cases.json
        ▼
V1/                     Cloudflare Worker
```

搭档包里的文档带他自己的机密标记，**永远不要提交**。提交的是这两个脚本的**输出**：
`data/source_cases/PMX103.json` 和 `data/partner_reference/PMX103.json`。
`build/tamper_demo.py` 会把整个包复制到 `outputs/tamper/` 再改，那个目录同样在 `.gitignore` 里。

1571 映射、Module 1 缺口分析、1.20 装配、校验规则**只在 Python 里实现了一次**。Worker 把它们的产物当构建产物发出去，只有两件事在请求时实时跑：cover letter 生成，和对生成文本的 grounding 核查。

这些流水线步骤是确定性的，所以预计算和实时算逐字节相同。

**改了 Python 逻辑或案例数据之后，必须重跑那两条命令再部署**，否则线上还是旧产物。

---

## 3. 凭据

只有两样。**没有任何一样应该进 Git。**

### 3.1 Cloudflare 授权

这台机器上 **wrangler 已经是登录状态**（OAuth，`<你的 Cloudflare 账号邮箱>`）。确认：

```bash
cd V1 && npx wrangler whoami
```

应该看到 Account ID `<ACCOUNT_ID>`，以及 `workers_scripts (write)`、`workers_routes (write)` 权限。

如果失效了，重新授权：

```bash
npx wrangler login
```

浏览器会开授权页。**必须看到终端出现 `Successfully logged in`。**

> ⚠️ **在 Cloudflare 网页后台登录 ≠ wrangler 已授权。** 两件完全独立的事。

非交互场景（CI）用 scoped API token：https://dash.cloudflare.com/profile/api-tokens ，用 "Edit Cloudflare Workers" 模板，范围限定这个账号和 `indhive.com` zone。**不要用 Global API Key。** 设成 `CLOUDFLARE_API_TOKEN` 环境变量，不要写进任何文件。

### 3.2 Anthropic API Key

**去哪里拿：** https://console.anthropic.com → Settings → API keys → Create Key（只显示一次，`sk-ant-` 开头）。

**顺手做成本保护**：Settings → Limits 设月度上限。这个站每次对话约 $0.02–0.15。

**本地**放 `V1/.dev.vars`（已 gitignore）：

```
ANTHROPIC_API_KEY=sk-ant-...
```

**生产**设成 Worker secret：

```bash
cd V1 && npx wrangler secret put ANTHROPIC_API_KEY
```

交互式输入，不回显不落盘。或者从本地文件直接管道进去：

```bash
sed -n 's/^ANTHROPIC_API_KEY=//p' .dev.vars | tr -d '\r\n' | npx wrangler secret put ANTHROPIC_API_KEY
```

确认设上了（不显示值）：

```bash
npx wrangler secret list
```

> **注意**：secret 存在 ≠ 有效。只有真实调用一次才知道 key 有没有过期。

---

## 4. 配置文件：`V1/wrangler.jsonc`

```jsonc
{
  "name": "indhive",                  // 决定 workers.dev 地址的第一段
  "main": "src/index.ts",
  "compatibility_date": "2026-08-01",
  "compatibility_flags": ["nodejs_compat"],
  "assets": { "directory": "./public", "binding": "ASSETS" },
  "observability": { "enabled": true },
  "workers_dev": true,
  "ratelimits": [
    { "name": "CHAT_LIMIT", "namespace_id": "2001", "simple": { "limit": 8, "period": 60 } }
  ],
  "routes": [
    { "pattern": "indhive.com", "custom_domain": true },
    { "pattern": "www.indhive.com", "custom_domain": true }
  ]
}
```

### 必须理解的几点

**两个域名都用 `custom_domain: true`，不是 route。** wrangler 走 API 会**连 DNS 记录一起建**并签证书，所以子域名不需要手工建 AAAA `100::` 占位记录。（网页后台的 Connect domain 对话框做精确 zone 匹配，输 `www.indhive.com` 会报 `No zones match` —— 那是对话框的限制，用 wrangler 就没这问题。）

**`workers_dev: true` 必须显式写。** 一旦声明了 `routes`，wrangler 默认把 workers.dev 地址**关掉**，部署输出里会有一行警告。留着它作为证书签发期间的回退地址。

**`ratelimits` 的 `period` 只支持 10 或 60 秒。** 做不了「每天最多 N 次」。而且这个限流器是**边缘位置级、最终一致**的 —— 是抗持续滥用的兜底，不是精确闸门。配置值要比想要的效果更严。

**`assets.directory` 指向 `./public`**，是直接提交进 Git 的源文件，不是构建产物。这个项目前端没有构建步骤，所以部署前不需要 build。

---

## 5. 部署

### 5.1 部署前检查

```bash
cd V1
git status --short                  # 确认没有意外改动
npx tsc --noEmit                    # 类型检查
npx wrangler whoami                 # 确认授权和账号对
npx wrangler secret list            # 确认 ANTHROPIC_API_KEY 在
npx wrangler deploy --dry-run       # 不上传，只验证能打包
```

如果改过 Python 侧：

```bash
cd ../indkit && python scripts/run_pipeline.py --all
cd ../V1 && python build/bundle_cases.py
```

`scripts/run_pipeline.py --all` 不会重跑不变量扫描（那一步要语料和模型）。只有改了 `scripts/scan_invariants.py`
或搭档换了文档才需要：

```bash
cd indkit && python scripts/scan_invariants.py
```

它写 `outputs/generated/PMX103/invariant_scan.json`，随后必须再跑一次 `bundle_cases.py`。

### 5.2 部署

```bash
npx wrangler deploy
```

### 5.3 输出里要核对什么

```
env.CHAT_LIMIT (8 requests/60s)      Rate Limit
env.ASSETS                           Assets
Uploaded indhive (15.64 sec)
  https://indhive.pumpkin-ai-v2.workers.dev
  indhive.com (custom domain)
  www.indhive.com (custom domain)
Current Version ID: 23bc3e3d-d676-4512-84ac-b64de9327d6a
```

必须确认：

- **`CHAT_LIMIT` binding 在**
- **三个地址都列出来了**（少了 workers.dev 说明 `workers_dev: true` 掉了）
- 静态资源上传数量合理（首次 4 个，之后只传变更的）

**把 Version ID 记下来** —— 这是回滚点。secret 不会出现在这个列表里，正常。

---

## 6. 验证清单

```bash
U="https://indhive.com"

# 1. 页面和静态资源
for p in / /app.js /styles.css /favicon.svg; do
  curl -s -o /dev/null -w "$p  %{http_code}\n" "$U$p"
done

# 2. 案例接口（应返回 11 个：IND001-010 加 PMX103）
curl -s "$U/api/cases" | python -c "import json,sys; d=json.load(sys.stdin)['cases']; print(len(d),'cases;', [c['case_id'] for c in d if c.get('origin')=='partner_supplied'])"

# 3. 未知案例 -> 404
curl -s -o /dev/null -w "bogus case %{http_code}\n" "$U/api/case/NOPE"

# 4. 超长输入 -> 400
python -c "import json; print(json.dumps({'messages':[{'role':'user','content':'x'*5000}]}))" > /tmp/big.json
curl -s -o /dev/null -w "oversize %{http_code}\n" -X POST "$U/api/chat" \
  -H 'content-type: application/json' -d @/tmp/big.json

# 5. GET 打 chat -> 405
curl -s -o /dev/null -w "GET chat %{http_code}\n" "$U/api/chat"

# 6. 证书
echo | openssl s_client -connect indhive.com:443 -servername indhive.com 2>/dev/null \
  | openssl x509 -noout -subject -dates
```

### 结果对照

| 检查 | 期望 |
|---|---|
| 页面 / 静态资源 | 全 200 |
| `/api/cases` | 11 个案例，其中 `PMX103` 的 `origin` 是 `partner_supplied` |
| 未知案例 | 404 |
| 超长输入 | 400 |
| GET `/api/chat` | 405 |
| 证书 | `CN=indhive.com`，有效期覆盖当前 |

### 浏览器走查

在真实浏览器打开 https://indhive.com：

- 落地页顶部是 **PMX-103** 独立深色块，标 `Partner input · reviewable`
- 下面是十个虚构案例，再下面两组卡片：**Input**（1 张）+ **Generated output**（5 张）
- 切到 IND003，五张输出卡应出现红黄标记
- 进 Source input，`draft_form_1571_tracker` 那条记录两个字段都带 `CONFLICT`
- 点任一字段的目的地标签，跳到对应视图且目标字段已展开
- 点 **Open PMX-103**：多出 **Checked against his answers** 一组四张卡，
  底部出现「Module 1 只用一小片」的边界声明；再切回 IND001，这两块都消失
- 缺口对照视图里，GAP-01 / GAP-04 / GAP-05 / GAP-06 四条都在「Reached by both」
- 右下角对话球能开，console 无报错

### 最后一步：一次真实调用

上面全过之后，唯一没证明的是 **API key 是否有效**（存在 ≠ 有效）。在对话框里问一句，比如 `What am I looking at?`。成功即全通。

**必测的两道陷阱题**（这是这个产品可信度的核心）：

- `Which sponsor name is the correct one for IND003?` → 必须拒绝，摊开两个值说需人工判定
- `When will Module 4 ship and how much does it cost?` → 必须说自己无法回答商业问题

任何一题它顺着答了，说明 `V1/src/prompt.ts` 的约束被削弱了，回滚。

---

## 7. 回滚

```bash
cd V1
npx wrangler deployments list          # 看历史版本
npx wrangler rollback <VERSION_ID>
```

或网页后台：Worker → Deployments → 选历史版本 → Rollback。

### 已知版本

| Version ID | 说明 |
|---|---|
| `23bc3e3d-d676-4512-84ac-b64de9327d6a` | 当前线上。含边缘限流 binding |
| `c9f8e583-4f90-4c41-af82-04f2f0d2af9f` | 自定义域名 + workers.dev，**无边缘限流** |
| `cabf38b1-f9fe-4412-bcc9-013c31a37939` | 绑域名，**workers.dev 被关掉** |
| `981d1831-52b5-4593-8f29-538423b92cf4` | 首次部署，仅 workers.dev，**secret 还没设** |

**代码层面的回退点是 Git**：`git log --oneline`。

---

## 8. 坑（都踩过）

### 8.1 声明 routes 会自动关掉 workers.dev

部署输出里那行警告很容易划过去。必须显式写 `workers_dev: true` 才保得住测试地址。

### 8.2 Windows 上 `Ctrl+C` 杀不干净 workerd

本地开发时，僵尸 `workerd` 进程会继续占着端口并**用旧代码应答**，表现为「改了没生效」。

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'workerd.exe' -or ($_.Name -in @('node.exe','cmd.exe') -and $_.CommandLine -match 'wrangler') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

### 8.3 删掉再重建静态文件，wrangler dev 的 asset manifest 认不到

本地 `wrangler dev` 运行中删除并重建 `public/` 下的文件，会出现 404。**重启 wrangler。**

### 8.4 Git Bash 会把 `/F` 当路径转换

`taskkill /F /PID` 在 Git Bash 里报 `Invalid argument - 'F:/'`。用 PowerShell 的 `Stop-Process`。

### 8.5 别让模型凭记忆报 box 号

`get_source_input` 一开始不返回字段去向，模型就凭记忆说 IND number 在 Box 1（实际是 Box 6）。**凡是有确定答案的东西，让工具返回，不要让模型回忆。** 现在 `src/tools.ts` 的 `destinationOf()` 和 `public/app.js` 里同名函数保持一致，两边不会漂。

### 8.6 Opus 的 thinking block 必须原样回传

流式解析要累积 `thinking_delta` 和 `signature_delta`，否则回传历史里是空 thinking 块，第二轮 API 直接 400。只在多轮工具调用时触发，单轮测试测不出来。

### 8.7 并行工具调用时 chip 标签会错配

前端按位置匹配 `tool_done` 会贴错参数。必须按 `tool_use.id` 匹配 —— 这些 chip 是可信度来源，贴错等于撒谎。

---

## 9. 不能动的三条

改代码时必须保留。

1. **冲突绝不自动选边。** 两条源记录打架时，canonical 值置空 + 标 CONFLICT，界面摊开所有竞争值。system prompt 里也有对应约束。这是整个产品可信度的地基。
2. **1571 只放真表上存在的字段。** 不在表上的（dosage form、route、protocol 标识、investigator 联系方式）归到 *Supporting data — not a Form 1571 box*。曾经把这些塞进 Box 12，内行一眼就能看穿。
3. **cover letter 的 grounding 核查不能去掉。** 生成后反查文本里的邮箱、电话、日期、邮编是否都能追到白名单事实。这是「AI 写的文档没有编造」的唯一证据。

---

## 10. 还没做的

| 缺口 | 说明 |
|---|---|
| 从真实文档抽取 | 源记录是已抽取好的结构化数据。读 PDF/DOCX/表格这一层完全没做，**这是最大的缺口** |
| Form 1572 / 3674 / 药品标签 | 无生成器 |
| eCTD 打包、Part 11 签名、审计轨迹 | 无 |
| Module 2/3/4/5 | 超出本 demo 范围 |
| 用户账号 / 配额 | 任何人有链接就能用 |
| 持久化 | 刷新即丢 |
| 源记录词汇改造 + 原文摘录 | 源记录的键名就是 canonical 路径，所以输入→1571 看起来接近改名。改成真实文档词汇并加原文摘录，能把演示力提升一个量级 |
