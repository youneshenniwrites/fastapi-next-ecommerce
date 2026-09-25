# Delivery skills

These repository skills package our existing delivery workflow. They use GitHub
Issues, the project board and the canonical PR template. They do not
create a background service or replace external Codex review.

| Invoke | Outcome |
| --- | --- |
| `$deliver-ticket` | Complete an authorized ticket using the saved Lean/Parallel mode and existing delivery skills. |
| `$product-discovery` | Product decisions, MVP boundary and exclusions recorded as a decision note before refinement. |
| `$refine-tickets` | Scoped linked stories, dependencies and a resumable issue handoff before coding. |
| `$create-pr` | Issue-linked PR with factual description, ownership, labels and review request. |
| `$preflight-review PR #42` | Apply repository Codex review lessons to the full diff and interacting regressions before external review. |
| `$self-review PR #42` | Full diff review, findings and verification; review-only requests do not edit code. |
| `$security-review PR #42` | Adversarial pass over auth, privilege, money, secrets and dependencies when relevant. |
| `$release-readiness` | Pre-deploy gates (envs, migrations, secrets, CI, smoke, Sentry, rollback) before a release. |
| `$architecture-review` | Structural placement, boundaries and contracts check before large epics; ADR when warranted. |
| `$address-codex-comments PR #42` | Verified fixes, evidence replies, resolved addressed threads and fresh review when needed. |
| `$update-delivery-board` | Board reconciled with actual delivery and acceptance evidence. |
| `$update-docs for PR #42` | Relevant README, Wiki or API documentation updated and verified. |

Replace #42 with the actual PR. Natural-language requests can also select the
skills. For new product ideas, run `$product-discovery` before `$refine-tickets`
so stories decompose from recorded decisions, not open questions.

Codex CLI/IDE provides `/skills` selection and `$skill-name` mentions;
these files do not register arbitrary `/create-pr` or `/preflight-review` commands. Desktop picker
availability depends on the installed host. See the
[official skill documentation](https://learn.chatgpt.com/docs/build-skills).

## Discovery and source of truth

The versioned source is `.agents/skills/<name>/SKILL.md`; `agents/openai.yaml`
provides picker labels and example prompts. Open a Codex task at this repository
or a subdirectory so repository skill discovery applies. A task launched in a
parent workspace does not automatically scan nested repositories: explicitly
point it to this repository's SKILL.md, or reopen the task in the repository.
No global installation is required. Restart/reopen the task if a newly added
skill does not appear in the selector.

AGENTS.md routes agents to the skills. [Delivery policy](delivery.md),
[review evidence](codex-review.md), the PR template and the existing naming and
ownership skills remain authoritative for their respective rules. Read them on
resume rather than relying on conversation memory.

For multi-step delivery, use the [checkpoint and handoff checker guidance](delivery.md#evidence-backed-checkpoints).
It validates evidence fields, not external truth or permission to merge.

## Completion boundaries

A created PR is In review, not Done. Self-review and resolved comments are not
external approval. Merge requires current-head external review and applicable CI
under the existing policy; owner-approved deferrals must be explicitly recorded.
The exact-head review instructions above have one exception: the owner-authorized
[pure-main-sync carry-forward procedure](codex-review.md#review-carry-forward-for-a-pure-main-sync).
Apply every evidence and CI condition before omitting a repeat review; all other
changes require current-head review. This does not waive branch protection.

Docs and board updates report what was verified and what remains outstanding.

`deliver-ticket` coordinates these skills; [delivery-mode.md](delivery-mode.md)
stores the owner-selected execution mode. It does not install a scheduler.
For tasks outside this repository, explicitly invoke the repository skill path.
A personal skill link may point to this directory, but is machine-local, not
installed by merging a PR, and must not duplicate the mode or policy.
