---
name: cadence-planning
description: Cadence's planning phase. Drafts and confirms `plan/*.md` for the current task; entering this phase when directly requested by the user is also considered entering Cadence, and after the current flow is confirmed, it defaults to transitioning to `cadence-issue-generation`.
---

# Cadence Planning

Draft `Cadence Planning` for the repository and save it to the current project's `plan/` directory tree.

## Lifecycle Binding

1. This skill serves as the `Planning` phase of `Cadence`.
2. When the user directly specifies this skill, it should also be treated as "entering `Cadence` from the planning phase."
3. Phase prerequisites, confirmation points, and subsequent handoff are governed by [../using-cadence/references/cadence-lifecycle.md](../using-cadence/references/cadence-lifecycle.md).
4. If the current request is entering `Cadence` directly from this phase, output the shared lifecycle-defined entry prompt before starting to draft the plan.
5. Planning phase completion does not equal exiting `Cadence`; after confirming continuation in the current flow, default to automatically transitioning to `cadence-issue-generation`.
6. If the current request reaches a shared lifecycle-defined terminal state in this phase, or the user explicitly ends the current flow in this phase, first output the shared lifecycle-defined exit prompt, then resume default execution mode.

## Shared Source of Truth

1. Lifecycle, confirmation points, default handoff, and terminal states are governed by `../using-cadence/references/cadence-lifecycle.md`.
2. `plan/*.md` structural requirements are governed by `assets/plan-template.md`.
3. This document describes the `Planning` phase's drafting, review, self-check, and confirmation point handling rules.
4. Semantic validation for the planning phase is the responsibility of the main agent and `plan-reviewer`.
5. The shared `available capabilities` gate for the entire flow is governed by `../using-cadence/references/cadence-lifecycle.md`; this document only supplements `Planning` phase writeback and reviewer output requirements.
6. If this phase's adaptation conclusion is `none-applicable`, the main agent must explicitly state the reason in the current round's planning notes or `plan-reviewer` output; do not implicitly skip.

## File and Naming Conventions

1. Plan files are only written to the current local repository's `plan/` directory tree, not to global directories.
2. Plan file paths use `plan/YYYY-MM-DD-<feature-name>.md`, using the current local date.
3. `feature-name` is deterministically generated from the task title using the following rules: only keep lowercase letters, digits, and hyphens; unsafe or non-stably-transcribable characters are uniformly replaced with hyphens; consecutive hyphens are collapsed to one; leading and trailing hyphens are removed; maximum length is capped at 48 characters.
4. If the normalized `feature-name` is empty, use `task-<8-char-hash>` as a fallback name, where `hash` is stably generated from the original task title.
5. If the default target path already exists and the user has not explicitly requested reusing that file, append `-2`, `-3`, etc. as incrementing suffixes to the filename until an unoccupied path is obtained.
6. Use `assets/plan-template.md` as the complete plan template; the written result should fully replace body placeholders with actual content.
7. `<task>`: Use a short title for the current task, written into the plan body heading.
8. Plan content must only contain confirmed facts, constraints, and conclusions.
9. If a key piece of information is unclear, missing, or can only be filled by assumption, ask for clarification first; only draft or write related content after receiving a clear response.

## Quick Flow

1. Prerequisite check: First read confirmable code, documentation, and context within the repository, and complete a current session `available capabilities` adaptation check per the shared lifecycle; restate currently confirmed task facts in chat; only ask the user when information cannot be confirmed within the repository and would affect plan boundaries or strategy.
2. Clarify gaps: If key information gaps still exist after entering the planning phase, at most 3 mutually independent and necessary questions can be asked in the same round; questions should focus on information outside the repository that would affect plan boundaries or strategy.
3. Phase boundaries: The planning phase focuses on plan files and fact clarification, not code editing.
4. Write draft: After determining the target `plan/*.md` path, first draft the `Cadence Planning` initial draft using `assets/plan-template.md` and write it directly to the target `plan/*.md`; before `plan-reviewer` passes, the current content at that path is only treated as the current phase draft, not as a confirmed plan.
5. Reviewer review: Dispatch the `plan-reviewer` subagent to directly review the current `plan/*.md` draft; if review does not pass, the main agent modifies the same plan file per `plan-reviewer` rules below, re-reviews, or clarifies with the user.
6. Final self-check: After review passes, the main agent reads back the current `plan/*.md` to complete the final writeback self-check, confirming path, content, placeholder cleanup, and format state are all correct.
7. Confirmation point: After the current plan file passes review and completes self-check, present the plan file path, plan summary, and review results to the user, and explicitly ask: `Reply confirm to enter cadence-issue-generation.`
8. In-confirmation-point feedback: Entering `cadence-issue-generation` uses the user's explicit confirmation as the sole trigger; general discussion, supplementary requirements, continued analysis, or other non-confirmation responses continue to be handled within the current confirmation point.
9. Automatic handoff: After confirmation, automatically transition to `cadence-issue-generation` based on the current plan file.

## plan-reviewer

- `plan-reviewer` executes after the current plan draft is written to the target `plan/*.md`, responsible for reviewing the current plan draft per the review rules below, and checking whether the target path and current file content match.
- `plan-reviewer` uniformly handles content review, structural checks, target path checks, and plan file content validation for the Planning phase; do not additionally split other reviewer processes, and do not add duplicate self-check chains in parallel.
- `plan-reviewer` is read-only by default; it does not directly write to `plan/*.md`, nor does it confirm the plan on behalf of the main agent.
- The main agent provides `plan-reviewer` with minimum necessary context: currently confirmed task facts, plan target path, current plan full text, `assets/plan-template.md` structural requirements, and the review rules below.
- `plan-reviewer` does not read back through the entire conversation history; it only performs independent review based on context provided by the main agent and the current `plan/*.md`.
- `plan-reviewer` also follows the shared lifecycle's current session `available capabilities` gate before reviewing; if the conclusion is `none-applicable`, the reason must be explicitly stated in the output.
- `plan-reviewer` is also responsible for target path checks and plan file content validation, including: target path conforms to `plan/*.md` naming conventions, current file content is consistent with template structure, current file content is consistent with the task corresponding to the target path, no placeholder residue, no obvious format corruption.
- Each blocking issue in `FINDINGS` must have a label: `[auto_fixable]` means the main agent can fix it directly without introducing unconfirmed information, changing key scope, or making key strategy decisions on behalf of the user; `[needs_user_decision]` means the user must be consulted first.
- If `plan-reviewer` raises issues, the main agent by default only auto-revises the current `plan/*.md` based on `[auto_fixable]` `FINDINGS`, then re-initiates the same type of review; auto-revision executes at most 3 rounds.
- If any `[needs_user_decision]` issue appears, or the auto-revision limit is reached without passing, the main agent must stop auto-revision and clarify with the user.

### Review Rules

- Only flag defects that would cause actual problems in subsequent `Issue Generation` or `Execution`; wording optimization, style preferences, or non-blocking improvement suggestions are not blocking issues.
- Plans must not contain `TODO`, `TBD`, placeholders, unfinished sections, missing steps, or other obviously unclosed content.
- `Goals`, `Definition of Done (DoD)`, `Non-goals`, and `Scope` must have clear boundaries and not conflict with each other.
- `Impact`, `Constraints & Dependencies`, `Implementation Strategy`, `Phase Breakdown`, `Testing & Validation`, `Risks & Mitigations` should be consistent with current task facts.
- The plan must cover currently confirmed requirements without obvious scope creep, unfounded expansion, or over-engineering.
- `Implementation Strategy` should reflect the currently chosen approach; when important alternatives exist but are not adopted, the non-adopted approach should be explicitly stated.
- `Phase Breakdown` should be split by outcomes, dependencies, or milestones, not by mechanical implementation actions.
- `Phase Breakdown` and section descriptions should be sufficiently executable; if an engineer proceeding based on this would still likely get stuck due to ambiguity, contradictions, or missing information, it should be flagged as an issue.
- `References` should preferably be locatable files, line numbers, or explicit links; do not write vague untraceable sources.

Can be assembled directly from the following skeleton:

```text
You are the plan-reviewer subagent for the current Cadence Planning.

Task facts:
- <confirmed facts>

Plan target path:
- <plan/...>

Plan content:
<current plan full text, or explicit instruction to read the target plan file directly>

Review requirements:
- Only review per the facts, plan template structure, and review rules provided by the main agent
- Read-only by default; do not directly modify plan files
- Do not trust the drafter's self-assessment; directly check plan content section by section
- First complete a current session `available capabilities` adaptation check; if there are applicable capabilities, prioritize calling them and record usage in output; if judgment is `none-applicable`, explicitly state the reason
- Do not skip the adaptation check just because regular reading and command entry points exist; if a capability is unavailable, do not treat it as a blocking reason
- Only flag defects that would cause actual problems in subsequent issue generation or execution; do not fixate on wording, style, or non-blocking optimization suggestions
- Each blocking issue must be labeled as `[auto_fixable]` or `[needs_user_decision]`

Check focus:
- Whether the plan target path has correctly landed at `plan/*.md`, and whether naming conforms to conventions
- Whether current plan file content is consistent with the task corresponding to the target path
- Whether there is unconfirmed information, guessing, or fabrication
- Whether there are `TODO`, `TBD`, placeholders, unfinished sections, unfounded jumps, or missing steps
- Whether all template sections are complete, without placeholders, without unnecessary blanks
- Whether Goals / Scope / Non-goals / DoD are clear and consistent
- Whether all currently confirmed requirements are fully covered, without obvious scope creep or over-engineering
- Whether impact, dependencies, implementation strategy, and phase breakdown are consistent with current facts
- Whether an engineer entering issue generation and execution directly with this plan would get stuck due to ambiguity, contradictions, or missing information
- Whether testing and validation are based on truly executable, reproducible entry points
- Whether risks, fallbacks, and references are specific and actionable

Expected output:
- Return per the format below
```

Output format:

```text
REVIEW_TYPE: plan-reviewer
DECISION: <PASS | FAIL>
SUMMARY: <one-sentence conclusion>
CAPABILITY_USE:
- <used capability + purpose> or none-applicable: <reason>
FINDINGS:
- <none or issues item by item; each prefixed with `[auto_fixable]` or `[needs_user_decision]`, and try to include section name or location>
SUGGESTIONS:
- <none or non-blocking suggestions>
SUGGESTED_NEXT_STEP:
- <none or suggested action>
```

## Resources

- [../using-cadence/references/cadence-lifecycle.md](../using-cadence/references/cadence-lifecycle.md): `Cadence` shared lifecycle, confirmation points, and default handoff rules
- `assets/plan-template.md`: Complete plan template
