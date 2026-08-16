# TradingAgents Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](pyproject.toml)

[TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) 的增强套件：**不修改原项目任何文件**，为多智能体股票分析补上「读得完、推得出、比得了、看得见」四种能力。

## 背景

[TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) 是一个优秀的多智能体 A 股分析平台——市场分析师、基本面分析师、多空研究团队、交易员、风控经理、投资组合经理轮番上阵，产出一份深度报告。但实际天天用它看盘时，有几个真实的痛点：

1. **报告读不完**：一次"全面"深度分析产出十几万字（光多空辩论就 7 万字），开盘前只有 5 分钟
2. **跑完不吭声**：分析要跑十几分钟，得自己开网页反复刷新看进度
3. **换模型太麻烦**：想对比不同模型的分析效果，只能一个个手动跑、手动抄数据
4. **辩论没法看**：多空双方几个回合的激烈交锋是报告里最有价值的部分，却只能翻终端日志

Studio 就是补这四块拼图的：**四个独立模块 + 一个统一命令行 + 一份集中配置**。

## 功能

| 模块 | 解决的问题 | 一句话效果 |
|---|---|---|
| **digest** | 报告读不完 | 十几万字报告提炼成约 200 字开盘前简报（结论/信号/风险/动作四段式） |
| **notify** | 跑完不吭声 | 飞书卡片主动推送（股票名称 + 简报 + 详情按钮），cron 定时全管道自动化 |
| **compare** | 换模型太麻烦 | 一条命令让 N 个模型同题分析，产出耗时/token/成本/决策硬指标对比表 |
| **replay** | 辩论没法看 | 智能体辩论渲染成回放页：聊天流（多空一来一回）+ 多空对垒（分歧点两两配对）|

### digest — 开盘前简报

从原项目的报告产物中取全文（自动处理模型输出里的转义残留与 dict 转储），用 OpenAI 兼容接口的大模型提炼：

```
【结论】中性偏持有：中报数周内落地可免费裁决参数分歧，事件前不加仓也不割肉
【信号】现价88.90处布林13.1%分位超卖；RSI6=31.3接近超卖；缩量阴跌无恐慌抛售
【风险】中报跳空事件风险；收盘跌破87.80或引发止损盘连锁抛售，下看85整数关口
【动作】存量约15%仓位持有；收盘破87.80无条件清仓，反弹至90.5-92无量可减仓四分之一
```

### notify — 多渠道推送与定时

- 支持渠道：**飞书** / **钉钉** / **企业微信** / **Telegram** / **通用 JSON webhook**，可同时配多个、全部生效
- 同一渠道可推多个群（`feishu#盯盘群` / `feishu#决策群`），注册式扩展新渠道
- 卡片带股票名称与多空判断，底部按钮直达**完整报告页**（左侧子报告导航 + 右侧内容，手机为抽屉式目录）与**辩论回放页**
- `cron` 调度器常驻：工作日 09:30 自动 `分析 → 提炼 → 推送`，全程无人值守

### compare — 多模型对比

```bash
studio compare run 002594 -m glm-5.3,GLM-5.3,qwen-max -d 标准
```

同一支股票、同一深度并发跑多个模型（并发数可配，尊重原项目用户级限流），自动采集硬指标：

| 模型 | 状态 | 耗时 | 报告字数 | 输入tok | 输出tok | 成本 | 决策 |
|---|---|---|---|---|---|---|---|
| ... | | | | | | | |

结果落 SQLite + markdown/CSV（Excel 可直接打开），分步耗时与错误明细一并列出。

### replay — 辩论回放

从研究团队报告的原始数据中**精确解析**出多空双方的轮次发言（不是靠猜），渲染成自包含单文件 HTML，可直接发给任何人：

- **💬 辩论实况**：聊天对话框，多头（红·右）空头（绿·左）一来一回，按轮分隔，长论点折叠展开，底部是研究经理裁决
- **⚔️ 多空对垒**：LLM 把双方论点按话题两两配对——左列多头怎么说、右列空头怎么说，保留关键价位与数字；每个任务只生成一次，落盘缓存

另支持完整分析时间线视图（各 agent 产出按流程分组、搜索、筛选、自动播放）。

## 架构：零侵入集成

Studio 对 TradingAgents-CN **只读**，全部交互走三条通道，原项目一个文件都不用改：

```
┌──────────────┐   HTTP API（登录/发起分析/轮询/取报告/用量）
│              │◀──── MongoDB（可选，仅兜底）
│   studio     │   data/ 卷只读挂载（报告产物/辩论过程）
│              │────▶ 自己的 SQLite / 导出 HTML / 飞书
└──────────────┘
```

唯一的"写"是发起分析请求——与你在网页上点"开始分析"完全等价。

## 安装

### 方式一：本机直跑

```bash
git clone https://github.com/frank-quant/TradingAgents-CN-studio.git studio
cd studio
pip install -e .
cp studio.yaml.example studio.yaml   # 填 api 密码 / llm key / 飞书 webhook
studio doctor                        # 自检：API/登录/数据卷/LLM/渠道
```

要求：Python ≥ 3.10，能访问到 TradingAgents-CN 的 Web 入口（默认 `http://localhost`）。

`studio.yaml` 关键配置：

| 段 | 作用 |
|---|---|
| `api` | 原项目地址与登录账号（密码可用 `${ENV}` 引用） |
| `llm` | digest/对垒配对用的大模型（OpenAI 兼容；`extra_body` 可传 `reasoning_effort` 等供应商参数） |
| `data.ta_dir` | 原项目 `data/` 目录路径（replay/辩论的数据源） |
| `notify.channels` | `feishu.webhook` / 通用 `webhook.url` |
| `notify.report_url_prefix` | 卡片按钮指向的报告服务地址（手机访问填局域网 IP） |
| `cron.jobs` | 定时任务：`schedule` + `symbol` + `depth` + `pipeline` |

### 方式二：Docker 挂到已有部署

在 TradingAgents-CN 的部署目录（有 `docker-compose.hub.nginx.yml` 的那个）：

```bash
git clone https://github.com/frank-quant/TradingAgents-CN-studio.git
docker compose -f docker-compose.hub.nginx.yml \
               -f TradingAgents-CN-studio/docker/docker-compose.studio.yml up -d studio
```

- 加入原项目网络，经 `http://nginx` 访问 API，不依赖宿主机端口（报告服务除外，默认发布 `8890`）
- 原项目 `data/` 卷**只读**挂载，studio 产物写自己的卷
- 不想要了 `down studio` 即可，原项目无感

## 使用

```bash
studio doctor                                  # 自检
studio digest run --symbol 002594              # 提炼该股最近一次分析
studio digest run <task-id> / --file x.md      # 按任务 / 本地文件提炼
studio notify test                             # 向所有渠道发测试消息
studio notify send <task-id>                   # 推送简报卡片（带详情按钮）
studio compare run 002594 -m a,b,c --dry-run   # 对比（dry-run 只看计划）
studio replay debate <task-id>                 # 导出辩论回放（聊天流+对垒）
studio replay export <task-id>                 # 导出完整时间线回放
studio report serve --port 8890                # 报告详情服务（卡片按钮落点）
studio cron                                    # 常驻调度（容器里跑的就是它）
```

### 推送渠道配置

在 `studio.yaml` 的 `notify.channels` 下按需添加，**同时配多个全部生效**；键名支持 `渠道类型#别名` 让同一渠道推多个群：

| 渠道 | 配置项 | 在哪获取 |
|---|---|---|
| `feishu` | `webhook`（必填）、`secret`（开了签名校验才填） | 飞书群 → 设置 → 群机器人 → 添加**自定义机器人** |
| `dingtalk` | `webhook`（必填）、`secret`（安全设置选"加签"时必填） | 钉钉群 → 设置 → 智能群助手 → 添加**自定义**机器人 |
| `wecom` | `webhook`（必填） | 企业微信群 → 右键 → 添加**群机器人** |
| `telegram` | `token`、`chat_id`（必填）、`proxy`（国内网络需要） | `@BotFather` 创建 bot；拉入群后取 chat_id |
| `webhook` | `url`（必填） | 任意接收 `POST {title, body, markdown, buttons}` 的服务 |

```yaml
notify:
  channels:
    feishu:                 # 飞书主群
      webhook: https://open.feishu.cn/open-apis/bot/v2/hook/xxx
      secret: ""
    feishu#决策群:           # 同一渠道的第二个群（#后是别名）
      webhook: https://open.feishu.cn/open-apis/bot/v2/hook/yyy
    dingtalk:               # 钉钉群
      webhook: https://oapi.dingtalk.com/robot/send?access_token=zzz
      secret: SECxxx
```

配置后用一条命令验证（向所有渠道发测试消息，逐个报告成功/失败）：

```bash
studio notify test
```

> Telegram 在国内网络下需配置 `proxy`（如 `http://127.0.0.1:7897`）；飞书/钉钉/企微均使用群机器人 webhook，不需要创建企业应用。

### 定时推送

`studio.yaml` 的 `cron.jobs` 声明任务，调度器常驻后按 cron 表达式触发完整管道：

```yaml
cron:
  timezone: Asia/Shanghai
  jobs:
    - name: 早盘简报
      schedule: "30 9 * * 1-5"     # 工作日 09:30
      symbol: "002594"
      depth: 标准
      pipeline: [digest, notify]
```

之后每个工作日早上，飞书群会自动收到：**比亚迪(002594) 开盘前简报（中性）**，点按钮看全文或辩论回放。

## 开发

```bash
pip install -e ".[dev]"
pytest                    # 冒烟测试：配置/存储/SSE解析/签名/裁剪，不依赖运行中的原项目
```

目录结构：`src/studio/core`（共享地基：配置 / API 客户端 / SQLite / 事件模型 / 文本清洗），四个业务模块与之平级、互不依赖；`docker/` 为部署补丁；`tests/` 冒烟测试。

### 开发工具

本项目由 **ZCode**（AI 编程智能体，https://z.ai）驱动 **GLM-5.3**（智谱 BigModel）全程辅助开发：从原项目 API 逆向分析、四模块设计实现、真实数据联调（以一次完整的比亚迪分析作为验收样本）到移动端适配，均在人机协作下完成。

## 致谢

- [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) 及其上游 [TradingAgents](https://github.com/TauricResearch/TradingAgents)

## License

MIT
