# Reviewed development frontend previews — VIN-45

## Boundary and budget

One manually requested protected preview is the first delivery target, not an
automatic PR platform. Use the existing development frontend on Vercel Hobby;
no new account, purchased domain, paid plan, database clone or schedule.
Direct Git deployments remain disabled. The stable development/production aliases
are not promoted or replaced by this workflow.

The preview shares **fictional development** accounts, catalog and carts through
`https://forme-api-development.vercel.app`. This is intentionally shared data:
the same account sees its same cart on stable development and a preview. Host-only
`__Host-session` cookies keep browser sessions separate; different accounts retain
backend ownership checks. No production API/database/JWT key, database password,
limiter signing key, Sentry upload token or deployment write token is supplied to
preview code. Authentication uses the existing ordinary ingress limit when no
limiter signing key is configured; this is not a new visitor-isolation guarantee.
Before upload, health and deliberate invalid-login probes require the actual
FastAPI responses without a bypass. Protection responses stop creation; if API
access later changes, investigate instead of copying secrets. No hosting protection
is weakened by this feature.

## Trust and credentials

`Reviewed frontend preview` is manual and runs only on `main`. Its GitHub
`development` environment retains the existing main-only restriction. Trusted-main
Python code validates an open non-draft same-repository PR and the operator's full
expected SHA, using complete current-head selected review evidence and the latest
matching successful PR runs for Backend CI, Frontend CI, Dependency audit and
Review gate tests. Unresolved findings, forks, stale review, missing/pending/failed
CI and a changed head fail closed. The requested head must contain current main,
so PR CI’s synthetic merge has the same tree as the uploaded head; a main advance
during verification stops creation. CodeRabbit is selected only for the existing
routine-documentation exception; other source uses the existing Codex gate.

Validation runs before the step receives the Vercel token and is repeated before
upload. No npm, PR script or local build runs from the source archive on the
credentialed runner. Only the pinned official Vercel CLI uploads source for the
remote build. The CLI's child environment excludes GitHub/database/signing secrets;
its write token is a CLI argument, never a build/runtime variable or uploaded file.
Vendor failure output is not dumped into public Actions logs. Reject executable
Vercel config, links, local provider credentials and non-example environment files.
A trusted fixed JSON CLI configuration selects the existing Next.js build.

Before upload, the API audit requires the exact approved development project/team,
frontend root, provider system variables, deployment protection and an empty
Preview environment scope. Accepted SSO modes are `all`, `preview`,
`prod_deployment_urls_and_all_previews` and `all_except_custom_domains`; the
unsupported abbreviated `prod_deployment_urls` value is rejected. Existing
Production-target variables on this **development project** are not inherited by a Preview deployment. Only explicit
non-secret development configuration is injected for this preview; diagnostics
and webhook relay stay off. Unexpected variables or incomplete metadata stop it.

## Exact origin

`APP_ORIGIN_MODE=vercel-preview` requires `VERCEL=1`, `VERCEL_ENV=preview` and a
canonical single provider `VERCEL_URL` hostname. Its only allowed origin is
`https://<that hostname>`. It ignores stable `APP_ORIGIN` and aliases, never request
Host or forwarded headers. Aliases/other preview hosts do not acquire session-write
permission. Invalid provider context fails closed. Normal local/development and
production origin policy is unchanged.

## Usage and retirement

After this orchestration is reviewed and merged, synchronize the source branch
with current main and obtain its fresh current-head review and CI. A behind or
diverged branch is ineligible. Then request the workflow from `main`:

```sh
gh workflow run preview.yml --ref main \
  -f operation=create -f pr_number=NUMBER -f head_sha=FULL_REVIEWED_SHA
```

Read the Actions summary for the exact preview URL, source SHA and deployment ID.
Use the deployment's unique URL, not a stable alias. Keep Vercel Authentication;
team members sign in normally. Do not invoke protected-request tooling blindly:
`vercel curl` may create persistent project-wide automation bypass access when no
secret exists. This preview proof does not authorize that extra access.

For an HTTP probe that must reach the application behind Vercel Authentication,
use the supported [deployment-specific share grant](https://vercel.com/docs/rest-api/aliases/update-the-protection-bypass-for-a-url)
only within explicit access authorization. Target the recorded managed deployment
ID, set a finite short expiry, preserve unrelated grants, keep its token/cookie
private and revoke only the grant created for the proof immediately afterward.
Verify revocation; if cleanup fails, record it and retire the managed preview.
Wrong-origin logout must return the application's JSON `Origin rejected` response;
a Vercel authentication failure alone does not verify the application policy.

Verify the exact release, HTTPS/security headers, real fictional login/cart,
anonymous sessions on other hosts, distinct-account ownership, wrong-origin writes
and absence of production credentials. An uploaded build does not prove these.
Use a tiny reviewed proof PR after trusted orchestration lands; never dispatch the
bootstrap feature branch with secrets. Leave VIN-45 open until hosted proof exists.

Then retire **only** the recorded managed deployment:

```sh
gh workflow run preview.yml --ref main \
  -f operation=retire -f deployment_id=dpl_EXACT_MANAGED_PREVIEW
```

Retirement checks the exact project, non-production target and VIN-45 metadata.
Never delete by project name or stable URL. Verify the deployment is removed and
stable development/production URLs are unchanged. Record proof/cleanup on VIN-45.
A failed/uncertain creation may leave a deployment: inspect Vercel before retrying
and retire the identified managed preview rather than blindly creating duplicates.
Free quota/provider refusal is an explicit unfinished acceptance blocker.

## Hosted checkpoint — 2 October 2026

[Creation run 37068729348](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37068729348)
created protected deployment `dpl_EMjSUs1KW1avWvYPQuTdcQSGbohn` from reviewed
PR #265 revision `2112afbd9220351d9edead970576a32a30544a90`.
Its unique hostname was
`vindor-ecommerce-development-oim57jtjd-younes-hennis-projects.vercel.app`;
it is retired, not a current demo link. The workflow validated the source and
credential boundary; Vercel reported a ready Preview deployment. Unauthenticated
HTTP navigation redirected to Vercel login, while the authenticated in-app browser
could use the storefront. A login-page HTTP 200 is not application-response proof.

Two fictional development customers registered and signed in. The second account
had an empty cart; signing back into the first account restored its own cart.
The stable development host remained signed out while the preview was signed in.
Both sessions were signed out and the first cart was emptied before retirement.
These observations prove account/host isolation and persistence, not exact
single-click quantity semantics: a quantity change from one to three was observed
without captured request counts. Its cause remains unproven; VIN-260's cart
coverage must investigate rather than claim a regression fix.

[Retirement run 37069674886](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37069674886)
removed that exact managed deployment and verified provider 404. The unique URL
then returned HTTP 404 / `DEPLOYMENT_NOT_FOUND`; the documented stable development
and production aliases still responded normally. No protection grant was created.

VIN-45 remains incomplete: protected application headers/release identity and
actual wrong-origin HTTP rejection still need hosted evidence. The foreign-origin
browser form produced no observable application response, so it is not a pass.
The later creation request in
[run 37069992201](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37069992201)
was rejected before credentials/upload because PR #265 had already merged. Use a
fresh reviewed open PR for the remaining proof; do not weaken the open-source guard
or reuse the retired URL. Record the final result and cleanup on VIN-45 before
claiming its portfolio outcome.

## Sources

Platform behavior follows [CLI deployment](https://vercel.com/docs/cli/deploy),
[system variables](https://vercel.com/docs/environment-variables/system-environment-variables),
[deployment protection](https://vercel.com/docs/deployment-protection),
[protected CLI requests](https://vercel.com/docs/cli/curl),
[retirement](https://vercel.com/docs/cli/remove) and
[Hobby limits](https://vercel.com/docs/plans/hobby). Project policy and the existing
session contract remain authoritative.
