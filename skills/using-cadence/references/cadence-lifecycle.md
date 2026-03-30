# Cadence Lifecycle

`Cadence = Plan-driven phased execution flow.`

This file is the shared lifecycle constraints for `Cadence`. `using-cadence` and the three phase skills should all interpret phases, confirmation points, and subsequent handoff based on this file.

## Core Semantics

1. `using-cadence` is `Cadence`'s preferred public entry point and default entry point, always starting from the `Planning` phase.
2. `cadence-planning`, `cadence-issue-generation`, and `cadence-execution` together bear `Cadence`'s phase advancement responsibilities and connect per the shared lifecycle.
3. When the user directly specifies a phase skill, it means entering `Cadence` from that phase and continuing advancement along the lifecycle after that phase.
4. The current phase is determined by the current entry method and the user's explicit specification; continuation after interruption is by the user explicitly selecting the corresponding phase.
5. Unless the user explicitly requests exiting `Cadence`, or the current task's `Cadence` flow has reached a terminal state, once entered into the flow, continue within the `Cadence` lifecycle.
6. "Stopped at a confirmation point" means `Cadence` is paused waiting for user input, not that the flow has ended.

## Shared Source of Truth

1. Lifecycle, phase prerequisites, confirmation points, default handoff, and terminal states are governed by this file.
2. `plan/*.md` structural requirements are governed by `../cadence-planning/assets/plan-template.md`; `cadence-planning` supplements the planning phase process and reviewer rules.
3. `issues/*.toml` field structure, default values, and annotation examples are governed by `assets/issue-template.toml`; `cadence-issue-generation` and `cadence-execution` supplement each phase's generation, review, writeback, and advancement rules.
4. `scripts/cadence_validate.py` provides basic structure and execution-stage writeback boundary checks, serving as a mechanical guardrail.
5. Phase skills, reviewers, and the main agent are responsible for semantic validation such as plan consistency, issue decomposition quality, validation strategy, and execution judgment; reviewer gates for each issue in the `Execution` phase are governed by `cadence-execution`'s rules.

## Current Session Capabilities Gate

1. `Cadence`'s `Planning`, `Issue Generation`, and `Execution` phases, before starting the current round's substantive work, must by default first complete a current session `available capabilities` adaptation check.
2. The `available capabilities` referred to in this file only means session tool capabilities that are enabled in the current session and actually callable by the agent, such as skills, MCP tools; it does not include regular commands, repository scripts, or other non-session-tool means.
3. The adaptation check scope covers all `available capabilities` in the current session; do not only check a single familiar capability, and do not skip screening just because regular command entry points exist.
4. If there are applicable capabilities that can provide substantive benefit to the current subtask, prioritize calling them at the most appropriate point; applicable scenarios include investigation, strategy review, implementation assistance, review, targeted validation, command execution, or result documentation enhancement.
5. If it is judged that there are no suitable capabilities currently, or calling would significantly increase cost, risk, or interfere with the main process, it may not be called; but `none-applicable` or an equivalent conclusion must be explicitly stated with reasons in the current round's phase notes, reviewer output, or execution-period `notes`.
6. "It's faster to just run the command" by itself is not a sufficient reason; only when `available capabilities` provide no substantive benefit to the current subtask, or would clearly amplify coordination, environment, or switching costs, does it constitute a reason not to call.
7. Do not mechanically call capabilities unrelated to the current subtask just to formally satisfy the rules; the requirement is to first complete explicit screening, then actively call applicable capabilities.

## Entry Prompt

1. When the current request enters `Cadence` for the first time via `using-cadence`, or enters `Cadence` from a specific phase by directly specifying a phase skill, output a clear status prompt before starting substantive planning, generation, or execution work.
2. This prompt should at least include:
   - Entered `Cadence`
   - Current phase
   - Reason for entering this phase
   - Next action
3. Recommended to keep it concise and clear, for example: `Entered Cadence. Current phase: Planning. Reason: Starting from the beginning using using-cadence. Next: Draft the initial plan.`
4. If entering via direct phase skill specification, the prompt should also clearly state that the current phase comes from the user's explicit phase selection.
5. Internal phase automatic handoffs do not need to repeat the full "entered `Cadence`" prompt; only output this prompt when the current request enters `Cadence` for the first time.

## Exit Prompt

1. When the current request causes the `Cadence` flow to reach a terminal state, or the user explicitly requests ending, canceling, or exiting the current `Cadence` flow, output a clear exit prompt before resuming default execution mode.
2. This prompt should at least include:
   - Exited `Cadence`
   - Phase at exit
   - Reason for exit
   - Current result or subsequent state
3. Recommended to keep it concise and clear, for example: `Exited Cadence. Exit phase: Execution. Reason: All issues completed and validated. Follow-up: Resuming default execution mode.`
4. If the user actively terminates the current flow, the prompt should also clearly state that this is a user-driven exit rather than normal completion.
5. Confirmation points do not output an exit prompt; only output when a true terminal state is reached.

## Phases and Prerequisites

### Planning

- Phase: `cadence-planning`
- Goal: Draft and confirm `plan/*.md`
- Minimum prerequisite: A identifiable current task exists
- Phase completion: In the current flow, the user explicitly confirms continuing to `cadence-issue-generation` based on the current plan file
- Default follow-up: After receiving confirmation in the current flow, automatically transition to `cadence-issue-generation`

### Issue Generation

- Phase: `cadence-issue-generation`
- Goal: Generate issue files for the current task based on plan files
- Minimum prerequisite: A `plan/*.md` matching the current task exists, or one explicitly specified by the user
- Phase completion: In the current flow, the user explicitly confirms continuing to `cadence-execution` based on the current issue file
- Default follow-up: After receiving confirmation in the current flow, automatically transition to `cadence-execution`

### Execution

- Phase: `cadence-execution`
- Goal: Advance implementation, validation, and status writeback based on existing issue files
- Minimum prerequisite: Issue files matching the current task or explicitly specified by the user exist and are continuable
- Phase constraints:
  - Before each issue enters issue-level final `validate_by`, `spec-reviewer = PASS` must be obtained first, then `code-reviewer = PASS`; main agent execution, single-chain, low-risk, or `implementer` dispatch exemption do not change this order. Only user explicit exemption allows skipping reviewer gates.
- Phase completion: All executable issues have completed required reviewer reviews and necessary validation and status writeback
- Default follow-up: Remain within `Cadence` until a terminal state is reached or the user explicitly ends the flow

## Entry and Phase Selection

1. When using `using-cadence`, always start from `cadence-planning`; do not automatically select a later phase based on existing plan or issue files.
2. When the user directly specifies `cadence-planning`, `cadence-issue-generation`, or `cadence-execution`, always enter `Cadence` from that explicitly specified phase.
3. If a phase lacks the target files, context, or has multiple candidate targets needed to continue, do not automatically redirect to another phase based on repository state; first ask the user to specify the target file, task, or explicitly choose which phase to use.
4. Downstream handoff within the current flow still advances per each phase's confirmation points and default follow-up; but cross-interruption recovery relies only on the user's subsequent explicit phase selection, not on system auto-recovery.

## Confirmation Point Semantics

1. `Planning`'s confirmation point is "plan file has been written to `plan/*.md` and completed `plan-reviewer` review, waiting for user to reply confirm to enter `cadence-issue-generation`"; before receiving explicit confirmation, do not enter the downstream phase.
2. `Issue Generation`'s confirmation point is "issue file has been written and completed `issue-reviewer` review, waiting for user to continue adjusting, adopt, or confirm entering `cadence-execution`"; before receiving explicit confirmation, do not enter the downstream phase.
3. While at the `Issue Generation` confirmation point, if the user continues to provide supplementary, deletion, reordering, or clarification feedback on the current issue file, continue handling that file within the current `Issue Generation` phase.
4. While at a confirmation point, it is still considered active `Cadence` within the current flow; as long as the user subsequently gives a clear confirmation matching the current confirmation point, the current downstream phase should continue advancing.
5. If the flow is interrupted after a confirmation point, the user can directly specify the downstream phase skill to continue; that explicit phase selection itself is treated as re-entering `Cadence` from that phase.
6. Confirmation points are not terminal states; do not automatically exit `Cadence` when stopped at a confirmation point.

## Contract Issues and User Decisions

1. If during `Execution` it is discovered that the current issue's contract fields (e.g., `depends_on`, `done_when`, `validate_by`, `regress_by`, `regress_timing`) are incorrect, missing, or inconsistent with the plan, the issue should be treated as contract-blocked.
2. Such situations are low-frequency exception handling and are not targets for main process optimization.
3. The main agent should first mark the affected issue as `blocked`, and record the blocking reason, impact scope, resolution conditions, and suggested revision phase in `notes`: issue contract problems usually suggest entering `cadence-issue-generation`; plan-level problems usually suggest entering `cadence-planning`.
4. After status writeback, the main agent should explain the issue, current impact, and suggested revision direction to the user, and ask how to proceed.
5. The current flow waits for user decision in the `Execution` phase; the user can choose to enter `cadence-issue-generation`, enter `cadence-planning`, remain in `Execution`, or end the current flow.
6. If the user explicitly chooses `cadence-issue-generation` or `cadence-planning`, that phase selection is treated as re-entering `Cadence` from the corresponding phase; subsequent advancement follows that phase's normal reviewer and confirmation point semantics.
7. As long as `blocked` issues or pending user decisions still exist, the current flow continues waiting in the `Execution` phase, without automatically exiting `Cadence` or outputting an exit prompt.

## Terminal States and Auto-Exit

1. When the current task's `Cadence` flow reaches a terminal state, automatically exit `Cadence` and resume default execution mode.
2. The following situations are considered terminal states:
   - User explicitly requests ending, canceling, or exiting the current `Cadence` flow
   - `Execution` phase has completed required reviewer reviews for all executable issues, and completed necessary validation and status writeback, with no pending next steps
   - User explicitly refuses to continue the current `Planning` or `Issue Generation` flow, causing the current task to terminate at that phase
3. If only stopped at a confirmation point, waiting for confirmation, waiting to adopt issue files, waiting for user to decide next steps, or `blocked` issues still exist, it is not a terminal state, and do not automatically exit `Cadence`.

## Directly Invoking Phase Skills

1. When the user directly specifies `cadence-planning`, `cadence-issue-generation`, or `cadence-execution`, the lifecycle semantics are still interpreted per this file.
2. Phase skills should check prerequisites before starting this phase's work, rather than assuming upstream phases have already completed.
3. When prerequisites are not met, or the current target is unclear, do not automatically switch to another phase based on repository state; first ask the user to supplement the target file, task, or explicitly specify a more appropriate phase.
4. After a phase skill completes its local work, it should continue advancing per the handoff or confirmation points defined in this file; do not treat itself as the flow endpoint.
