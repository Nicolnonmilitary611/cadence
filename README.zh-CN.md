# Cadence

**计划驱动的分阶段执行流 —— 一个轻量、稳定、通用的 agent harness。**

可在 Codex、 Claude Code 及其他 AI agent 中使用。

---

**目录**

- [Cadence 的灵魂：只定义流程，不定义实现](#cadence-的灵魂只定义流程不定义实现)
- [它如何工作](#它如何工作)
- [流水线概览](#流水线概览)
- [Harness 分层](#harness-分层)
- [快速开始](#快速开始)
- [FAQ](#faq)
- [设计原则](#设计原则)
- [License](#license)

---

## Cadence 的灵魂：只定义流程，不定义实现

Cadence 是一个轻量、稳定、通用的 agent harness。它规定"做什么、按什么顺序、在什么条件下推进"，但不规定"怎么做"。每一步具体用什么 MCP 工具、什么 subagent 策略、什么 review 维度，由 agent 根据你的项目类型、技术栈和个人习惯自行选择。

这些本应定制化的内容不应该硬编码在 harness 里：

- 用什么工具做 code review → 取决于你的技术栈和团队习惯
- 用什么策略跑测试 → 取决于你的项目类型和测试框架
- 用什么维度做 plan review → 取决于你的项目复杂度和风险容忍度
- 用什么 MCP server 辅助 → 取决于你当前启用了什么能力

Cadence 只有三样东西：**阶段定义**、**确认点规则**、**issue 文件 schema**。不内置命令集、不内置领域知识、不内置特定工具链。剩下的全靠你已有的 agent 能力和项目上下文来填充。

这意味着两件事：

**Cadence 不会过时。** 你的 MCP server 在进化，你的 agent 在升级，你的项目在变——harness 不需要跟着改。流程是刚性的，实现是自由的。

**Cadence 对所有项目类型一视同仁。** 不管你是写 TypeScript、Python、Go 还是 Rust，不管你是单体应用、微服务还是库，Cadence 的工作方式完全一样。它不知道也不需要知道你在构建什么——它只知道如何可靠地推进一个从计划到实现的流程。

---

## 它如何工作

它从你向 AI agent 描述一个任务的那一刻就开始了。

agent 不会直接动手写代码。它会先退一步，读仓库、澄清关键缺口、起草结构化的计划文件，然后把计划交给一个独立的 `plan-reviewer` 子代理复核。复核通过后，你看到计划全文和评审结果，确认后它才继续。

接下来是 issue 生成。计划被拆解为一个个可独立交付、独立验证的结果单元，写入 TOML 文件。每个 issue 有清晰的完成条件、验证入口和依赖关系。`issue-reviewer` 子代理独立校验结构和拆分质量。你确认后，自动进入执行。

执行阶段，每个 issue 被派发给一个独立上下文的 `implementer` 子代理。完成后，必须依次通过 `spec-reviewer`（是否符合需求）和 `code-reviewer`（是否有缺陷和回归风险）两道门禁，才能进入最终验证。全部通过后，运行 `validate_by` 主验证和 `regress_by` 回归，即时回写状态到文件。

**你不需要记住任何流程。** skill 会自动检查当前阶段、读取已有产物、推进下一步。你只需要在确认点说"确认"。

---

## 流水线概览

```
┌─────────────────────────────────────────────────────────────────┐
│  Cadence 流水线                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  Planning    │───→│ Issue Generation │───→│  Execution   │  │
│  │              │    │                  │    │              │  │
│  │  plan/*.md   │    │  issues/*.toml   │    │  代码 + 验证  │  │
│  │              │    │                  │    │              │  │
│  │ plan-reviewer│    │ issue-reviewer   │    │ spec-reviewer│  │
│  │              │    │                  │    │ code-reviewer│  │
│  └──────────────┘    └──────────────────┘    └──────────────┘  │
│         ↑                    ↑                      ↑          │
│     用户确认             用户确认               自动推进        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Planning

将任务需求转化为结构化的计划文件。

1. 读取仓库上下文，澄清关键信息缺口
2. 基于模板起草 `plan/YYYY-MM-DD-<feature-name>.md`
3. `plan-reviewer` 子代理独立复核：完整性、一致性、可执行性
4. 自动修复可修问题，或向用户澄清需要决策的问题
5. 用户确认后，自动 handoff 到 Issue Generation

**计划文件包含**：背景、目标与 DoD、范围、影响面、约束与依赖、实施策略、阶段拆分、测试与验证、风险与应对。

### Issue Generation

将计划拆解为可独立执行、验证和回写的结果单元。

1. 读取计划文件，按拆分规则生成 `issues/YYYY-MM-DD-<feature-name>.toml`
2. `issue-reviewer` 子代理复核：TOML 结构、拆分粒度、依赖关系、验证策略
3. 自动修复结构问题
4. 用户确认后，自动 handoff 到 Execution

**拆分原则**：按结果拆（不按动作），按依赖拆（不按文件数），按验证拆（不按技术层）。每个 issue 对应一个主结果、一个主要验证入口、清晰依赖边界。

### Execution

按 issue 文件推进实现、验证和状态回写。

1. 选择当前可执行的前沿 issue（尊重依赖关系）
2. 为每个 issue 派发 `implementer` 子代理（独立上下文，不污染主对话）
3. 必经门禁：`spec-reviewer` → `code-reviewer`（不可跳过）
4. 执行 `validate_by`（主验证）和 `regress_by`（回归）
5. 即时回写状态到 issue 文件
6. 滚动重算可执行集合，继续推进

**并行调度**：多个独立 issue 默认并行派发子代理；存在共享写入范围或依赖冲突时自动回退为顺序。

---

## Harness 分层

Cadence 的 harness 不是一层，而是从结构到语义的分层设计：

```
┌──────────────────────────────────────────────┐
│  语义层（reviewer 子代理）                      │
│  计划是否完整？issue 拆分是否合理？代码是否有缺陷？│
├──────────────────────────────────────────────┤
│  流程层（三阶段流水线 + 确认点）                  │
│  阶段边界、handoff 规则、状态机推进              │
├──────────────────────────────────────────────┤
│  结构层（机械 guardrail）                       │
│  TOML 校验、字段约束、回写边界检查               │
├──────────────────────────────────────────────┤
│  环境层（文件系统 + skill 格式）                  │
│  plan/*.md、issues/*.toml、SKILL.md、模板       │
└──────────────────────────────────────────────┘
```

**环境层**是最基础的原语：agent 读写文件，文件作为状态载体，不依赖上下文窗口或对话历史。

**结构层**是 Python 脚本提供的机械保证：TOML 解析、字段类型、允许值、回写边界。不关心语义对不对，只关心结构合不合规。

**流程层**是三阶段流水线和确认点：plan-reviewer 通过后才能进 issue 生成，用户确认后才能进执行。阶段边界是强制的。

**语义层**是 reviewer 子代理的独立判断：plan-reviewer 检查计划完整性，issue-reviewer 检查拆分质量，spec-reviewer 检查需求覆盖，code-reviewer 检查缺陷风险。每一环只做自己的事，不信任上游自述。

---

## 快速开始

### 安装

```bash
git clone https://github.com/YukiKazahana/cadence.git
```

#### Linux/macOS

```
# 全局安装（按你使用的 agent 选择对应目录）
cp -r cadence/skills/ ~/.codex/skills/       # Codex
cp -r cadence/skills/ ~/.claude/skills/      # Claude Code
```

#### Windows PowerShell

```
# 全局安装（按你使用的 agent 选择对应目录）
Copy-Item -Recurse -Path .\cadence\skills\* -Destination $HOME\.codex\skills\       # Codex
Copy-Item -Recurse -Path .\cadence\skills\* -Destination $HOME\.claude\skills\     # Claude Code
```

### 使用

| 场景 | 命令 |
|------|------|
| 从头开始一个完整任务 | `/using-cadence` |
| 只做规划，不急着生成 issue | `/cadence-planning` |
| 已有计划，开始拆 issue | `/cadence-issue-generation` |
| 已有 issue 文件，开始实现 | `/cadence-execution` |
| 流程中断了，接着干 | 直接指定中断时的阶段，如 `/cadence-execution` |

---

## FAQ

**支持哪些 AI agent？**

Cadence 基于 Codex（`SKILL.md` + `agents/openai.yaml`）设计。任何支持相同 skill 格式的 AI agent 理论上都可以使用，包括但不限于 Codex、Claude Code 等。调用方式（slash command、skill 名称等）取决于具体 agent 的实现。

**流程中断了怎么办？**

直接指定阶段继续（`/cadence-execution` 等）。Cadence 不依赖系统自动恢复，你显式选择的阶段就是恢复点。

**我可以跳过某个阶段吗？**

可以。直接指定你想进入的阶段。但每个阶段会检查前置条件 —— 如果没有计划文件，Issue Generation 会要求你先完成 Planning。

**子代理失败了怎么办？**

自动回退到主代理执行，子代理失败不应阻塞整个流程。

---

## 设计原则

**不优化模型，优化环境。** Cadence 不改变 agent 的能力，而是通过约束机制、反馈回路和文件系统原语让 agent 在结构化的环境中可靠工作。

**文件系统是最基础的 harness 原语。** 所有状态、计划和 issue 都是文件。agent 有了工作台，工作可以增量进行，多 agent 可以通过文件协同。不依赖上下文窗口，不依赖对话历史。

**显式优于隐式。** 阶段转换需要用户确认，状态变更即时回写，不靠对话历史推断。

**不信任上游自述。** 每个 reviewer 子代理独立读取文件、逐条检查，不看起草者的自我评价。反馈回路的关键在于每一环都是独立判断。

**约束是结构保证，不是建议。** reviewer 门禁不可跳过，计划中不允许 TODO/TBD，回写只能动四个字段。这些不是最佳实践，是机械执行的规则。

**按结果拆分，不按动作拆分。** Issue 的边界是可交付的结果。只是改了多个文件但仍服务于同一结果的，不拆。

---

## License

MIT License - see LICENSE file for details.
