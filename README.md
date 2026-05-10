# Dev Agent Prilot

一个可落地的 AI 研发助理项目：读取 Issue / 工单描述，检索本地代码仓库上下文，调用 GPT 系列模型生成修复方案、统一 diff patch、测试建议和 PR 文案。适合放到 GitHub 作为“使用 Agent 或 AI 驱动构建的具体成果”。

> 定位：工程师辅助工具，不是无人值守自动合并机器人。它会生成 patch 和 PR 草稿，但默认不直接改代码，除非你显式加 `--apply`。

## 功能

- 从本地仓库读取代码树和相关文件上下文
- 根据 Issue / Bug 描述生成：
  - 问题摘要
  - 修改计划
  - unified diff patch
  - 测试命令建议
  - 风险点
  - PR 标题和 PR 描述
- 支持 dry-run 和自动应用 patch
- 支持运行测试命令并返回测试结果
- 提供 CLI 和 FastAPI 两种使用方式
- 内置单元测试、CI、Dockerfile、Makefile

## 目录结构

```text
dev-agent-prilot/
├── src/issuefix_agent/       # 核心 Agent 代码
├── tests/                    # 单元测试
├── examples/                 # 示例 issue
├── docs/                     # 架构说明
├── .github/workflows/ci.yml  # GitHub Actions
├── pyproject.toml            # Python 项目配置
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

## 快速开始

### 1. 安装

```bash
git clone <your-repo-url>
cd dev-agent-prilot
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY
```

`.env` 示例：

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.2
```

### 3. 对一个仓库执行分析

```bash
issuefix-agent analyze \
  --repo /path/to/your/repo \
  --issue-file examples/issue.md \
  --test-command "pytest"
```

默认只输出方案和 patch，不修改代码。

### 4. 应用 patch

```bash
issuefix-agent analyze \
  --repo /path/to/your/repo \
  --issue-file examples/issue.md \
  --apply \
  --test-command "pytest"
```

### 5. 启动 API 服务

```bash
uvicorn issuefix_agent.api:app --reload
```

请求示例：

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "repo_path": "/path/to/your/repo",
    "issue_text": "修复登录接口在 token 过期时返回 500 的问题",
    "apply_patch": false,
    "test_command": "pytest"
  }'
```

## CLI 命令

```bash
issuefix-agent analyze --help
issuefix-agent tree --repo /path/to/repo
issuefix-agent search --repo /path/to/repo --query "token expired"
```

## 设计原则

1. **默认安全**：默认 dry-run，不直接改代码。
2. **上下文可控**：只读取必要文件，限制上下文大小，避免把整个仓库塞进模型。
3. **人类审查优先**：生成的 diff 必须由工程师 review。
4. **可替换模型层**：LLM 调用封装在 `llm.py`，后续可以接 Claude、Gemini、DeepSeek、本地模型或企业内网模型。

## 适合作为表单里的“具体成果”描述

我基于 GPT 系列模型构建了一个研发工单自动分析与代码修复 Agent。它可以读取 Issue、错误日志和本地代码仓库上下文，自动定位相关文件，生成修复计划、unified diff patch、测试建议和 PR 文案。核心流程覆盖“理解问题—检索代码—生成修改—运行校验—输出 PR 草稿”。项目提供 CLI 和 FastAPI 两种使用方式，默认 dry-run，只有显式启用时才会应用 patch，确保工程师保持最终控制权。

## 注意事项

- 不要把 `.env` 或 `OPENAI_API_KEY` 提交到 GitHub。
- 第一次接入真实仓库时，请先只使用 dry-run。
- 对安全、支付、权限、数据迁移等高风险代码，不要让 Agent 自动应用 patch。
- 生成结果可能错误；必须 code review。

## License

MIT
