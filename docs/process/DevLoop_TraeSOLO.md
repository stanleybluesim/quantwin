# DevLoop Specification (TraeSOLO Edition)

## 1. 核心理念 (Core Philosophy)

QuantWin 的开发流程遵循 **DevLoop** 闭环模型，结合 **TraeSOLO** 单人全栈开发模式，强调以下原则：
- **Evidence-Based**: 任何改动必须有证据（日志、截图、测试报告）。
- **Gate-Driven**: 本地门禁（Local Gate）必须通过才能提交 PR。
- **Task-Centric**: 一切工作始于 Task，终于 PR。

## 2. 工作流 (Workflow)

### 2.1 任务定义 (Task Definition)
每个任务（Task）应有一个唯一的 ID（如 `TK-YYYYMMDD-TOPIC-001`）。
在开始编码前，必须明确：
- **Goal**: 目标是什么？
- **Must-Haves**: 必须满足的验收标准。
- **Plan**: 初步的 Todo List。

### 2.2 分支管理 (Branching)
- **Base Branch**: 通常是 `main`。
- **Feature Branch**: 格式 `type/task-id-desc` (e.g., `feat/auth-login-flow`, `docs/devloop-traesolo`).
- **Commit Message**: 遵循 Conventional Commits (e.g., `feat(auth): implement login`).

### 2.3 开发循环 (The Loop)
1.  **Checkout**: 从最新 `main` 切出分支。
2.  **Todo**: 创建/更新 Todo List。
3.  **Code**: 编写代码与测试 (Red-Green-Refactor)。
4.  **Verify**: 运行本地验证脚本 (`scripts/validate_*.sh`, `pytest`).
5.  **Evidence**: 收集运行结果到 `Evidence/<TaskID>/` 目录。

### 2.4 提交与评审 (Commit & Review)
- 确保所有本地门禁通过。
- 生成 Evidence 包。
- 提交 PR，并在 Body 中附上 Evidence 路径或摘要。
- 如果 CI 失败，修复后重新生成 Evidence 并更新 PR。

## 3. 证据标准 (Evidence Standards)

Evidence 目录结构示例：
```
Evidence/TK-20260130-DEVLOOP-001/
├── git_status.txt       # 提交前的状态
├── validate_docs.log    # 文档检查日志
├── pytest.log           # 测试运行日志
└── summary.md           # 简要说明
```

## 4. 常用命令 (Cheatsheet)

```bash
# 1. Start Task
git checkout main && git pull
git checkout -b feat/my-feature

# 2. Run Gates
bash scripts/preflight.sh
bash scripts/validate_docs.sh

# 3. Capture Evidence
mkdir -p Evidence/TK-MyTask
bash scripts/preflight.sh | tee Evidence/TK-MyTask/preflight.log

# 4. Commit
git add .
git commit -m "feat: my feature"
```

## 5. 工具链 (Toolchain)
- **Trae**: IDE & AI Assistant.
- **Pytest**: Testing Framework.
- **Scripts**: `scripts/` 目录下的自动化脚本。
