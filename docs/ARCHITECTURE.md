# Architecture

Dev Agent Prilot 分成四层：

## 1. Repository Layer

`repo.py` 负责读取本地仓库：

- 遍历代码树
- 忽略 `.git`、`node_modules`、`dist`、`.venv` 等目录
- 根据 Issue 中的关键词检索相关文件
- 限制单文件和总上下文长度

这一层不调用模型，便于测试。

## 2. Prompt Layer

`prompts.py` 负责把 Issue、代码树、相关文件上下文整理成稳定提示词。

要求模型输出 JSON，字段包括：

- `summary`
- `plan`
- `patch`
- `tests`
- `risks`
- `pr_title`
- `pr_body`

## 3. LLM Layer

`llm.py` 封装模型调用。默认使用 OpenAI Responses API。

后续如果要切换 Claude、Gemini、DeepSeek 或内部模型，只需要实现同样的 `LLMClient` 接口。

## 4. Orchestration Layer

`agent.py` 编排完整流程：

1. 读取 Issue
2. 检索仓库上下文
3. 调用模型生成方案
4. 解析 JSON
5. 可选：应用 patch
6. 可选：运行测试
7. 返回结构化结果

## Safety Boundaries

- 默认不应用 patch。
- 应用 patch 前使用 `git apply --check` 做校验。
- 测试命令由用户显式传入。
- 不自动提交、不自动 push、不自动 merge。

## Future Work

- GitHub App 集成：自动读取 issue、评论 PR 草稿
- 多 Agent 协作：Planner / Coder / Reviewer / Tester
- 更精确的 AST 索引
- 失败测试的自动二轮修复
- 审计日志和 token 成本统计
