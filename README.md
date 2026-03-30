# Cadence

<div align="center">

[English](README.md) | [简体中文](README.zh-CN.md)

</div>

---

**Plan-driven phased execution flow — a lightweight, stable, universal agent harness.**

Usable with Codex, Claude Code, and other AI agents.

---

**Table of Contents**

- [The Soul of Cadence: Define Process, Not Implementation](#the-soul-of-cadence-define-process-not-implementation)
- [How It Works](#how-it-works)
- [Pipeline Overview](#pipeline-overview)
- [Harness Layers](#harness-layers)
- [Quick Start](#quick-start)
- [FAQ](#faq)
- [Design Principles](#design-principles)
- [License](#license)

---

## The Soul of Cadence: Define Process, Not Implementation

Cadence is a lightweight, stable, universal agent harness. It specifies "what to do, in what order, and under what conditions to advance" — but not "how to do it." What MCP tools, subagent strategies, or review dimensions each step uses is left to the agent to choose based on your project type, tech stack, and personal preferences.

These should not be hardcoded in the harness:

- What tool to use for code review → depends on your tech stack and team habits
- What strategy to use for running tests → depends on your project type and test framework
- What dimensions to use for plan review → depends on your project complexity and risk tolerance
- What MCP servers to use → depends on what capabilities you currently have enabled

Cadence only has three things: **phase definitions**, **confirmation point rules**, and **issue file schema**. No built-in command sets, no built-in domain knowledge, no built-in toolchains. Everything else is filled in by your agent's existing capabilities and project context.

This means two things:

**Cadence won't become outdated.** Your MCP servers evolve, your agents upgrade, your projects change — the harness doesn't need to change with them. The process is rigid; the implementation is free.

**Cadence treats all project types equally.** Whether you write TypeScript, Python, Go, or Rust, whether you're building a monolith, microservices, or a library, Cadence works exactly the same way. It doesn't know and doesn't need to know what you're building — it only knows how to reliably advance a process from plan to implementation.

---

## How It Works

It starts the moment you describe a task to an AI agent.

The agent doesn't jump straight into writing code. It first takes a step back, reads the repository, clarifies key gaps, drafts a structured plan file, and then hands it to an independent `plan-reviewer` subagent for review. After the review passes, you see the full plan and review results, and only after you confirm does it proceed.

Next is issue generation. The plan is decomposed into independently deliverable, independently verifiable outcome units, written to TOML files. Each issue has clear completion conditions, validation entry points, and dependencies. The `issue-reviewer` subagent independently validates structure and decomposition quality. After you confirm, execution begins automatically.

In the execution phase, each issue is dispatched to an `implementer` subagent with an independent context. After completion, it must pass through `spec-reviewer` (whether it meets requirements) and `code-reviewer` (whether there are defects and regression risks) gates in sequence before entering final validation. After all pass, `validate_by` primary validation and `regress_by` regression are run, with status immediately written back to the file.

**You don't need to remember any of the process.** The skill automatically checks the current phase, reads existing artifacts, and advances to the next step. You only need to say "confirm" at confirmation points.

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Cadence Pipeline                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐   │
│  │  Planning    │───→│ Issue Generation │───→│  Execution   │   │
│  │              │    │                  │    │              │   │
│  │  plan/*.md   │    │  issues/*.toml   │    │  code +      │   │
│  │              │    │                  │    │  validation  │   │
│  │ plan-reviewer│    │ issue-reviewer   │    │ spec-reviewer│   │
│  │              │    │                  │    │ code-reviewer│   │
│  └──────────────┘    └──────────────────┘    └──────────────┘   │
│         ↑                    ↑                      ↑           │
│    User confirm        User confirm          Auto advance       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Planning

Transform task requirements into structured plan files.

1. Read repository context, clarify key information gaps
2. Draft `plan/YYYY-MM-DD-<feature-name>.md` based on template
3. `plan-reviewer` subagent independently reviews: completeness, consistency, executability
4. Auto-fix fixable issues, or clarify with user for decisions needed
5. After user confirms, automatically handoff to Issue Generation

**Plan file contains**: Background, Goals & DoD, Scope, Impact, Constraints & Dependencies, Implementation Strategy, Phase Breakdown, Testing & Validation, Risks & Mitigations.

### Issue Generation

Decompose the plan into independently executable, verifiable, and writable outcome units.

1. Read plan file, generate `issues/YYYY-MM-DD-<feature-name>.toml` following decomposition rules
2. `issue-reviewer` subagent reviews: TOML structure, decomposition granularity, dependencies, validation strategy
3. Auto-fix structural issues
4. After user confirms, automatically handoff to Execution

**Decomposition principles**: Split by outcome (not by action), split by dependency (not by file count), split by validation (not by technical layer). Each issue corresponds to one primary outcome, one primary validation entry point, and clear dependency boundaries.

### Execution

Advance implementation, validation, and state writeback based on issue files.

1. Select currently executable frontier issues (respecting dependencies)
2. Dispatch `implementer` subagent for each issue (independent context, no main conversation pollution)
3. Required gates: `spec-reviewer` → `code-reviewer` (cannot be skipped)
4. Execute `validate_by` (primary validation) and `regress_by` (regression)
5. Immediately write back status to issue file
6. Rolling recalculation of executable set, continue advancing

**Parallel scheduling**: Multiple independent issues are dispatched to subagents in parallel by default; falls back to sequential when shared write scopes or dependency conflicts exist.

---

## Harness Layers

Cadence's harness is not a single layer, but a layered design from structure to semantics:

```
┌───────────────────────────────────────────────┐
│  Semantic Layer (reviewer subagents)          │
│  Is the plan complete? Are issues well-split? │
│  Is the code defect-free?                     │
├───────────────────────────────────────────────┤
│  Process Layer (three-phase pipeline +        │
│  confirmation points)                         │
│  Phase boundaries, handoff rules, state       │
│  machine advancement                          │
├───────────────────────────────────────────────┤
│  Structural Layer (mechanical guardrails)     │
│  TOML validation, field constraints,          │
│  writeback boundary checks                    │
├───────────────────────────────────────────────┤
│  Environment Layer (file system + skill       │
│  format)                                      │
│  plan/*.md, issues/*.toml, SKILL.md,          │
│  templates                                    │
└───────────────────────────────────────────────┘
```

**Environment Layer** is the most fundamental primitive: agents read and write files, files serve as state carriers, independent of context windows or conversation history.

**Structural Layer** provides mechanical guarantees through Python scripts: TOML parsing, field types, allowed values, writeback boundaries. It doesn't care whether the semantics are correct, only whether the structure is compliant.

**Process Layer** is the three-phase pipeline and confirmation points: after plan-reviewer passes, issue generation can proceed; after user confirms, execution can begin. Phase boundaries are enforced.

**Semantic Layer** is the independent judgment of reviewer subagents: plan-reviewer checks plan completeness, issue-reviewer checks decomposition quality, spec-reviewer checks requirements coverage, code-reviewer checks defect risks. Each ring does only its own job and does not trust upstream self-assessment.

---

## Quick Start

### Installation

```bash
git clone https://github.com/YukiKazahana/cadence.git
```

#### Linux/macOS

```
# Global install (choose the directory for your agent)
cp -r cadence/skills/ ~/.codex/skills/       # Codex
cp -r cadence/skills/ ~/.claude/skills/      # Claude Code
```

#### Windows PowerShell

```
# Global install (choose the directory for your agent)
Copy-Item -Recurse -Path .\cadence\skills\* -Destination $HOME\.codex\skills\       # Codex
Copy-Item -Recurse -Path .\cadence\skills\* -Destination $HOME\.claude\skills\     # Claude Code
```

### Usage

| Scenario | Command |
|----------|---------|
| Start a complete task from scratch | `/using-cadence` |
| Planning only, not ready for issue generation | `/cadence-planning` |
| Plan exists, start splitting issues | `/cadence-issue-generation` |
| Issue files exist, start implementation | `/cadence-execution` |
| Process interrupted, resume work | Specify the interrupted phase directly, e.g. `/cadence-execution` |

---

## FAQ

**Which AI agents are supported?**

Cadence is designed based on Codex (`SKILL.md` + `agents/openai.yaml`). Any AI agent that supports the same skill format can theoretically use it, including but not limited to Codex, Claude Code, etc. The invocation method (slash command, skill name, etc.) depends on the specific agent's implementation.

**What if the process is interrupted?**

Specify the phase directly to continue (`/cadence-execution`, etc.). Cadence doesn't depend on system auto-recovery — the phase you explicitly choose is the recovery point.

**Can I skip a phase?**

Yes. Specify the phase you want to enter directly. But each phase checks prerequisites — if there's no plan file, Issue Generation will require you to complete Planning first.

**What if a subagent fails?**

It automatically falls back to main agent execution. Subagent failure should not block the entire process.

---

## Design Principles

**Don't optimize the model, optimize the environment.** Cadence doesn't change agent capabilities — it enables agents to work reliably in a structured environment through constraint mechanisms, feedback loops, and file system primitives.

**File system is the most fundamental harness primitive.** All state, plans, and issues are files. The agent has a workbench, work can proceed incrementally, and multiple agents can coordinate through files. No dependency on context windows or conversation history.

**Explicit over implicit.** Phase transitions require user confirmation, state changes are immediately written back, not inferred from conversation history.

**Don't trust upstream self-assessment.** Each reviewer subagent independently reads files and checks item by item, without looking at the drafter's self-evaluation. The key to feedback loops is that each ring is an independent judgment.

**Constraints are structural guarantees, not suggestions.** Reviewer gates cannot be skipped, plans must not contain TODO/TBD, writeback can only modify four fields. These are not best practices — they are mechanically enforced rules.

**Split by outcome, not by action.** Issue boundaries are deliverable outcomes. Changes that touch multiple files but still serve the same outcome are not split.

---

## License

MIT License - see LICENSE file for details.

---

Thanks to [LinuxDo](https://linux.do/)
