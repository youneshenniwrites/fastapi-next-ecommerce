# Lessons from repository reviews

These are review questions derived from historical findings, not claims that the
current implementation still has those defects. Follow current project policy
when a historical remedy conflicts with a later architectural decision.

## Documentation and contracts — PRs 35, 41, 47, 49, 59, 79, 88

Search the repository for the superseded claim when changing architecture, hosting,
assets or delivered features. Include scoped skills, README, API guide, roadmap,
CI summaries, the canonical skill invocation guide, example configuration and anchors. A new correct paragraph does not
remove an old contradictory instruction. Verify local launch URLs against exact
origin checks. Preserve self-review disclosure and distinguish informational
review status from enforced approval.

## Review automation trust — PR 37

Check who can create authoritative requests, exact request syntax and verified
bot identity. Trace submitted, edited and dismissed findings after a clean signal;
resolving or dismissing a finding does not create new approval. Check failed or
late refreshes, reopened PRs and multiple PRs sharing a SHA. A commit status is not
inherently PR-bound. Respect the explicit deferred enforcement work in #38; do not
claim the historical inherited-status finding has been eliminated.

## UI lifecycle and accessibility — PRs 56, 66, 78

Inspect portaled overlays when crossing breakpoints; hiding a trigger’s wrapper
does not dismiss a modal or its focus trap. Inspect computed focus styles from
both shared CSS and primitives. Test a page initially opened hidden as well as
one hidden after mount; do not assume a visibility event always precedes setup.

## Cart/session state — PR 80

- Recovery: exercise empty and populated states, initial failure, later failure,
  catalog controls and cart page. Every stale consumer needs a visible explanation
  and a working retry. Include lost RSC transport responses that publish no snapshot;
  transition completion alone must not reveal concealed data. Trace the provider used by each warning; a healthy outer
  provider cannot report a failed inner provider. Retry must revalidate the failed
  dependency, including identity, and restore usable controls.
- Identity: test guest→A, A→guest/expired and A→B, with focus, without a hide event,
  and through the existing session observer. Invalidate private snapshots before
  displaying a new identity. Compare every arriving snapshot with the observed
  session, including late ready results, not only initial loading results. Test both
  response orders: a snapshot must remain concealed while session resolution is
  pending or failed, not only when a resolved identity already mismatches. Server mutations must independently verify ownership.
- Operation lifetime: account changes must invalidate pending guards, errors and
  success timers. Late A completion must not overwrite B feedback or clear B’s
  in-flight operation. Check both admission and completion, including A→guest→A.
- Relative writes: distinguish typed absolute quantity from Add/+/- intentions.
  Verify behavior against a newer server quantity and the quantity limit, including
  rejection paths that still require refreshed data. Do not describe a read then
  write as atomic across clients.
- Uncertain outcomes: a timeout may follow a committed write. Do not automatically
  retry a relative mutation. Reconcile against an authoritative read; clear
  uncertainty only with a new successful snapshot after the failure (an old ready
  value is not confirmation), and keep recovery
  available when that read fails. Check ordering of action result and refreshed UI.
- Interaction: focus may occur between pointer-down and click. Concealing private
  state must not accidentally replace the activation target. Test privacy and
  first-click behavior together rather than replacing one regression with another.
  Concealed interactive descendants must leave the tab order (opacity and
  aria-hidden alone are insufficient); preserve an in-progress pointer click
  before applying inert. Reset abandoned pointer activations on window blur and
  page exit so a missing pointerup cannot permanently defeat concealment.
- Rendering: slow private reads must not block unrelated route content. Suspending
  a second copy of interactive children can remount forms and discard input/focus.
  Test typing during slow reads and no-JavaScript rendering where promised.
  Distinguish server-rendered markup from visible streamed content: Suspense
  replacement needs JavaScript, even when its HTML includes authoritative data.

Prefer the installed Next.js documentation and framework-managed reads/actions to
another client cache or polling mechanism. These lessons constrain behavior, not a
requirement to preserve the old cart implementation.

Follow-up examples: [late ready identity](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/80#discussion_r3997171787),
[new read evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/80#discussion_r3997171789),
[concealed refresh recovery](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/80#discussion_r3997191653).

[Snapshot preceding session resolution](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/80#discussion_r3997240114).

[Concealed focus targets](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/80#discussion_r3997271714).
