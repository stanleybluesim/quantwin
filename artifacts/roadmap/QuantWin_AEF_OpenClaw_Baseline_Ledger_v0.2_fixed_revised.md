# QuantWin AEF OpenClaw Baseline Ledger V0.2-fixed

## 1. 文档元数据

| 字段 | 值 |
|---|---|
| Document Name | `QuantWin_AEF_OpenClaw_Baseline_Ledger` |
| Version | `v0.2-fixed` |
| Status | `Ready for Landing Review` |
| Owner | `PM / AR` |
| Reviewer | `QA / GOV` |
| Approval State | `Pending Landing Review` |
| Effective Scope | `拟作为 QuantWin / AEF / OpenClaw 当前阶段正式基线入口文件首版` |
| Current Baseline Entry ID | `BL-ENTRY-001` (`PROPOSED`) |
| Lock Timestamp | `2026-03-24` |
| Lock Basis | `本文件仅依据本轮锁定 SoT 收束当前全局阶段、OpenClaw 阶段、专题阶段、当前工作优先级与禁止外推范围` |

### 1.1 Landing Criteria

本文件仅当以下门禁全部满足时，方可由 `Ready for Landing Review` 变更为落库通过状态：

| Gate | 通过标准 |
|---|---|
| G6 正式入口文件状态口径 | 正文、定位、摘要不再同时出现“待评审”与“已成立”双语义 |
| G7 SoT 锁定表达自包含 | 不查看附注也能在正文主段唯一识别当前状态层锁定对象 |
| G8 Traceability proposed 语义控制 | 全文不再出现把 proposed / 临时语义上推为正式注册事实的表述 |
| G9 P0 / P1 任务清单裁决性 | 每条 P0 / P1 条目均包含来源 SoT、Owner、Accountable Owner、Output Path、进入条件、退出条件、验收命令、不可外推声明 |
| G10 首版正式入口文件完整性 | Markdown 结构完整闭合；正文完整覆盖至 13 节；无截断、无未闭合代码块 |
| G11 禁止外推范围显式化 | 正文显式给出“不得外推为”与“不得混写”两组规则 |
| G12 Traceability / 维护约束 / 一句话摘要 | 正文显式给出 12 Traceability、变更触发规则、维护约束、13 当前基线一句话摘要 |
| G13 禁用路径约束 | 全文不得出现受本轮审计强制约束禁止的路径命名空间 |

---

## 2. 文档定位

本文件拟作为 QuantWin / AEF / OpenClaw 当前阶段的正式基线入口文件首版。  
其用途是统一回答以下问题：

1. 当前全局阶段是什么  
2. 当前 OpenClaw 阶段是什么  
3. 当前专题阶段是什么  
4. 当前 SoT 应按什么顺序裁决  
5. 当前工作优先级是什么  
6. 哪些结论禁止外推  

本文件不替代上游 SoT。  
本文件只负责对上游 SoT 做当前阶段收束、归档与裁决入口统一。

---

## 3. 采用的 SoT

### 3.1 总体治理层
- `AEF 协议：生产级 AI 自主开发最终 operational 版 (V10.4 Final Operational Edition).md`

### 3.2 边界裁决层
- `ADR-AEF-015：AEF–QuantWin 集成边界规范.md`

### 3.3 正式规范层
- `Architecture Spec (AS) v5.0-7.1 — QuantWin .pdf`

### 3.4 当前状态层
- `AEF Phase 0 实施.txt`
- `《QuantWin 专题工作启动.txt》— 2026-03-24 锁定版本（用于 devloop ChatGPT/Qwen specialist 专题当前状态裁决）`

### 3.5 当前状态层锁定表达
本文件当前状态层的专题现态裁决，**只以**以下对象为准：

> `《QuantWin 专题工作启动.txt》— 2026-03-24 锁定版本（用于 devloop ChatGPT/Qwen specialist 专题当前状态裁决）`

内部版本索引仅用于附注复核，不作为正文主锁定表达。

---

## 4. 术语与裁决口径

### 4.1 术语定义
- **工程收口**  
  指专题对应的 PR、分支、主线同步、边界整改等工程治理动作已完成，但不自动等于正式验收完成。
- **工件落库**  
  指验证记录、Traceability 工件或其他治理工件已正式进入仓库并具备可追溯性。
- **正式验收**  
  指正式门槛已满足，并可在项目记录中明确表述为“正式验收完成”。
- **运行时发布**  
  指运行时当前生效策略、发布态、上线态发生变化；该状态不得由工程治理层结论直接外推。
- **FORMAL_ACCEPTANCE_REVIEW_READY**  
  指正式验收前置工件已补齐、证据已满足复核前提，但尚未正式表述为“正式验收完成”。

### 4.2 基本裁决规则
1. 专题当前状态，不得由总体协议直接替代。  
2. 工程治理层结论，不得外推为运行时已切换 / 已生效 / 已上线。  
3. 建议新增对象、建议新增 ID、临时标签，不得写成正式注册事实。  
4. 同名文件若存在多版本，必须先锁定唯一版本，再进入状态裁决。  
5. 当前状态层的锁定表达必须在正文主段可读、可裁决、可复核。  

---

## 5. SoT 分层与裁决顺序

### 5.1 分层定义
- **L1：总体治理层**  
  负责总体路线图、阶段划分、治理原则。
- **L2：边界裁决层**  
  负责 AEF / QuantWin 分层边界、运行时发布边界、SoT 分工。
- **L3：正式规范层**  
  负责 API / Schema / Traceability / Metrics / Tests / C-7 等正式结构。
- **L4：当前状态层**  
  负责当前阶段、当前专题、当前收口状态与未完成项。

### 5.2 裁决顺序
#### 当前专题状态问题
`L4 → L2 → L3 → L1`

#### 分层边界问题
`L2 → L3 → L1 → L4`

#### 正式规范结构问题
`L3 → L2 → L1 → L4`

#### 总体路线图问题
`L1 → L2 → L3 → L4`

---

## 6. 当前全局阶段

### 6.1 全局阶段结论
当前全局阶段为：

**AEF Phase 0 已完成；项目处于 Phase 0 完成后的过渡阶段。**

### 6.2 已确认事项
- AEF Phase 0 已全部闭环完成。
- 当前不再继续执行 Phase 0 收口命令。

### 6.3 当前未完成事项
- AEF Phase 1~5 尚未形成项目内正式推进闭环。
- 本轮锁定 SoT 未提供单一路线图入口文件。

---

## 7. 当前 OpenClaw 阶段

### 7.1 当前阶段结论
OpenClaw 当前处于：

**主机层可用，但模型层仍未打通。**

### 7.2 已确认事项
- 宿主与主机侧基础能力已通过基础可用性检查。

### 7.3 当前阻塞项
以下阻塞项未清除前，不得宣称已进入“AEF 约束下自主编程闭环”阶段：
- 无可用 provider
- 无 primary/default model
- 无可用 API key
- 无真实 agent turn smoke 证据

### 7.4 当前阶段语义
当前阶段只能表述为：
- OpenClaw 基础宿主层已具备前置条件
- OpenClaw 模型层仍 BLOCKED
- 尚未进入自治编程闭环实施阶段

不得表述为：
- OpenClaw 已具备完整自主编程能力
- OpenClaw 已在 AEF 约束下完成自治闭环
- OpenClaw 已可替代运行时发布链路

---

## 8. 当前专题阶段矩阵

### 8.1 锁定专题
当前锁定专题为：

`devloop ChatGPT/Qwen specialist`

### 8.2 适用范围
本节结论**仅适用于** `devloop ChatGPT/Qwen specialist` 子专题。  
本节结论**不适用于** 其他专题、全仓正式验收结论、或运行时发布状态判断。

### 8.3 当前专题正式状态
本专题当前正式状态只能表述为：

**已完成工程收口；待补专题级验证记录与 Traceability 工件落库后，可标记为正式验收完成。**

### 8.4 当前已确认事项
- 专题 PR 已合并
- 本地与远端专题分支已清理
- `main` 已与 `origin/main` 对齐
- 本专题未回流 PR #23
- 本专题未重新打开 AEF Phase 0

### 8.5 当前未直接确认事项
因本轮锁定 SoT 未见以下事项的直接落库证据，所以下列状态维持“未直接确认”：

- 专题级验证记录已完整落库
- Traceability 工件已正式落库

### 8.6 中间状态
当 `8.5` 所列两项全部补齐，并完成与正式规范结构的映射后，本专题可进入：

**`FORMAL_ACCEPTANCE_REVIEW_READY`**

该状态表示：
- 已具备正式验收复核前置条件
- 尚不等于“正式验收完成”

状态迁移链如下：

`工程收口完成 → FORMAL_ACCEPTANCE_REVIEW_READY → 正式验收完成`

### 8.7 正式验收阻断语句
在 `8.5` 所列事项未直接确认前，**不得**写：
- 本专题已正式验收完成
- 本专题已正式闭环验收
- 本专题已完成正式 Traceability 落库并注册

### 8.8 当前专题禁止上推的结论
不得直接写为：
- 本专题已正式验收完成
- 本专题 Traceability 已代表 QuantWin 全仓完成
- 本专题结论可自动外推到其他专题
- 本专题工件结论已证明运行时当前生效状态已切换

---

## 9. 当前正式规范约束

### 9.1 MUST 映射的正式结构
当前所有后续专题级验证记录与 Traceability 工件 MUST 映射到：
- `Traceability Matrix`
- `Metric Specifications`
- `Test Specifications & Gates`

### 9.2 MUST 维护的 C-7 字段
跨层对象 MUST 挂接以下最小追溯字段：
- `run_id`
- `audit_id`
- `trace_id`
- `report_id`（仅报告导出链路适用）

### 9.3 MUST 维护的边界
- AEF = 工程治理层
- QuantWin = 业务运行层
- FastStream = 唯一异步通信层
- 异步消息 MUST 通过已登记 `Topic`
- 异步消息 MUST 携带 `idempotency_key`
- 工件变更与运行时发布动作 MUST 分离

---

## 10. 当前工作优先级清单

> 本节中的 P0 / P1 仅表示**当前工作优先级**，不表示 AEF Phase 已自动切换。

### 10.1 当前工作优先级 P0

#### WP-P0-1 OpenClaw 模型层阻塞清除
- **来源 SoT**  
  `AEF 协议 V10.4`；本文件 `§7 当前 OpenClaw 阶段`
- **Owner**  
  `AR / AD / SRE`
- **Accountable Owner**  
  `AR`
- **排序依据**  
  当前唯一功能性硬阻塞；不清除则无法进入真实 agent turn 与自治编程闭环准备。
- **进入条件**  
  OpenClaw 仍处于“主机层可用，但模型层仍未打通”。
- **退出条件**  
  同时满足以下 4 项：
  1. 至少 1 个可用 provider
  2. 已设置 primary/default model
  3. 至少 1 个可用 API key
  4. 至少 1 次最小 agent turn smoke 证据完成
- **输出物 / Output Path**
  - `artifacts/baseline/OpenClaw_Model_Bringup_Record.md`
  - `artifacts/baseline/OpenClaw_AgentTurn_Smoke.md`
- **Proposed TC / BL ID**
  - `TC-BL-P0-001`（PROPOSED）
  - `BL-GATE-005`（PROPOSED）
- **验收命令**
  ```bash
  ls artifacts/baseline/OpenClaw_Model_Bringup_Record.md
  ls artifacts/baseline/OpenClaw_AgentTurn_Smoke.md
  ```
- **Proposed 语义说明**
  路径迁移不改变 `TC-BL-P0-001` 与 `BL-GATE-005` 的 proposed 语义，不得据此上推为已正式注册事实。
- **不可外推声明**  
  本项仅为工程治理侧前置阻塞清除，不得外推为运行时发布、运行时已生效、或自治闭环已达成。

#### WP-P0-2 devloop specialist 正式验收准备
- **来源 SoT**  
  `《QuantWin 专题工作启动.txt》— 2026-03-24 锁定版本`；`Architecture Spec (AS) v5.0-7.1 — QuantWin .pdf`；`ADR-AEF-015：AEF–QuantWin 集成边界规范.md`
- **Owner**  
  `PM / QA / GOV`
- **Accountable Owner**  
  `QA`
- **排序依据**  
  当前唯一治理硬债；不完成则专题状态不得上推为正式验收完成。
- **进入条件**  
  本专题当前状态为“已完成工程收口”，但专题级验证记录与 Traceability 工件尚未直接确认落库。
- **退出条件**  
  同时满足以下 4 项：
  1. 专题级验证记录正式落库
  2. Traceability 工件正式落库
  3. 原始命令输出 / 边界证据 / C-7 证据补齐
  4. 工件可映射到 `Traceability Matrix / Metric Specifications / Test Specifications & Gates`
- **输出物 / Output Path**
  - `artifacts/devloop/DevloopSpecialistValidationReport.md`
  - `artifacts/devloop/DevloopSpecialistTraceability.md`
  - `artifacts/devloop/evidence/`
- **Proposed TC / BL ID**
  - `TC-BL-P0-002`（PROPOSED）
  - `BL-GATE-006`（PROPOSED）
- **验收命令**
  ```bash
  ls artifacts/devloop/DevloopSpecialistValidationReport.md
  ls artifacts/devloop/DevloopSpecialistTraceability.md
  test -d artifacts/devloop/evidence
  ```
- **不可外推声明**  
  本项完成后，仅表示专题已具备进入正式验收复核的前置条件；不得自动写为“正式验收完成”或“运行时已生效”。

### 10.2 当前工作优先级 P1

#### WP-P1-1 AEF 工程反馈闭环接入
- **来源 SoT**  
  `AEF 协议 V10.4`；`ADR-AEF-015：AEF–QuantWin 集成边界规范.md`
- **Owner**  
  `AR / DEV / QA`
- **Accountable Owner**  
  `QA`
- **排序依据**  
  属于 Phase 0 后续工程韧性增强项；不影响当前全局阶段判断，但影响后续自动修复闭环质量。
- **进入条件**  
  Phase 0 已完成；当前需要把工程反馈、日志清洗与语义指纹归档纳入统一闭环。
- **退出条件**  
  同时满足以下 4 项：
  1. Log Adapter 接入说明落库
  2. EFR 记录格式固定
  3. 语义指纹归档路径固定
  4. 全部对象保持 AEF 工程治理层边界，不越界到运行时发布
- **输出物 / Output Path**
  - `artifacts/aef/AEF_Log_Adapter_Record.md`
  - `artifacts/aef/AEF_EFR_Record.md`
  - `artifacts/aef/AEF_Semantic_Fingerprint_Index.md`
- **Proposed TC / BL ID**
  - `TC-BL-P1-001`（PROPOSED）
  - `BL-GATE-007`（PROPOSED）
- **验收命令**
  ```bash
  ls artifacts/aef/AEF_Log_Adapter_Record.md
  ls artifacts/aef/AEF_EFR_Record.md
  ls artifacts/aef/AEF_Semantic_Fingerprint_Index.md
  ```
- **不可外推声明**  
  本项仅补工程反馈闭环，不得外推为 QuantWin 运行时策略链已切换，亦不得写为 OpenClaw 已达成自治闭环。

#### WP-P1-2 受保护域边界守卫与门禁代码化
- **来源 SoT**  
  `ADR-AEF-015：AEF–QuantWin 集成边界规范.md`；`Architecture Spec (AS) v5.0-7.1 — QuantWin .pdf`
- **Owner**  
  `AR / QA / GOV`
- **Accountable Owner**  
  `GOV`
- **排序依据**  
  属于跨层边界硬化项；不影响当前阶段判定，但影响后续自动化安全边界。
- **进入条件**  
  已完成 Phase 0；当前需要把受保护域、运行时发布边界、FastStream 唯一异步层约束固化为可执行门禁。
- **退出条件**  
  同时满足以下 4 项：
  1. 受保护域规则文件落库
  2. 边界守卫检查脚本落库
  3. Gate 规则矩阵落库
  4. 显式阻断“AEF 直改线上当前生效状态”路径
- **输出物 / Output Path**
  - `contracts/aef/protected_domain_rules.yaml`
  - `tools/aef_boundary_guard.py`
  - `artifacts/aef/AEF_Protected_Domain_GateMatrix.md`
- **Proposed TC / BL ID**
  - `TC-BL-P1-002`（PROPOSED）
  - `BL-GATE-008`（PROPOSED）
- **验收命令**
  ```bash
  ls contracts/aef/protected_domain_rules.yaml
  ls tools/aef_boundary_guard.py
  ls artifacts/aef/AEF_Protected_Domain_GateMatrix.md
  ```
- **不可外推声明**  
  本项仅表示工程门禁能力增强，不得外推为运行时治理链已替换 RMS，亦不得写为运行时发布链已由 AEF 接管。

#### WP-P1-3 回归护栏与 TTL / registry integrity 固化
- **来源 SoT**  
  `AEF 协议 V10.4`；`Architecture Spec (AS) v5.0-7.1 — QuantWin .pdf`
- **Owner**  
  `DEV / QA / SRE`
- **Accountable Owner**  
  `SRE`
- **排序依据**  
  属于回归与韧性维护项；不改变当前阶段结论，但决定后续多轮自动修复的稳定性。
- **进入条件**  
  当前需要为后续工程自动化补齐回归目录、TTL 清理与 registry integrity 约束。
- **退出条件**  
  同时满足以下 4 项：
  1. `tests/regressions/` 目录与索引落库
  2. TTL 清理策略文件落库
  3. registry integrity 校验记录落库
  4. 与 C-7 / 边界治理规则无冲突
- **输出物 / Output Path**
  - `tests/regressions/README.md`
  - `config/aef/ttl_policy.yaml`
  - `artifacts/aef/AEF_Registry_Integrity_Record.md`
- **Proposed TC / BL ID**
  - `TC-BL-P1-003`（PROPOSED）
  - `BL-GATE-009`（PROPOSED）
- **验收命令**
  ```bash
  ls tests/regressions/README.md
  ls config/aef/ttl_policy.yaml
  ls artifacts/aef/AEF_Registry_Integrity_Record.md
  ```
- **不可外推声明**  
  本项仅表示回归与清理护栏已具备工程落点，不得外推为业务运行链已进入自动发布、自动验收或自动上线状态。

---

## 11. 禁止外推范围

### 11.1 不得外推为
- QuantWin 全仓正式验收完成
- AEF 全域正式验收完成
- OpenClaw 已进入完整自治编程闭环
- 运行时当前生效状态已切换
- 运行时当前生效策略已发布
- 运行时当前配置已上线生效
- 当前建议新增 ID 已正式注册

### 11.2 不得混写
- AEF 协议中的总体路线图
- AS 中的正式规范结构
- ADR 中的边界约束
- 当前专题状态文件中的现态结论
- 工程治理层工件变更结论
- 业务运行层当前生效状态结论

---

## 12. Traceability

### 12.1 当前基线追溯关系
- 全局阶段 → `AEF Phase 0 实施.txt`
- 总体路线图 → `AEF 协议 V10.4`
- 边界裁决 → `ADR-AEF-015`
- 正式规范 → `AS v5.0-7.1`
- 当前专题状态 → `《QuantWin 专题工作启动.txt》— 2026-03-24 锁定版本`

### 12.2 Content-Change 触发规则
出现以下任一情况时，本文件内容 MUST 更新：
1. `AEF 协议 V10.4` 的阶段路线图发生变更
2. `ADR-AEF-015` 的边界裁决规则发生变更
3. `AS v5.0-7.1` 的正式规范结构或 C-7 要求发生变更
4. 当前全局阶段、OpenClaw 阶段或专题阶段发生正式状态更新
5. 当前工作优先级、进入条件、退出条件或输出物发生变更

### 12.3 Lock-Change 触发规则
出现以下任一情况时，本文件锁定对象 MUST 更新：
1. `《QuantWin 专题工作启动.txt》` 的锁定版本发生变更
2. 当前状态层使用的同名文件版本重新裁定
3. 当前状态层锁定日期发生重置
4. 当前专题裁决依据从其他状态文件切换到新锁定对象

### 12.4 维护约束
1. 本文件不得绕开上游 SoT 单独改写事实。  
2. 本文件只允许由 SoT 变更驱动修订，不允许旁路改写事实。  
3. 若同名文件存在多版本，本文件必须显式记录正文主锁定表达。  
4. 本文件只做基线收束，不做运行时发布声明。  

### 12.5 建议命名规则（建议新增，非既成事实）
以下命名仅为后续追溯统一建议，不构成已正式注册事实：
- `BL-ENTRY-*`：基线入口文件类追溯项
- `BL-GATE-*`：基线审计门禁类追溯项

建议对应关系：
- `BL-ENTRY-001`：单一正式基线入口文件首版
- `BL-GATE-001`：SoT 锁定与引用规范
- `BL-GATE-002`：阶段命名隔离
- `BL-GATE-003`：任务清单裁决性
- `BL-GATE-004`：正式口径去草案化
- `BL-GATE-005`：OpenClaw 模型层阻塞清除验收
- `BL-GATE-006`：devloop specialist 正式验收准备验收
- `BL-GATE-007`：AEF 工程反馈闭环接入验收
- `BL-GATE-008`：受保护域边界守卫与门禁代码化验收
- `BL-GATE-009`：回归护栏与 TTL / registry integrity 固化验收

---

## 13. 当前基线一句话摘要

**AEF Phase 0 已完成；OpenClaw 当前仍处于“主机层可用，但模型层仍未打通”的过渡阶段；`devloop ChatGPT/Qwen specialist` 已完成工程收口但尚未达到正式验收；本文件当前状态为 `Ready for Landing Review`，拟作为 QuantWin / AEF / OpenClaw 当前阶段正式基线入口文件首版。**

---

## 附注 A：当前状态层内部版本索引

`《QuantWin 专题工作启动.txt》— 2026-03-24 锁定版本` 的内部版本索引为：

`file_000000008c60720880a6b868d6eb647c`

该索引仅供版本复核使用，不作为正文主锁定表达。
