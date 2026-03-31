---
name: cadence-execution
description: Cadence's execution phase. Advances implementation, validation, and status writeback based on existing and continuable issue files; entering this phase when directly requested by the user is also considered entering Cadence. If there is no clear issue file or the target is unclear, ask the user to specify.
---

# Cadence Execution

Within `Cadence`, advance implementation, validation, and status writeback based on existing issue files.

## Lifecycle Binding

1. This skill serves as the `Execution` phase of `Cadence`.
2. When the user directly specifies this skill, it should also be treated as "entering `Cadence` from the execution phase."
3. Phase prerequisites, confirmation points, and handoff are governed by [../using-cadence/references/cadence-lifecycle.md](../using-cadence/references/cadence-lifecycle.md).
4. If the current request is entering `Cadence` directly from this phase, output the shared lifecycle-defined entry prompt before starting execution of issues in the issue file.
5. If the current request reaches a shared lifecycle-defined terminal state in this phase, or the user explicitly ends the current flow in this phase, first output the shared lifecycle-defined exit prompt, then resume default execution mode.

## Shared Source of Truth

1. Lifecycle, confirmation points, default handoff, and terminal states are governed by `../using-cadence/references/cadence-lifecycle.md`.
2. Issue file field structure, default values, and annotation examples are governed by `../using-cadence/assets/issue-template.toml`.
3. `../using-cadence/scripts/cadence_validate.py` provides basic structural checks and execution-stage writeback boundary checks for issue files, serving as a mechanical guardrail.
4. Whether the current issue can continue execution, whether blocking semantics hold, whether each issue has completed the required reviewer chain, and whether validation and regression strategies are reasonable, are the responsibility of the main agent, reviewers, and the current phase process logic.
5. The shared `available capabilities` gate for the entire flow is governed by `../using-cadence/references/cadence-lifecycle.md`; this document only supplements `Execution` phase dispatch, output, and `notes` writeback requirements.
6. If the current round's adaptation conclusion is `none-applicable` and the current issue undergoes status writeback, the main agent must write the reason into the corresponding issue's `notes`.

## Quick Flow

1. Prerequisite check: Read the issue file specified by the user or corresponding to the current task; if there are multiple candidates or the target cannot be safely determined, ask the user to specify first. Read the matching `.cadence/plan/*.md` if needed.
2. Select frontier: Choose the currently executable issues to advance this round based on "Status Advancement and Execution Order" below.
3. Dispatch strategy: Determine the execution method for each selected issue (implementer subagent or main agent execution) and the scheduling method between multiple frontier issues (sequential or parallel) based on "Subagent Dispatch" below.
4. Execution loop: For selected issues, perform implementation, required reviewer reviews (first `spec-reviewer`, then `code-reviewer`), final validation, regression, and status writeback.
5. Rolling recalculation: After integrating this round's results, recalculate the executable set and continue advancing.
6. Wait or end: If all executable issues have completed required reviewer reviews and necessary validation and status writeback, end the current `Cadence` flow per the shared lifecycle; if there are no currently executable issues but `blocked` issues or pending user decisions still exist, remain in the `Execution` phase waiting, do not automatically exit the flow.

## Subagent Dispatch

### Default Strategy

- Subagents are one of the default execution methods in the `Execution` phase.
- Issue-level execution method: For each currently executable frontier issue, default to dispatching an implementer subagent; only switch to main agent execution when the main agent execution exemption conditions defined in this section are met.
- A single-chain scenario is not an exemption reason by itself; even with only one frontier issue, default to dispatching an implementer subagent for that issue.
- Multi-frontier scheduling method: If there are 2 or more mutually independent frontier issues, default to dispatching multiple implementer subagents separately and advancing with parallel scheduling; only switch to sequential scheduling when the parallel fallback conditions defined in this section are met, and further fall back to main agent execution for individual issues if necessary.
- The main agent is always the controller of the current `Cadence` flow, responsible for selecting issues, updating issue file status, integrating results, and responsible for issue-level final `validate_by` / `regress_by` command selection, result review, pass determination, status writeback, and `notes`.
- The goal of dispatching subagents is to reduce main agent context pollution and, when appropriate, process mutually independent work in parallel.
- Default dispatch unit is the issue; only add subagents within a single issue when the current issue should not be split into a new issue but still contains bounded auxiliary subtasks that don't break single-state advancement.
- Subagent dispatch only targets issues selected by the main agent for the current round; do not default to handing an entire dependency chain to the same subagent for continuous advancement.
- Before each issue enters issue-level final `validate_by`, it must by default complete the `spec-reviewer -> code-reviewer` two-reviewer gate.
- When the current issue uses the subagent chain, default advancement order is `implementer -> spec-reviewer -> code-reviewer -> main agent enters issue-level final validation / schedules regression as appropriate -> (optional) command execution -> main agent final determination / writeback`.
- If main agent execution exemption applies and implementation is done locally by the main agent, only the `implementer` dispatch is exempted; `spec-reviewer` or `code-reviewer` are not exempted.

### Judgment Order

- First determine the execution method for each frontier issue: default to dispatching an implementer subagent; only switch to main agent execution when main agent execution exemption conditions are met.
- Then determine the scheduling method for multiple frontier issues: if there are 2 or more frontier issues that are mutually independent, have no shared write scope, no shared runtime state, and no serial dependencies, default to parallel scheduling.
- If there is only one frontier issue, there is no "sequential or parallel" scheduling choice; advance directly by that issue's execution method.
- When parallel prerequisites are not met, do not use parallel scheduling; switch to sequential scheduling; if an issue also meets main agent execution exemption conditions, that issue falls back to main agent execution directly.
- Even when parallel prerequisites are met, if "parallel fallback conditions" below are also triggered, still fall back to sequential scheduling, and further fall back to main agent execution for individual issues if necessary.

### When Subagents Are Appropriate

- 2 or more selected issues this round are mutually independent and can enter parallel scheduling without sharing write scope or runtime state.
- The current issue contains a clearly bounded, contextually closed, independently verifiable subtask suitable for processing in a new context.
- Independent investigation, targeted reproduction, directed validation, or narrow-scope implementation is needed, and results can be uniformly integrated by the main agent.

### Parallel Scheduling Fallback Conditions

- The following conditions cause "multi-frontier default parallel scheduling" to fall back to sequential scheduling, and further fall back to main agent execution if necessary:
- Multiple candidate tasks share files, share state, or have strong sequential dependencies — subagents would interfere with each other.
- The current step requires the main agent to continuously make global judgments, cross-module tradeoffs, or continuous interaction — splitting into parallel subagents would amplify coordination costs.
- A candidate issue's boundaries, write scope, or validation entry points are not yet clear — the main agent temporarily cannot safely provide sufficient context for multiple subagents simultaneously.
- When some candidate issues are suitable for subagents and others are not, subagents can be dispatched only for suitable issues, with remaining issues processed sequentially or locally; do not force splitting for the sake of formal "full parallelism."

### Main Agent Execution Exemption Conditions

- The following conditions can serve as exemption conditions for default implementer subagent dispatch, switching to main agent execution:
- The current change is extremely small, low-risk, and dispatch and integration costs are clearly higher than direct processing benefits, e.g., single-file, few-line fix.
- The current step depends on global judgment, cross-module tradeoffs, or continuous interaction — splitting to a subagent would instead increase coordination costs.
- The current write scope is highly coupled with changes the main agent has not yet integrated — splitting would easily produce high coordination costs or erroneous overwrites.
- The current issue's boundaries, write scope, or validation entry points are not yet clear — the main agent temporarily cannot safely provide sufficient context.
- The subagent tool is currently unavailable, not enabled, or has failed consecutively on that issue — retry benefits are clearly lower than main agent execution.
- Main agent execution exemption only affects "who does the implementation"; it does not affect reviewer gates — after main agent implementation completes, `spec-reviewer = PASS` must still be obtained first, then `code-reviewer = PASS`, before entering issue-level final `validate_by`.

### Dispatch Requirements

- Each subagent uses a new context and does not inherit the entire conversation history; the main agent only provides the minimum context needed to complete the current task.
- Instructions must include at least: current issue `id`, target outcome, clear scope, allowed write files or modules, dependencies, validation entry points, change constraints, and expected output.
- The main agent should directly provide the precise context needed for the current task; do not have subagents read back through the entire plan or entire conversation history on their own.
- If a section of issue contract, acceptance criteria, or current-round task text is critical to implementation success, paste it directly into the dispatch prompt; do not only give a file path for the subagent to find on its own.
- Before dispatching `implementer`, `spec-reviewer`, `code-reviewer`, or arranging issue-level `validate_by` / `regress_by` execution, the main agent should have completed the shared lifecycle-required current session `available capabilities` adaptation check and directly provide the capability context that needs to be continued to the subagent.
- Do not write any single `available capability` as an explicit prerequisite in shared issue contracts.
- During parallel scheduling, each subagent's write scope must not overlap; if write scopes overlap, switch to sequential scheduling or have the main agent handle uniformly.
- Do not concurrently run multiple implementer subagents on the same write scope; parallel scheduling is only for mutually independent problem domains or issues.
- After an implementer subagent returns, or after main agent local implementation completes, the main agent is responsible for reviewing results, handling concerns, chaining the reviewer process, and uniformly executing final writeback.
- Subagents can handle implementation, self-testing, targeted validation, issue-level final `validate_by` / `regress_by` command execution, or reviewer reviews; the main agent retains final pass determination and status writeback authority, and does not delegate issue-level final adjudication directly to subagents.
- In the reviewer process, first have `spec-reviewer` check whether the current issue meets scope and completion conditions, then have `code-reviewer` check for defect risks, regression risks, test gaps, and implementation quality risks.
- Unless the user explicitly exempts the current issue's reviewer gates, no issue may skip `spec-reviewer` or `code-reviewer`; single-chain, low-risk, main agent execution, or implementer dispatch failure are not reasons to skip reviewers.
- If an `available capability` is currently unavailable, not enabled, or not suitable for the current subtask, do not treat it as a blocking reason; continue advancing via other feasible methods in the current process.
- If exemption conditions are met and execution falls back to the main agent, the reason should be explicitly stated in the current round's execution notes, avoiding making "no subagent dispatched" an implicit behavior.

### Prompt Skeletons

#### Implementer Subagent

Can be assembled directly from the following skeleton:

```text
You are the implementer subagent for the current Cadence issue.

Issue: <id>
Target outcome: <outcome to achieve this round>
Task text:
- <directly paste the most critical issue contract, acceptance criteria, or task text for this round>

Scope:
- What to do: <...>
- What not to do: <...>

Allowed writes:
- <file/module/...>

Dependencies:
- <id or none>

Implementation requirements:
- If you have questions about requirements, acceptance criteria, implementation strategy, dependencies, or assumptions, raise them before starting
- Only modify within allowed write scope
- You are not in an empty repository; do not revert others' changes
- Follow existing codebase patterns; do not casually refactor structure outside the issue scope
- First complete a current session `available capabilities` adaptation check; if there are applicable capabilities, prioritize calling them and record usage in output; if judgment is `none-applicable`, explicitly state the reason
- Do not skip the adaptation check just because regular command entry points exist; if a capability is unavailable, do not treat it as a blocking reason
- Issue-level final `validate_by` is led by the main agent which is responsible for final adjudication; you by default only do implementation-phase self-testing, local validation, or auxiliary checks explicitly requested by the main agent — you do not by default assume issue-level final `validate_by` / `regress_by` pass determination
- If you lack context necessary to complete the current task, do not guess — return NEEDS_CONTEXT directly
- If you find the task requires unexpected architectural decisions, large-scale understanding beyond provided context, or unplanned refactoring, return BLOCKED or DONE_WITH_CONCERNS directly

Self-check during implementation:
- Have you fully covered the required behavior and edge cases
- Have you only implemented what was requested, with no extra functionality
- Are naming, responsibility separation, and interfaces clear
- Do tests or self-tests actually verify behavior

Validation entry points:
- validate_by: <...>
- regress_by: <... or none>

Expected output:
- Return per "Subagent Output Format / Implementation" below
```

#### Reviewer Subagent

Can be assembled directly from the following skeleton:

```text
You are the reviewer subagent for the current Cadence issue.

Review type: <spec-reviewer | code-reviewer>
Issue: <id>
Review target: <why this review is needed>
Task text:
- <directly paste the issue's key contract, acceptance criteria, or task text>

Review scope:
- Only check changes within the current issue scope and allowed write scope
- Read-only by default; do not directly modify files unless the main agent explicitly requests fixes
- Do not read back through the entire plan or entire conversation history; only use context provided by the main agent
- First complete a current session `available capabilities` adaptation check; if there are applicable capabilities, prioritize calling them and record usage in output; if judgment is `none-applicable`, explicitly state the reason
- Do not skip the adaptation check just because regular reading and command entry points exist; if a capability is unavailable, do not treat it as a blocking reason

Check focus:
- spec-reviewer:
  - Do not trust the implementer's self-assessment; independently read the code and check item by item against the task text and issue contract
  - Check for missing requirements, extra implementation, or misunderstandings of requirements
  - If issues are found, try to provide file:line evidence
- code-reviewer:
  - Only execute after `spec-reviewer` has passed
  - Focus on correctness defects, behavioral regression risks, edge case omissions, test gaps, and implementation risks
  - Additionally check naming, responsibility separation, interface clarity, whether the plan's file structure is significantly deviated from, and whether this change creates overly large new files or significantly amplifies existing files

Expected output:
- Return per "Subagent Output Format / Reviewer" below
```

### Subagent Output Format

#### Implementation

```text
STATUS: <DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED>
SUMMARY: <one-sentence result description>
CHANGED_FILES:
- <path> or none
CAPABILITY_USE:
- <used capability + purpose> or none-applicable: <reason>
SELF_CHECK:
- <self-test or local validation performed; write none if none>
CONCERNS:
- <none or specific concern>
NEEDED_CONTEXT:
- <none or missing context>
BLOCKERS:
- <none or blocking reason>
```

#### Reviewer

```text
REVIEW_TYPE: <spec-reviewer | code-reviewer>
DECISION: <PASS | FAIL>
SUMMARY: <one-sentence conclusion>
CAPABILITY_USE:
- <used capability + purpose> or none-applicable: <reason>
FINDINGS:
- <none or issues item by item; try to include file:line numbers, and prefix with [critical|important|minor]>
SUGGESTED_NEXT_STEP:
- <none or suggested action>
```

### Return Status and Review

- Implementation subagents should explicitly return one of: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`.
- `DONE`: Enter the reviewer process.
- `DONE_WITH_CONCERNS`: Main agent processes concerns first; if the current issue can still proceed, enter the reviewer process.
- `NEEDS_CONTEXT`: Main agent supplements missing context before re-dispatching; do not let the subagent continue working with unresolved questions.
- `BLOCKED`: Main agent supplements context based on the blocking reason, narrows scope, re-dispatches to a more suitable subagent, or falls back to main agent execution; do not retry in-place under the same conditions.
- Both implementation and reviewer subagents must explicitly return `CAPABILITY_USE`; if the conclusion is `none-applicable`, the main agent should still review whether the reason is valid, supplementing to issue `notes` or re-dispatching as necessary.
- Whether the current issue is completed by `implementer` or locally by the main agent, before entering issue-level final `validate_by`, `spec-reviewer = PASS` must be completed first, then `code-reviewer = PASS`; unless the user explicitly exempts, it must not be skipped.
- Reviewer subagents should return `DECISION` and `FINDINGS` per the format above.
- `DECISION = PASS`: If the current reviewer is `spec-reviewer`, continue to `code-reviewer`; if the current reviewer is `code-reviewer`, enter main agent integration and final validation.
- `DECISION = FAIL`: Fix `FINDINGS` first, then re-execute the same reviewer review.
- Reviewer order is fixed: first `spec-reviewer`, then `code-reviewer`; `code-reviewer` should not execute before `spec-reviewer` has passed; if any reviewer raises issues, fix first then re-review.

### Failure and Degradation

- If the subagent tool is unavailable, not enabled, or the dispatch call directly fails, first ask the user whether the current execution needs subagents enabled; if the user doesn't enable or can't enable, continue with main agent execution.
- If a subagent returns `needs_context`, `blocked`, or similar failure status, the main agent should prioritize supplementing context, narrowing scope, or re-dispatching to a more suitable subagent; if still not suitable, fall back to main agent execution.
- If a reviewer subagent finds issues, prioritize having the corresponding implementer subagent or a dedicated fix subagent handle them; if the subagent chain is no longer suitable, fall back to main agent execution.
- If reviewer subagent dispatch fails, the current reviewer chain is not suitable, or the implementation flow falls back to main agent execution, the main agent must still re-schedule `spec-reviewer` and `code-reviewer` for the current issue; before both reviewer gates pass, do not enter issue-level final `validate_by`. If the current session truly cannot complete reviewer subagent dispatch, the user must first be informed and asked whether to exempt the reviewer gates.
- Subagent failure by default should not block the entire `Execution` flow; as long as main agent execution can still continue, it should be compatible with fallback rather than deadlocking on the dispatch chain.
- If subagent failure causes the current issue to be unable to continue advancing, write back `status` or `notes` per the actual situation; do not hide the failure reason.

## Status Advancement and Execution Order

### File and Modification Boundaries

- Issue file paths are of the form `.cadence/issue/YYYY-MM-DD-<feature-name>.toml`; field structure, status values, and sentinel values are governed by `../using-cadence/assets/issue-template.toml`.
- The execution phase only allows updating `status`, `validate_status`, `regress_status`, and `notes`; whether reviewer gates have passed belongs to execution semantics and is not expressed through new issue fields.
- During execution, if status fields or `notes` need to reflect actual work, the current issue file must be immediately written back; if reviewer gates cannot be completed due to tool or environment reasons, the reason and user decision should also be recorded in `notes`.
- After each writeback, the file must be re-read and the following items directly verified:
  - File is still parseable as `TOML`
  - Current modification only involves `status`, `validate_status`, `regress_status`, and `notes`
  - `id` is still unique
  - `sequence` is still a unique positive integer
  - Fields defined as arrays in the template remain arrays
  - Status field values conform to allowed values in the template
- Can directly run `python3 ../using-cadence/scripts/cadence_validate.py issue <path>` for basic structural checks; if a pre-writeback snapshot is retained, can also run `python3 ../using-cadence/scripts/cadence_validate.py execution-write --before <before> --after <after>` to verify this writeback only modified allowed fields. Higher-level execution semantics are still the responsibility of the main agent and reviewers; if the script is unavailable, manually verify per the equivalent rules above.

### Contract Issues and User Decisions

- If during execution it is discovered that the current issue's contract fields are incorrect, missing, have wrong granularity, have incorrect dependency relationships, or `validate_by` / `regress_by` / `regress_timing` are clearly inconsistent with the actual plan, treat that issue as contract-blocked.
- Status writeback, user explanation, and subsequent phase selection after contract blocking are handled uniformly per "Contract Issues and User Decisions" in `../using-cadence/references/cadence-lifecycle.md`.

### Selection Order

- Execution scope includes:
  - Issues with `status != "done"`
  - Issues with `status = "done"` but `validate_status != "passed"`
  - Issues with `status = "done"`, `validate_status = "passed"`, `regress_timing = "before_fanout"`, `regress_by != "none"`, and `regress_status != "passed"`
  - When all issues' `status` is `done`, issues with `regress_by != "none"` and `regress_status != "passed"`
- For newly created issue files or user-driven updated issue files, only begin executing incomplete issues when the user explicitly requests continuing the current task, or explicitly agrees to enter the execution phase at a confirmation point.
- By default, only select issues to advance this round from the current executable frontier issue set.
- Prioritize resuming any issue whose status field is already `in_progress`, to avoid leaving half-finished work hanging until the end.
- When there are no `in_progress` issues, if there are issues with `status = "done"` but `validate_status != "passed"`, prioritize completing final validation for these issues.
- If there are no `in_progress` issues to resume, and there are issues with `regress_timing = "before_fanout"`, `regress_by != "none"`, `status = "done"`, `validate_status = "passed"`, but `regress_status != "passed"`, prioritize completing these regressions before unlocking downstream issues that depend on them.
- When all issues' `status` is `done`, if there are still issues with `regress_by != "none"` and `regress_status != "passed"`, continue completing remaining regressions.
- In all other cases, only select issues with `depends_on = []` or whose dependency issues have `status = "done"` and `validate_status = "passed"`, and if the prerequisite issue's `regress_timing = "before_fanout"` then its `regress_status = "passed"`, and whose own `status = "todo"`.
- Subsequent issues in the same dependency chain only enter the executable set after the prerequisite issue has `status = "done"` and `validate_status = "passed"`, and `before_fanout` regression has been completed and necessary writeback performed as needed.
- Issues with `status = "blocked"` are skipped by default until the block is resolved and written back to `todo` or `in_progress`.
- When multiple candidates simultaneously qualify, process in ascending `sequence` order; if `sequence` is the same, treat it as an issue contract error. `id` can be used as a fallback for display-level sorting if necessary, but should not be used to mask duplicate `sequence` values.
- If there is only one frontier issue in the current executable set (including single-chain scenarios), advance directly by that issue's execution method: default to dispatching an implementer subagent; only switch to main agent execution when main agent execution exemption conditions above are met.
- If there are 2 or more mutually independent frontier issues in the current executable set, default to dispatching implementer subagents separately and advancing with parallel scheduling; only switch to sequential scheduling when parallel scheduling fallback conditions above are met, and further fall back to main agent execution for individual issues if necessary.
- After any parallel issue completes integration, the main agent should immediately reassess the executable set; if new executable issues emerge as a result, proceed directly to the next selection without waiting for other parallel issues to finish.

### Status Advancement

- Before starting an issue, change `status` to `in_progress`.
- After implementation, necessary fixes, and required reviewer processes are complete, and the current issue is ready to enter issue-level final `validate_by`, write `status` back to `done`.
- Issue-level final `validate_by` and `regress_by` commands can be executed by the main agent directly or dispatched to subagents for execution as needed; regardless of whether execution is delegated, final pass determination and status writeback are the main agent's responsibility.
- When executing final validation, first change `validate_status` to `in_progress`.
- If `validate_by` passes, change `validate_status` to `passed`.
- If `validate_by` fails and the current issue still needs further modification, change `validate_status` to `failed` and write `status` back to `in_progress`.
- If `validate_by` fails and is blocked by external dependencies, environment, permissions, or contract issues, change `validate_status` to `failed` and change `status` to `blocked`; record the blocking reason, resolution conditions, and suggested follow-up handling in `notes`.
- For issues with `regress_timing = "before_fanout"`, as long as their `validate_status = "passed"` and `regress_status != "passed"`, the regression should be completed before continuing to unlock their downstream issues.
- When executing regression, first change the corresponding `regress_status` to `in_progress`.
- If `regress_by` passes, change `regress_status` to `passed`.
- If `regress_by` fails and implementation still needs modification, change `regress_status` to `failed` and write the fixing issue's `status` back to `in_progress`.
- If `regress_by` fails and is blocked by external dependencies, environment, permissions, or contract issues, change `regress_status` to `failed` and write the fixing issue's `status` back to `blocked`; record the blocking reason and resolution conditions in `notes`.
- Before starting validation or regression, first change the corresponding status field to `in_progress`.
- After a single issue completes, immediately update that issue's status; do not wait until all issues are finished for a batch update.
- Do not mark `validate_status` or `regress_status` as `passed` before the declared checks have actually passed.
- If development is blocked, use `status = "blocked"` and record the blocking reason and resolution conditions in `notes`.
- After all `status` values are `done`, catch up on remaining `regress_status` values, writing results back per issue immediately.

## Resources

- [../using-cadence/references/cadence-lifecycle.md](../using-cadence/references/cadence-lifecycle.md): `Cadence` shared lifecycle, confirmation points, and handoff rules
- `../using-cadence/assets/issue-template.toml`: Shared issue template and field schema
- `../using-cadence/scripts/cadence_validate.py`: Shared mechanical guardrail for issue file basic structure and execution-stage writeback boundary checks
