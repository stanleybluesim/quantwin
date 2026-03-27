# 编号：SoT-GOV-NAMING-20260327-01
# 版本：V2.7
# 状态：EFFECTIVE
# artifact_class: GovernanceRule
# primary_key: SoTFileNamingConvention
# document_id: SoT-GOV-NAMING-20260327-01

# QuantWin SoT 文件命名规范 (V2.7)

## 0. 治理字段 (Governance Fields)
* **Owner**: QuantWin Architecture Team
* **Accountable Owner**: Stanleybluesim
* **Output Path**: `sot/governance/QuantWin_SoT_GovernanceRule_SoTFileNamingConvention_v2.7.md`
* **进入条件**: 
  1. 本文稿经 Accountable Owner 签字确认。
  2. 基线 `QuantWin_AEF_OpenClaw_Baseline_Ledger_v0.2_fixed_revised.md` 已落库。
* **退出条件**: 
  1. 所有新增 SoT 文件遵循本命名规则。
  2. 既有文件迁移计划已制定。
  3. 迁移完成后，主线引用 MUST 指向新路径。
* **验收命令**: 
  ```bash
  FILE="sot/governance/QuantWin_SoT_GovernanceRule_SoTFileNamingConvention_v2.7.md"
  # 1. 文件存在性检查
  test -f "$FILE"
  # 2. 文件名与版本一致性检查
  basename "$FILE" | grep -E '^QuantWin_SoT_GovernanceRule_SoTFileNamingConvention_v2\.7\.md$'
  # 3. 内部元数据一致性检查 (V2.7 修复：状态值与 Header 一致)
  grep -E '^# 版本：V2.7$|^# 状态：EFFECTIVE$' "$FILE"
  # 4. 核心治理字段精确检查
  grep -E '^# artifact_class: GovernanceRule$|^# primary_key: SoTFileNamingConvention$|^# document_id: SoT-GOV-NAMING-20260327-01$' "$FILE"
  # 5. 治理默认值检查
  grep -E 'formal_acceptance = NOT_ASSERTED|runtime_publish_state = NOT_ASSERTED|trace_id =|run_id =|audit_id =|report_id =' "$FILE"
  # 6. 治理字段完整性检查 (V2.7 扩展：覆盖 G9 全部必备字段)
  grep -E '^\* \*\*Owner\*\*:|^\* \*\*Accountable Owner\*\*:|^\* \*\*Output Path\*\*:|^\* \*\*进入条件\*\*:|^\* \*\*退出条件\*\*:|^\* \*\*验收命令\*\*:|^\* \*\*不可外推声明\*\*:|^\* \*\*不得混写为\*\*:' "$FILE"
  ```
* **不可外推声明**: 本规范仅约束工件存储标识，不代表任务已执行/已验收/已上线。
* **不得混写为**: 
  1. 不得混写为 `FORMALLY_ACCEPTED` 状态。
  2. 不得混写为 `runtime current-live state changed` 状态。
  3. 不得混写为 `WP-P1-4` 任务执行证据。

## 1. 文档定位 (Positioning)
本文件是 QuantWin 项目内正式 SoT (Source of Truth) 工件的定名与存储规则。
本文件生效后：
- 新增正式 SoT 文件 **MUST** 遵循本规则。
- 既有正式 SoT 文件在发生改名或迁移时 **MUST** 遵循本规则。
- 本文件本身属于 `GovernanceRule` 类 SoT 工件。
- 本文件不改变任何运行时当前生效状态，不构成运行时发布动作。

## 2. 适用范围 (Scope)
### 2.1 适用对象
本规则适用于 QuantWin 项目内以下正式 SoT 文件类别 (`ArtifactClass`)：
- `BaselineEntry` (基线入口)
- `TaskRegistration` (任务注册)
- `FreezeRecord` (冻结记录)
- `UpgradeDecision` (升级裁决)
- `AcceptanceDecision` (验收决策)
- `GovernanceRule` (治理规则)

### 2.2 不适用对象
以下对象 **MUST NOT** 直接按本规则落库为正式 SoT：
- 草案 (Drafts)
- 临时对话导出 (Temp Exports)
- 证据清单草稿 (Evidence Drafts)
- 未锁定 `PrimaryKey` 的候选文本
- 尚未形成正式治理边界的讨论稿

### 2.3 与既有治理边界的一致性
本规则 **MUST** 与以下治理边界保持一致：
- 工件变更与运行时发布动作 **MUST** 分离。
- 正式 SoT 命名变更 **MUST NOT** 被写成运行时已切换 / 已生效 / 已上线。
- 建议新增 ID / `PROPOSED-*` / 临时标签 **MUST NOT** 因命名规则落库而被上推为既成事实。
- 文件名 **MUST NOT** 包含暗示运行时状态的词汇（如 `Live`, `Prod`, `Active`, `Running`）。

## 3. 命名语法 (Naming Syntax)
### 3.1 正式语法
所有正式 SoT 文件名 **MUST** 采用以下格式（区分大小写，下划线分隔）：
`QuantWin_SoT_<ArtifactClass>_<PrimaryKey>_[vV]<Version>.md`

### 3.2 字段定义
| 字段 | 定义 | 示例 | 约束 |
| :--- | :--- | :--- | :--- |
| `QuantWin_SoT_` | 固定前缀 | `QuantWin_SoT_` | 不可修改，标识项目与文件类型 |
| `<ArtifactClass>` | 工件类别 | `GovernanceRule` | 必须来自 2.1 节定义的枚举值 |
| `<PrimaryKey>` | 主键标识 | `SoTFileNamingConvention` | **必须稳定**，不含日期/时间戳，唯一标识业务对象 |
| `[vV]<Version>` | 版本号 | `v2.7`, `V3` | **兼容大小写**，必须与内部元数据 `版本` 一致 |
| `.md` | 扩展名 | `.md` | 必须为 Markdown 格式 |

### 3.3 版本控制规则
- **初始版本**：`v1.0` 或 `V1`。
- **内容修正**：`v1.1`, `v1.2` (不改变任务边界/契约)。
- **结构变更**：`v2.0`, `V3`, `V4`, `V5`, `V6`, `V7` (边界/契约重大变更，**MUST** 重新签字)。
- **弃用**：旧版本文件 **MUST NOT** 删除，应标记为 `DEPRECATED` 并保留在 `sot/archive/`。

### 3.4 示例
- **合法**: `QuantWin_SoT_GovernanceRule_SoTFileNamingConvention_v2.7.md`
- **合法**: `QuantWin_SoT_TaskRegistration_WP-P1-4_V3.md` (兼容既有大写 V)
- **非法**: `QuantWin_SoT_TaskRegistration_WP-P1-4_20260327_v1.0.md` (主键含日期)
- **非法**: `QuantWin_SoT_TaskRegistration_WP-P1-4_Final.md` (含误导词)

## 4. 存储与迁移 (Storage & Migration)
### 4.1 目标路径
所有正式 SoT 文件 **MUST** 存储于项目根目录下的 `sot/` 分区（repo-relative）：
- `sot/baseline/` : 存放 `BaselineEntry`
- `sot/tasks/` : 存放 `TaskRegistration`
- `sot/governance/` : 存放 `GovernanceRule`, `FreezeRecord`, `UpgradeDecision`
- `sot/acceptance/` : 存放 `AcceptanceDecision`
- `sot/archive/` : 存放 `DEPRECATED` 旧版本

### 4.2 迁移规则
- 既有文件在下次变更时 **MUST** 重命名以符合本规则。
- 迁移过程中 **MUST** 保留原文件副本至 `sot/archive/` 至少 90 天。
- **迁移期兼容**：旧路径文件在迁移期内仍可被引用，但新文件 MUST 使用新路径。
- **归档约束**：
  - Archive 版 **MUST** 显式标记 `DEPRECATED`。
  - Archive 版 **MUST NOT** 继续作为当前有效 SoT 引用源。
  - 迁移完成后，主线引用 **MUST** 指向新路径。
  - 迁移完成后，自动化检查与主线引用 **SHOULD** 仅指向新路径，不再把 archive 版作为当前有效规则对象。
- 迁移不改变文件内容语义，仅调整标识与路径。

## 5. 元数据与审计 (Metadata & Audit)
### 5.1 元数据一致性 (Metadata Consistency)
- **文件名承载字段**：`ArtifactClass` / `PrimaryKey` / `Version` **MUST** 与文件名一致。
- **正文承载字段**：`编号 (document_id)` / `状态 (status)` **MUST** 与正文 Header 元数据一致。
- **主键定义**：
  - `document_id` = 文档实例 ID (逻辑主键，如 `SoT-GOV-NAMING-20260327-01`)
  - `primary_key` = 被治理对象键 (业务主键，如 `SoTFileNamingConvention`)
  - 文件名 = 物理索引表示 (派生自上述两者)
- **不一致处置**：若文件名版本与正文版本不一致，审计 **MUST** 触发 `SOT-NAME-003 VERSION_MISMATCH` 告警。

### 5.2 审计错误码
| 错误码 | 含义 | 处置 |
| :--- | :--- | :--- |
| `SOT-NAME-001` | INVALID_ARTIFACT_CLASS | 拒绝落库，修正类别 |
| `SOT-NAME-002` | PRIMARY_KEY_MISSING | 拒绝落库，补充主键 |
| `SOT-NAME-003` | VERSION_MISMATCH | 触发告警，同步版本 |
| `SOT-NAME-004` | ILLEGAL_FILENAME_TOKEN | 拒绝落库，移除误导词 |

### 5.3 链路追踪 (Traceability)
- 所有 SoT 文件 **MUST** 在内部元数据中包含 `trace_id` 或 `audit_id`。
- 变更日志 **MUST** 记录在 `QuantWin_SoT_Change_Log.md` 中，关联 `run_id`。
- **例外规则**：对于 GovernanceRule 类 docs-only 文件，trace_id / audit_id 可在 Header 或 Signature Section 落字；若无独立审计事件则统一写 N/A。

## 6. 治理默认值 (Governance Defaults / C-7)
*本文件作为治理规则，其默认治理语义定义如下：*
- `formal_acceptance = NOT_ASSERTED` (直至验收命令执行完毕)
- `runtime_publish_state = NOT_ASSERTED` (本文件不触发运行时切换)
- `trace_id = N/A` (unless separate naming audit is recorded)
- `run_id = N/A` (for docs-only rule landing)
- `audit_id = N/A` (unless audit event is separately recorded)
- `report_id = N/A` (unless report-chain evidence is included)
- `retry_policy = no_automatic_retry` (人工确认制)
- `timeout_policy = fail_closed_on_command_timeout`
- `async_semantics = not_applicable_docs_only`
- **补充说明**：对于 GovernanceRule 类 docs-only 文件，trace_id / audit_id 若无独立审计事件则统一写 N/A。

## 7. 签字确认区 (Signature Section)
- [x] 我已阅读并确认上述治理字段与命名规则完整且准确。
- [x] 我授权此规范作为正式 SoT 治理规则落库。
- **confirmed_by (Accountable Owner)**: Stanleybluesim
- **confirmed_at**: 2026-03-27 00:00:00
- **signature_status**: EFFECTIVE
- **trace_id / audit_id**: N/A