# Delivery execution mode

**Current mode: Lean**

Owner-selected on 22 September 2026. One agent, batched work and no scheduled
wakeups. Complete authorized tickets without requiring repeated continuation
prompts; normal acceptance, review and merge rules still apply.

The owner may say **enable parallel mode** or **enable lean mode**. Update this
file through the normal PR workflow after an explicit switch. Never infer a
switch from quota resets. Parallel mode permits bounded implementer/verifier
delegation as defined in [deliver-ticket](../.agents/skills/deliver-ticket/SKILL.md);
it does not authorize additional product scope, spending, merges or deployments.

Fresh repository tasks read this setting through AGENTS.md. Until a change merges,
other checkouts may retain the previous setting; report that distinction.
