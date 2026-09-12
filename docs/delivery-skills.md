# Delivery skills

These repository skills package our existing delivery workflow. They use GitHub
Issues, the four-column project board and the canonical PR template. They do not
create a background service or replace external Codex review.

| Invoke | Outcome |
| --- | --- |
| `$refine-tickets` | Scoped linked stories, dependencies and a resumable issue handoff before coding. |
| `$create-pr` | Issue-linked PR with factual description, ownership, labels and review request. |
| `$self-review PR #42` | Full diff review, findings and verification; review-only requests do not edit code. |
| `$address-codex-comments PR #42` | Verified fixes, evidence replies, resolved addressed threads and fresh review when needed. |
| `$update-delivery-board` | Board reconciled with actual delivery and acceptance evidence. |
| `$update-docs for PR #42` | Relevant README, Wiki or API documentation updated and verified. |

Replace #42 with the actual PR. Natural-language requests can also select the
skills. Codex CLI/IDE provides `/skills` selection and `$skill-name` mentions;
these files do not register arbitrary `/create-pr` commands. Desktop picker
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

## Completion boundaries

A created PR is In review, not Done. Self-review and resolved comments are not
external approval. Merge requires current-head external review and applicable CI
under the existing policy; owner-approved deferrals must be explicitly recorded.
Docs and board updates report what was verified and what remains outstanding.

The proposed `finish-pr` orchestration skill is not included in this first set.
It can follow once these individual workflows have been exercised.
