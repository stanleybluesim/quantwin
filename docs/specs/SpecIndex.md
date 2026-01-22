# SpecIndex (冻结清单)

> 目标：把“验收依据”变成仓库内可追溯的基线（版本 + sha256）。

## Artifacts

| artifact_id | title | version | sha256 | storage | notes |
|---|---|---|---|---|---|
| RS-QUANTWIN | Requirements Spec | v3.1 | TODO | external-or-docs/specs | 把 PDF 放入 docs/specs/ 后填 sha256 |
| AS-QUANTWIN | Architecture Spec | v5.x | TODO | external-or-docs/specs | 同上 |
| INPUT-PACK | Input Pack | v1 | TODO | external-or-docs/specs | 如是 md，建议直接纳入 repo |

## How to fill sha256
- macOS:
  - `shasum -a 256 <file>`
- linux:
  - `sha256sum <file>`

填完后提交即可。
