---
name: using-cadence
description: Use when the user explicitly requests to use Cadence. This skill serves as Cadence's unified entry point, always starting from `cadence-planning`, bringing the task into Cadence.
---

# using-cadence

Bring the current task into `Cadence`.

`Cadence = Plan-driven phased execution flow.`

## Core Constraints

1. This skill is `Cadence`'s unified entry point and default entry point, responsible for handling explicit `Cadence` requests and default entry for complex or non-trivial tasks.
2. This skill always starts from `cadence-planning` to bring tasks into `Cadence`; do not infer which subsequent phase to enter based on file states in the repository here.
3. If the user directly specifies `cadence-planning`, `cadence-issue-generation`, or `cadence-execution`, it means entering `Cadence` from that phase and continuing advancement along the lifecycle after that phase.
4. If the flow is interrupted and needs to continue from mid-process, the user directly specifies the corresponding phase skill to continue the flow.
5. Unless the user explicitly requests exiting `Cadence`, or the current task flow has reached a shared lifecycle-defined terminal state, once entered into the flow, remain within the `Cadence` lifecycle for advancement.
6. When the current request first enters `Cadence`, output a clear entry prompt before starting substantive work, explaining the current phase, entry reason, and next action.
7. When the current request causes `Cadence` to reach a terminal state or explicitly exits, output a clear exit prompt before resuming default execution mode, explaining the exit phase, exit reason, and subsequent state.
8. Phase semantics, confirmation points, and default handoff rules are governed by [references/cadence-lifecycle.md](references/cadence-lifecycle.md).

## Quick Flow

1. Read [references/cadence-lifecycle.md](references/cadence-lifecycle.md), and bring the current task into the flow starting from the `Planning` phase per the shared lifecycle semantics.
2. If the user actually wants to continue a pre-existing `Cadence` flow from mid-process, do not guess the target here; prompt the user to directly specify the corresponding phase skill.

## Resources

- [references/cadence-lifecycle.md](references/cadence-lifecycle.md): `Cadence` shared lifecycle semantics, phase prerequisites, confirmation points, and handoff rules
