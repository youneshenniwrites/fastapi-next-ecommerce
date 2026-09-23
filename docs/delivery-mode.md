# Delivery execution mode

**Current mode: Parallel**

Owner-selected on 23 September 2026. Use bounded implementation and independent
verification agents within one active feature, with isolated writing worktrees and
test resources. No scheduled wakeups. Complete authorized tickets without requiring repeated continuation
prompts; normal acceptance, review and merge rules still apply. Answer intermediate
questions briefly, then continue the active delivery. A question or status request
is not a pause; stop only on an explicit pause or a concrete blocker.

The owner may say **enable parallel mode** or **enable lean mode**. Update this
file through the normal PR workflow after an explicit switch. Never infer a
switch from quota resets. Parallel mode permits bounded implementer/verifier
delegation as defined in [deliver-ticket](../.agents/skills/deliver-ticket/SKILL.md);
it does not authorize additional product scope, spending, merges or deployments.

Fresh repository tasks read this setting through AGENTS.md. Until a change merges,
other checkouts may retain the previous setting; report that distinction.
