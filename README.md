```markdown
# 🔮 OpenOracle — 公开AI预测系统

> 让预测在阳光下运行，让AI在监督中成长。

OpenOracle 是一个**透明、可证伪、可解释**的公开预测基础设施。它不是一个神秘的黑箱先知，而是一个允许任何人提问、任何人验证、社区共同校准的公共知识工具。

---

## ✨ 核心原则

| 原则 | 含义 |
|------|------|
| **可回溯性** | 所有预测都可追溯到原始证据和推理路径 |
| **可证伪性** | 每个预测都有明确的结算条件，失败会被记录 |
| **可解释性** | 多智能体（MAP-REDUCE）协同推理，过程透明 |
| **透明性** | 全流程开源，日志结构化公开 |
| **反审查** | 不隐藏失败预测，失败是进化的养料 |

---

## 🧱 系统架构

```

用户提问 → 问题DNA编码 → 预测引擎 (MAP-REDUCE) → 许可证神谕 → 社区校准 → 证据链构建 → 上链存证
↓ 拒绝
返回原因+上诉通道

```

| 层级 | 组件 | 说明 |
|------|------|------|
| 数据层 | IPFS + 区块链存证 | 证据与预测不可篡改 |
| 逻辑层 | MAP-REDUCE-AGENT | 多智能体分解与证据融合 |
| 接口层 | REST API + Web3 前端 | 标准 OpenAPI 接口 |
| 治理层 | DAO + 进化护栏 | 社区多数投票，不可变原则保护 |

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/chene2603-cmd/chen.git
cd chen/openoracle-genesis
```

2. 使用 Docker 一键启动（推荐）

```bash
# 开发模式（API + 本地链 + IPFS）
chmod +x scripts/start_oracle.sh
./scripts/start_oracle.sh dev

# 部署智能合约到本地链
./scripts/start_oracle.sh deploy

# 生产模式（含 Nginx 反向代理）
./scripts/start_oracle.sh prod
```

3. 本地 Python 启动（开发调试）

```bash
# 安装依赖
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 启动 API
uvicorn src.api.app:app --reload
```

访问 http://localhost:8000/docs 查看 Swagger 文档并直接测试。

---

📡 API 端点概览

方法 路径 说明
POST /api/v1/predict 提交预测问题，获取完整预测结果
POST /api/v1/community/feedback 提交社区反馈（校准数据）
POST /api/v1/governance/propose 创建治理提案
GET /api/v1/governance/votes 查看所有投票状态
GET /health 服务健康检查

---

🧠 预测示例

请求：

```json
{
  "question": "2026年比特币价格会突破10万美元吗？",
  "source": "user_submitted"
}
```

响应（简化）：

```json
{
  "status": "APPROVED",
  "prediction": {
    "prediction_id": "P...",
    "question_id": "Q...",
    "probability": 0.72,
    "calibrated_probability": 0.68,
    "confidence_interval": [0.62, 0.78],
    "consensus_strength": 0.85,
    "reasoning": "基于历史类比和因果链分析...",
    "evidence_chain": {
      "type": "DIRECTED_ACYCLIC_GRAPH",
      "nodes": [...],
      "edges": [...]
    },
    "calibration": {
      "feedback_count": 5,
      "calibration_confidence": 0.9,
      "majority_reasoning": "证据较充分，但需考虑监管风险"
    }
  }
}
```

---

🛠 项目结构

```
openoracle-genesis/
├── blueprint/                # 原始蓝图设计文档
├── src/
│   ├── core/                 # 核心引擎（问题处理、预测、神谕等）
│   ├── contracts/            # Solidity 智能合约
│   ├── governance/           # DAO 投票与进化护栏
│   ├── api/                  # FastAPI 应用与路由
│   └── utils/                # 日志、配置等工具
├── ui/
│   ├── web/                  # 前端界面
│   └── cli/                  # 命令行工具
├── tests/                    # 单元测试与压力测试
├── scripts/                  # 部署与启动脚本
├── config/                   # 配置文件
├── docs/                     # 文档
├── docker-compose.yaml
├── Dockerfile
└── requirements.txt
```

---

🧪 运行测试

```bash
# 单元测试（不需要服务运行）
pytest tests/test_core.py -v

# 集成测试（需先启动服务）
pytest tests/test_stress.py -v --integration
```

---

🔒 不可变原则

以下原则被编码在系统 DNA 中，任何人都无法修改或删除，任何试图改变这些原则的提案都会被进化护栏自动拒绝：

1. 透明性 — 全流程公开
2. 可证伪性 — 所有预测可被事实检验
3. 开源 — 代码永远公开
4. 反审查 — 失败预测不隐藏

---

🤝 贡献

OpenOracle 是一个社区驱动的项目，欢迎提交 Issue、PR 或参与 DAO 治理投票。

---

📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

```

---

## 2. `docs/API_REFERENCE.md`

```markdown
# OpenOracle API 参考文档

**Base URL:** `http://localhost:8000/api/v1`

---

## 1. 提交预测问题

```

POST /predict

```

**描述**  
提交一个自然语言问题，经过完整管道（问题编码 → MAP‑REDUCE预测 → 许可证检查 → 社区校准 → 证据链构建）后返回预测结果。

**Request Body** (JSON)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `question` | string | 是 | 预测问题文本，如“2026年比特币价格会突破10万美元吗？” |
| `source` | string | 否 | 问题来源，可选值：`user_submitted`（默认）、`trend_analysis`、`expert_curated` |

**示例请求**
```json
{
  "question": "SpaceX在2026年会完成多少次星舰发射？",
  "source": "user_submitted"
}
```

Response
200 OK 时返回 PredictionResponse 对象。

字段 类型 说明
status string "APPROVED" 或 "REJECTED"
prediction object 预测详情（仅在 APPROVED 时完整）
message string 拒绝原因（仅在 REJECTED 时）

prediction 对象字段

字段 类型 说明
prediction_id string 预测唯一ID，以 P 开头
question_id string 问题ID，以 Q 开头
timestamp string ISO8601 时间戳
probability float 原始预测概率 (0–1)
calibrated_probability float 社区校准后概率
confidence_interval [float, float] 置信区间
uncertainty float 不确定性 (0–1)
consensus_strength float 智能体共识强度
agent_count int 参与分析的智能体数量
reasoning string 综合推理文本
evidence_chain object 证据链 DAG 结构
calibration object 校准报告（反馈数、因子等）

错误码

状态码 说明
400 请求格式错误（如问题过短）
500 内部管道异常

---

2. 提交社区反馈

```
POST /community/feedback
```

描述
提交对某个预测的评分、理由和新证据，用于社区校准回路。

Request Body

字段 类型 必填 说明
prediction_id string 是 要评价的预测ID
user_id string 是 用户标识
scores object 是 各维度得分 (0–1)，如 {"evidence_support": 0.9}
reasoning string 是 反馈理由
new_evidence list 否 新证据列表，每项可含 content 和 source

示例请求

```json
{
  "prediction_id": "P123abc",
  "user_id": "alice",
  "scores": {
    "evidence_support": 0.85,
    "reasoning_clarity": 0.7
  },
  "reasoning": "证据充分，但缺少对监管因素的考虑",
  "new_evidence": [
    {
      "content": "最新SEC文件显示...",
      "source": "https://sec.gov/..."
    }
  ]
}
```

Response

```json
{
  "status": "received",
  "message": "反馈已记录"
}
```

---

3. 创建治理提案

```
POST /governance/propose
```

描述
发起一个系统变更提案，自动进入DAO投票流程。不可变原则（透明、可证伪等）的修改会被直接拒绝。

Request Body

字段 类型 必填 说明
title string 是 提案标题
description string 是 提案描述
modifications list 是 预期修改的模块/原则列表
author string 是 提案者标识

示例请求

```json
{
  "title": "新增气候预测智能体",
  "description": "在MAP阶段增加专门分析气候数据的智能体。",
  "modifications": ["prediction_engine"],
  "author": "core_dev"
}
```

Response
成功时返回：

```json
{
  "status": "PROPOSED",
  "vote_id": "VOTE-ABCD1234"
}
```

若触及不可变原则，返回 403：

```json
{
  "detail": "原则 'transparency' 是不可变的，任何人无权修改。"
}
```

---

4. 查询投票状态

```
GET /governance/votes
```

描述
获取系统内所有投票的当前状态。

Response
返回投票列表：

```json
[
  {
    "vote_id": "VOTE-ABCD1234",
    "title": "新增气候预测智能体",
    "is_finalized": false,
    "deadline": "2026-05-14T12:00:00Z",
    "result": null
  },
  {
    "vote_id": "VOTE-XYZ9999",
    "title": "调整不确定性阈值",
    "is_finalized": true,
    "deadline": "2026-04-30T00:00:00Z",
    "result": {
      "passed": true,
      "winner": "APPROVE",
      "winner_ratio": 0.72
    }
  }
]
```

---

5. 健康检查

```
GET /health
```

Response

```json
{
  "status": "ok",
  "service": "OpenOracle"
}
```

```