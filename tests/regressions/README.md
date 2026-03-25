# Regression Registry README

## 1. Formal Object
- task_id: WP-P1-3
- task_name: 回归护栏与 TTL / registry integrity 固化
- owner: DEV / QA / SRE
- accountable_owner: SRE
- scope_layer: AEF_ENGINEERING_GOV
- formal_output: true

## 2. Entry / Exit Mapping
- entry_condition: 为后续工程自动化补齐回归目录、TTL 清理与 registry integrity 约束
- exit_condition_1: tests/regressions/ 目录与索引落库
- exit_condition_2: TTL 清理策略文件落库
- exit_condition_3: registry integrity 校验记录落库
- exit_condition_4: 与 C-7 / 边界治理规则无冲突

## 3. Boundary
- AEF = 工程治理层
- QuantWin = 业务运行层
- FastStream = 唯一异步通信层
- 所有异步消息 MUST 通过已登记 Topic
- 所有异步消息 MUST 携带 idempotency_key
- 工件变更与运行时发布动作 MUST 分离
- 本目录不表示运行时当前生效状态已切换
- 本目录不表示自动发布完成
- 本目录不表示自动验收完成
- 本目录不表示自动上线完成

## 4. Gate 2 Regression Rule
- 修复类变更 MUST 在 tests/regressions/ 下提交 Before/After 回归对
- before/ 表示修复前失败复现
- after/ 表示修复后通过复现
- 每个回归案例 MUST 可映射到唯一 case_id
- 每个回归案例 SHOULD 对应单一缺陷或单一修复点

## 5. Registry Index Contract
- 本轮索引采用文档内索引契约，不新增额外正式索引文件
- case_id MUST 唯一
- case_id MUST 匹配格式: RG-[0-9]{4}
- 每个 case SHOULD 包含:
  - before/
  - after/
  - meta.yaml
- meta.yaml MUST 包含:
  - case_id
  - introduced_by
  - created_at
  - ttl_days
  - trace_id
  - run_id
  - audit_id
  - cleanup_state

## 6. C-7 Required Fields
- trace_id: MUST
- run_id: MUST
- audit_id: MUST
- report_id: N/A
- report_id 仅报告导出链路适用
- 非报告链路写入真实 report_id = FAIL

## 7. TTL Binding
- ttl source MUST be config/aef/ttl_policy.yaml
- missing ttl_days = FAIL
- invalid ttl_days = FAIL
- duplicate case_id = FAIL
- missing trace_id / run_id / audit_id = FAIL

## 8. Minimal Acceptance Anchors
- acceptance_command_1: ls tests/regressions/README.md
- acceptance_command_2: ls config/aef/ttl_policy.yaml
- acceptance_command_3: ls artifacts/aef/AEF_Registry_Integrity_Record.md

## 9. Non-Extrapolation
- 本项仅表示回归与清理护栏已具备工程落点
- 不得外推为业务运行链已进入自动发布状态
- 不得外推为业务运行链已进入自动验收状态
- 不得外推为业务运行链已进入自动上线状态
