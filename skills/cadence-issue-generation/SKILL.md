---
name: cadence-issue-generation
description: Cadence's issue generation phase. Generates issue files for the current task based on plan files; entering this phase when directly requested by the user is also considered entering Cadence. If there is no clear plan file or the target is unclear, ask the user to specify.
---

# Cadence Issue Generation

Within `Cadence`, convert plan files into reviewed issue files.

## Lifecycle Binding

1. This skill serves as the `Issue Generation` phase of `Cadence`.
2. When the user directly specifies this skill, it should also be treated as "entering `Cadence` from the issue generation phase."
3. Phase prerequisites, confirmation points, and subsequent handoff are governed by [../using-cadence/references/cadence-lifecycle.md](../using-cadence/references/cadence-lifecycle.md).
4. If the current request is entering `Cadence` directly from this phase, output the shared lifecycle-defined entry prompt before starting this phase's issue generation.
5. If the current request reaches a shared lifecycle-defined terminal state in this phase, or the user explicitly ends the current flow in this phase, first output the shared lifecycle-defined exit prompt, then resume default execution mode.

## Shared Source of Truth

1. Lifecycle, confirmation points, default handoff, and terminal states are governed by `../using-cadence/references/cadence-lifecycle.md`.
2. Issue file field structure, default values, and annotation examples are governed by `../using-cadence/assets/issue-template.toml`.
3. `../using-cadence/scripts/cadence_validate.py` provides basic structural checks for issue files, serving as a mechanical guardrail.
4. Semantic validation such as plan consistency, issue decomposition quality, validation strategy, dependency design, and executability is the responsibility of the main agent and `issue-reviewer`.
5. The shared `available capabilities` gate for the entire flow is governed by `../using-cadence/references/cadence-lifecycle.md`; this document only supplements `Issue Generation` phase writeback and reviewer output requirements.
6. If this phase's adaptation conclusion is `none-applicable`, the main agent must explicitly state the reason in the current round's issue generation notes or `issue-reviewer` output; do not implicitly skip.

## Quick Flow

1. Prerequisite check: Determine and read the `plan/*.md` to be processed this time, and complete a current session `available capabilities` adaptation check per the shared lifecycle; if the user has explicitly specified a plan file, use that file first; if there are multiple candidates or the target cannot be safely determined, ask the user to specify first. If the corresponding issue file already exists, read it as well.
2. Issue decomposition: Generate or adjust issue entries per "Issue Decomposition Rules" and "Testing and Validation Fields" below.
3. Write draft: Per "Writing" below, first write the issue draft directly to `issues/YYYY-MM-DD-<feature-name>.toml`, and perform basic structural validation on the current file; before `issue-reviewer` passes, the current content at that path is only treated as the current phase draft, not as a confirmed issue input.
4. Reviewer review: Dispatch the `issue-reviewer` subagent to directly review the current issue draft; if review does not pass, the main agent modifies the same issue file per `issue-reviewer` rules below, re-reviews, or clarifies with the user.
5. Final self-check: After review passes, the main agent reads back the current issue file to complete the final structural self-check.
6. Confirmation point: After the current issue file passes review and completes self-check, present the issue file path, key change summary, key issue items, and review results to the user, and explicitly ask: `Reply confirm to enter cadence-execution.`
7. In-confirmation-point feedback: Before receiving explicit confirmation, supplementing, deleting, reordering, clarifying, or general discussion continues to be handled within the current `Issue Generation` confirmation point, without entering the downstream phase.
8. Automatic handoff: Only after receiving explicit confirmation, automatically transition to `cadence-execution` based on the current issue file.

## issue-reviewer

- `issue-reviewer` executes after the current issue draft is written to the target `issues/*.toml`, responsible for reviewing the current issue draft per the review rules below, and checking whether the target path and current file content match.
- `issue-reviewer` uniformly handles content review, structural checks, target path checks, and issue file content validation for the Issue Generation phase; do not additionally split other reviewer processes, and do not add duplicate self-check chains in parallel.
- `issue-reviewer` is read-only by default; it does not directly write to issue files, nor does it confirm entering `Execution` on behalf of the main agent.
- The main agent provides `issue-reviewer` with minimum necessary context: current plan file path, current plan full text or key sections, issue target path, current issue file full text, structural requirements from `../using-cadence/assets/issue-template.toml`, and the review rules below.
- `issue-reviewer` does not read back through the entire conversation history; it only performs independent review based on context provided by the main agent, the plan file, and the current issue file.
- `issue-reviewer` also follows the shared lifecycle's current session `available capabilities` gate before reviewing; if the conclusion is `none-applicable`, the reason must be explicitly stated in the output.
- `issue-reviewer` is also responsible for target path checks and issue file content validation, including: the issue target path has been properly placed at `issues/YYYY-MM-DD-<feature-name>.toml`, the current issue file can be directly parsed as `TOML`, content is consistent with template structure, current issue content is consistent with the task corresponding to the target path, `sequence` is a unique positive integer, no placeholder residue, no obvious format corruption, and `regress_by` / `regress_timing` / `regress_status` linkage is correct.
- Each blocking issue in `FINDINGS` must have a label: `[auto_fixable]` means the main agent can fix it directly without introducing unconfirmed information, changing key scope, or making key decomposition or key validation strategy decisions on behalf of the user; `[needs_user_decision]` means the user must be consulted first.
- If `issue-reviewer` raises issues, the main agent by default only auto-revises the current issue file based on `[auto_fixable]` `FINDINGS`, then re-initiates the same type of review; auto-revision executes at most 3 rounds.
- If any `[needs_user_decision]` issue appears, or the auto-revision limit is reached without passing, the main agent must stop auto-revision and clarify with the user.

### Review Rules

- Only flag defects that would cause actual problems in subsequent `Execution`; wording optimization, style preferences, or non-blocking improvement suggestions are not blocking issues.
- Review focus is calibrated across four categories: completeness, consistency with the plan, issue decomposition quality, and executability.
- If an implementer would do the wrong thing, miss plan requirements, or get stuck during the execution phase because of it, it's an issue; otherwise, it usually isn't.
- Unless there is an obviously severe gap, such as missing plan requirements, scope creep, incorrect dependencies, distorted validation entry points, placeholder content, or issue granularity so vague it cannot be executed, tend to give a `PASS`.
- The issue file must be directly parseable as `TOML`, and top-level fields, `[[issue]]` blocks, and required fields must all exist and be non-empty per template requirements.
- `id` must be unique; `sequence` must be a unique positive integer; fields defined as arrays in the template must maintain array form; status fields, `regress_timing`, and sentinel values must conform to allowed values in the template.
- Issue granularity should conform to "Issue Decomposition Rules" below; if an issue is clearly too coarse, too fine, has incorrect dependencies, or cannot be independently verified, it should be flagged as an issue.
- `scope`, `touch_points`, `depends_on`, `done_when`, `validate_by`, `regress_by`, `regress_timing`, `notes` should be consistent with current plan facts and only carry confirmed information.
- Task-specific content in issue files should be prioritized from confirmed content in the current plan directly; if the plan doesn't explicitly state it and it can't be reasonably inferred from the overall plan, it should be flagged as an issue.
- `sequence` should express default execution order; it only determines default precedence when multiple issues have simultaneously met dependencies and are all executable; it does not replace `depends_on`.
- `done_when` should state outcomes, not vague processes; `validate_by` and `regress_by` should conform to the selection order and writing requirements in "Testing and Validation Fields" below; `regress_timing` must match risk surface and dependency fanout.
- When `regress_by = "none"`, `regress_status` must be `not_needed`; when `regress_by != "none"`, `regress_status` initial value must be `not_run`.
- Issue file content should be fully closed, covering required issues, dependencies, and descriptions, with `TODO`, `TBD`, placeholders, and other unfinished sections cleared.
- If an engineer were to enter `Execution` directly with this issue file, they would still likely get stuck due to ambiguity, contradictions, missing validation entry points, or incorrect dependencies — this should be flagged as an issue.

Can be assembled directly from the following skeleton:

```text
You are the issue-reviewer subagent for the current Cadence Issue Generation.

Plan file path:
- <plan/...>

Plan content:
<current plan full text, or explicit instruction to read the plan file directly>

Issue target path:
- <issues/...>

Issue file content:
<current issue file full text, or explicit instruction to read the target issue file directly>

Review requirements:
- Only review per the plan content, issue template structure, and review rules provided by the main agent
- Read-only by default; do not directly modify issue files
- Do not trust the drafter's self-assessment; directly check issue file content item by item
- First complete a current session `available capabilities` adaptation check; if there are applicable capabilities, prioritize calling them and record usage in output; if judgment is `none-applicable`, explicitly state the reason
- Do not skip the adaptation check just because regular reading and command entry points exist; if a capability is unavailable, do not treat it as a blocking reason
- Only flag defects that would cause actual problems in subsequent execution; do not fixate on wording, style, or non-blocking optimization suggestions
- Calibrate across four categories: completeness, consistency with plan, issue decomposition quality, and executability
- Unless there is a severe gap that would cause an implementer to do the wrong thing, miss requirements, or get stuck in execution, tend to give PASS
- Each blocking issue must be labeled as `[auto_fixable]` or `[needs_user_decision]`

Check focus:
- Whether the issue target path has correctly landed at `issues/YYYY-MM-DD-<feature-name>.toml`, and whether naming conforms to conventions
- Whether the current issue file can be directly parsed as `TOML`
- Whether current issue content is consistent with the task corresponding to the target path
- Whether top-level fields, `[[issue]]` blocks, and required fields exist and are non-empty
- Whether `id` is unique, `sequence` is a unique positive integer, array fields maintain array form, status fields, `regress_timing`, and sentinel values are valid
- Whether each issue conforms to granularity rules and has clear scope, primary completion conditions, and primary validation entry points
- Whether `depends_on` only expresses hard dependencies, with no incorrect chains or missing dependencies
- Whether issue content is consistent with plan facts and whether any plan requirements that must be reflected in issues are missing
- Whether `done_when`, `validate_by`, `regress_by` are based on truly executable, reproducible entry points
- Whether `regress_by`, `regress_timing`, and `regress_status` linkage is correct
- Whether there are `TODO`, `TBD`, placeholders, unfounded jumps, or unclosed content
- Whether an engineer entering execution directly with this issue file would get stuck due to ambiguity, contradictions, or missing information

Expected output:
- Return per the format below
```

Output format:

```text
REVIEW_TYPE: issue-reviewer
DECISION: <PASS | FAIL>
SUMMARY: <one-sentence conclusion>
CAPABILITY_USE:
- <used capability + purpose> or none-applicable: <reason>
FINDINGS:
- <none or issues item by item; each prefixed with `[auto_fixable]` or `[needs_user_decision]`, and try to include issue id, section name or location, explaining why it would affect Execution>
SUGGESTIONS:
- <none or non-blocking suggestions>
SUGGESTED_NEXT_STEP:
- <none or suggested action>
```

## Issue Decomposition Rules

- One issue represents a clear outcome unit, not an implementation action.
- Each issue should have clear boundaries, primary completion conditions, and a primary validation path.
- Split by outcome, not by action.
- Split by dependency, not by file count.
- Split by validation, not by technical layer nouns.
- What can be independently delivered, independently verified, and independently written back, prioritize splitting apart.
- What must be delivered together, verified together, and judged complete together, prioritize merging.

### Default Granularity

- An appropriate issue should correspond to only one primary outcome, one primary validation entry point, and clear dependency boundaries.
- If an issue contains multiple mutually independent `done_when` conditions or multiple primary validation entry points, it is usually too coarse.
- If multiple issues are just implementation steps, file splits, or technical layer splits of the same outcome, they are usually too fine.
- If there are many issues, first check whether they are being mechanically split by process, file count, or technical layer nouns.
- If an issue simultaneously covers `schema + core logic + API/UI`, it is usually too coarse.
- If an issue's `done_when` needs to state multiple mutually independent "ands," it is usually too coarse.

### When to Split

- `done_when` is clearly not the same completion condition.
- `validate_by` or `regress_by` have different primary validation entry points.
- There are hard dependencies where the later part directly depends on the completed earlier part.
- The same issue simultaneously spans multiple high-risk surfaces, e.g., `schema`, core logic, interface contracts, user interface.
- One part might be `blocked`, but other parts should still proceed.
- After merging, the `scope` cannot accurately state what to do and what not to do.

### When Not to Split

- It's just multiple implementation steps for the same outcome.
- It just modifies multiple files but still serves the same outcome.
- It's just the natural components of "write code, add tests, update docs."
- It's just to make the number of issues more even.
- One part cannot be independently accepted and must be judged complete together with another part.

### Testing and Dependencies

- Do not default to splitting "add tests" into a separate issue.
- Feature implementation and its direct validation usually belong to the same issue.
- Only split test assets into a separate issue when the test asset itself is an independent deliverable, or when it becomes a common prerequisite for multiple subsequent issues.
- If multiple mutually independent outcome units are identified, and they don't share write scope, don't share runtime state, and have independent validation entry points, do not merge them into the same issue; prioritize splitting them into independent issues so the `Execution` phase can advance independently or in parallel.
- `depends_on` only writes hard dependencies, not suggested order.
- Default execution order goes in `sequence`; do not rely on file ordering to express precedence.
- What can be parallel should not be chained serially.
- Prefer depending on the nearest necessary prerequisite; do not create artificially long chains.
- If multiple issues all depend on the same prerequisite, they should each directly depend on that prerequisite's `id`.

## Writing

- Issue file path is derived from the plan file name as `issues/YYYY-MM-DD-<feature-name>.toml`.
- When first writing or revising an existing issue contract, first generate or rewrite the issue file based on `../using-cadence/assets/issue-template.toml`, replacing all placeholder values in it.
- Issue files must directly follow the field structure, status values, sentinel values, and annotation examples in `../using-cadence/assets/issue-template.toml`.
- When writing the actual issue file, all template placeholder values must be replaced with real task content.
- Each issue must have a `sequence`; recommended to use incrementing numbers like `10`, `20`, `30` for easy insertion of new issues later.
- Issue granularity and other contract fields should be determined in this phase; when first generating or revising an existing issue contract, status fields are re-initialized to template defaults and do not inherit running state from old issues; the execution phase only writes back `status`, `validate_status`, `regress_status`, and `notes`.
- Each non-trivial piece of work should be assigned to an issue before implementation begins.
- Each code change should be traceable to an issue `id`.
- After each issue file write, the file must be re-read and the following basic writeback constraints directly checked:
  - File can be directly parsed as `TOML`
  - Top-level fields, `[[issue]]` blocks, and required fields all exist and are non-empty per template requirements
  - `id` is unique
  - `sequence` is a unique positive integer
  - Fields defined as arrays in the template maintain array form, not degenerating into concatenated strings
  - Status fields, `regress_timing`, and sentinel values conform to allowed values in the template
  - `regress_by`, `regress_timing`, and `regress_status` linkage is correct
- Can directly run `python3 ../using-cadence/scripts/cadence_validate.py issue <path>` for basic structural checks; higher-level semantic validation is still the responsibility of the main agent and `issue-reviewer`. If the script is unavailable, manually verify per the equivalent rules.
- When generating or revising issues, task-specific content should prioritize reusing confirmed content from the current plan directly, without adding information not confirmed by the plan.
- "Must-pass checks" in the plan should be prioritized for assignment to each issue's `done_when`, `validate_by`, and `regress_by`.

## Testing and Validation Fields

### Core Principles

- Project native test code and its run commands are the default validation standard for code changes.
- If the current change requires stable testing and lacks a suitable project test vehicle, prioritize supplementing stable test assets, then use project commands to execute validation.
- Current session capabilities are primarily used for debugging, reproduction, targeted checks, and development-period assistance; they are not the default vehicle for long-term regression standards.
- Validation descriptions in plan and issue files must be written based on truly executable, reproducible entry points in the current repository.

### Three-Layer Model

1. `Repository Native Validation Entry Points`
   Refers to project native test assets and their run commands, including test code, test commands, and test targets.
   This is the default vehicle layer for `validate_by` and `regress_by`.

2. `Current Session Available Capabilities`
   Follows the shared lifecycle's definition of `available capabilities`, i.e., session tool capabilities that are enabled in the current session and actually callable by the agent, such as skills, MCP tools.
   This layer is primarily used for debugging, reproduction, and targeted checks; it is only written into validation steps as an exception when the repository truly lacks a suitable vehicle.

3. `Execution Auxiliary Strategies`
   Refers to execution strategies such as subagent parallel validation, independent review, problem reproduction task division.
   This layer helps improve efficiency and reliability, but should not be directly expressed as the primary description of `validate_by` or `regress_by`.

### Validation Level Selection

- Pure logic changes, prioritize unit tests.
- Module collaboration, interface contracts, or data flow changes, prioritize integration tests.
- Critical user paths or cross-page interaction changes, then consider e2e.
- Documentation, prompt text, lightweight configuration changes, prioritize existing commands, build checks, lint, or necessary fallback validation.

### Validation Method Selection Order

When selecting validation methods for `done_when`, `validate_by`, and `regress_by`, judge in the following order:

1. Existing focused test code and run commands within the repository.
2. If existing tests are insufficient, first supplement stable test assets at the appropriate level, then execute using project commands.
3. If the repository currently truly lacks a suitable project test vehicle, then prioritize finding low-level reproducible execution entry points, such as build, run, lint, type checking, or API calls.
4. If suitable entry points are still lacking, then use current session capabilities for temporary validation or targeted checks.
5. Only when all preceding methods are unsuitable, fall back to explicit manual checks.

### Writing Requirements

- `done_when` states outcomes, not vague processes.
- `validate_by` by default states project test commands; if tests need to be supplemented first, it should reflect "what tests to add" and "what commands to run."
- `regress_by` by default states project commands that need to be re-run; if none, write `none`.
- `regress_timing` by default maintains the template default `after_done`; only change to `before_fanout` when the current issue, after passing `validate_by`, would amplify regression costs if regression isn't run first before releasing multiple high-risk downstream issues. Typical scenarios include shared schema, core APIs, common foundation modules, or critical paths that affect multiple subsequent issues.
- If falling back to low-level reproducible execution entry points, current session capabilities, or manual steps, the reason should be explicitly stated.
- If current session capabilities help locate an issue, ultimately still try to supplement appropriate-level project tests and write project commands into validation fields.
- Subagents belong to execution auxiliary strategies and are not directly written as `validate_by` or `regress_by`; if needed, independent review arrangements can be recorded in `notes`.
- If there is currently no automated path, explicit manual validation steps are allowed, but steps must be specific, reproducible, and observable.

Reference writing examples:

- `validate_by`: `After adding auth module unit tests, run existing repository command pnpm test --filter auth`
- `validate_by`: `Run existing repository command pnpm test --filter payments to verify payments module related test cases`
- `validate_by`: `Run existing repository command pnpm test:e2e -- login.spec.ts to verify the login main path`
- `regress_by`: `Run existing repository command pnpm test:e2e -- login.spec.ts account.spec.ts to re-run login and account main paths`
- `regress_by`: `Run existing repository command pnpm test --filter auth && pnpm typecheck`

## Resources

- [../using-cadence/references/cadence-lifecycle.md](../using-cadence/references/cadence-lifecycle.md): `Cadence` shared lifecycle, confirmation points, and handoff semantics
- `../using-cadence/assets/issue-template.toml`: Shared issue template and field schema
- `../using-cadence/scripts/cadence_validate.py`: Shared mechanical guardrail for issue file basic structural checks
