# Contributing

Start with the [README](README.md) and [roadmap](docs/plans/roadmap.md). The working
product is the backend; the catalog frontend is runnable. Keep proposed features scoped
to the next usable behavior and separate tooling/documentation changes when useful.

## Local workflow

1. Create a task branch from current main. Inspect open PRs for overlapping changes.
2. Run `make setup`; use `make dev` when a live backend is needed.
3. Reproduce bugs before fixing them and add a behavior-level regression test.
4. Run `make check`. Use `make coverage`, `make audit`, and
   `make requirements-check` for relevant dependency or tooling changes.
5. Commit incrementally as each coherent change is completed and verified:
   stage only relevant files, keep coupled code, tests and generated files
   together, and review the staged diff before committing with a focused
   Conventional Commits subject (see Naming conventions below). Small tasks
   may need only one commit. Incremental commits do not replace full PR
   testing or current-head external review, and committing never authorizes
   pushing or merging.
6. Review the complete diff and open a focused PR with validation evidence.

`make hooks` installs optional local checks. CI still runs even when hooks are not
installed. Use separate Compose project names, ports, and databases for concurrent
worktrees. Never point test database overrides at customer data.

## Change contracts

- **Database:** add a new Alembic revision; do not edit an applied revision. Test
  empty-database upgrade, metadata consistency, and any affected existing data.
- **API:** document request/response changes, permissions, and error behavior.
  Product price is a decimal string in GBP; avoid introducing float arithmetic.
- **Dependencies:** edit pyproject.toml, regenerate uv.lock, and export requirements.txt.
  Run the audit and requirements check. Review upstream release notes for compatibility.
- **Frontend:** follow frontend/AGENTS.md. Run lint, formatting, type, unit, build
  and browser checks. Regenerate API types when the backend contract changes.
- **Docs/skills:** describe implemented behavior accurately. Validate links and skill
  frontmatter. Do not turn future plans into claims of production readiness.

See [tooling](docs/tooling.md) for exact checks and [development](docs/development.md)
for database and configuration details. Coding agents should also read [AGENTS.md](AGENTS.md).

## Naming conventions

Follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
for commit and squash subjects: `type(scope): description`. Scope is optional.
Use `feat` for features, `fix` for bugs; our other types are `docs`, `ci`, `build`,
`test`, `refactor`, `perf`, `style`, `chore`, and `revert`. Use lowercase types and
concise descriptions of the resulting change. Mark breaking changes with `!`
before the colon or a `BREAKING CHANGE:` footer, and explain migration effects.

The specification does not define branch names. Our local adaptation is
`type/vin-N-short-description`, with the actual GitHub issue number in lowercase
(`vin-118`, not the PR number). Keep the branch stable; track progress on the board.

| Branch | Commit subject |
| --- | --- |
| `feat/vin-118-order-drafts` | `feat(orders): add draft snapshots` |
| `fix/vin-89-cart-recovery` | `fix(cart): recover timed-out reads` |
| `docs/vin-178-branch-naming` | `docs: define repository naming conventions` |
| `ci/vin-178-branch-naming` | `ci: enforce issue-linked branches` |

New human PRs must match their branch issue key to the `[VIN-N]` title key.
A trusted main-branch workflow validates the format and confirms N is an
existing issue, not a PR. It publishes a head-bound `Branch naming` status for
all PRs including docs-only changes; title edits retrigger this lightweight check.
After this policy merges, validate a real status before adding it to required
checks, preserving all existing protections. Until then enforcement is pending.
Only existing PR #177 (`feat/order-drafts`) is grandfathered. Verified Dependabot
authorship is exempt; naming a human branch `dependabot/…` is not an exemption.

Do not create `agent/` branches. Existing Dependabot-managed branches keep their
bot names and upstream PR titles under the VIN-172 exception; use Conventional
Commits squash subjects when merging them.
PR titles use `[VIN-N] [type] Description`, where N is the linked GitHub issue
number, not the PR number. Use one lowercase type: `feat`, `fix`, `docs`,
`test`, `ci`, `chore`, `refactor`, or `perf`. Choose the primary purpose of the
final diff; describe any secondary changes in the body. No scope parentheses
or extra colon are required. Examples:

- `[VIN-158] [fix] Preserve anonymous visitor rate limits`
- `[VIN-118] [feat] Persist order snapshots`
- `[VIN-172] [docs] Correct export instructions and record dependency progress`

Open the body with `**Issue:** [VIN-N — Issue title](issue-url)`, followed by
`Closes #N` (complete) or `Refs #N` (partial), then a separate `**Problem:**`
line stating what is broken or missing. Do not repeat an Issue section below. Use the same alias in issue titles and handoffs; no separate
numbering system or duplicate issue is created. Refer to pull requests as `PR #N`.
For squash merges, explicitly supply a Conventional Commits subject, for example
`fix(security): isolate customer write limits (VIN-158)`; do not copy the PR title. Preserve breaking-change
information in the squash message. This policy applies to future work; do not
rewrite merged history. The ecommerce-naming skill guides agents through these
checks. This is a documented review policy, enforced for branches by the trusted naming status after rollout.

## Fetching and pushing

Keep the default full fetch refspec (`+refs/heads/*:refs/remotes/origin/*`).
Single-branch clones leave branch tracking refs missing or stale, which makes
`--force-with-lease` fail with a misleading "stale info" rejection that looks
like a server-side force-push block. First-push a new branch with
`git push -u origin <branch>` so its upstream tracks the branch itself, never
main. When rewriting an agent-owned branch, push with the branch-scoped form
`git push --force-with-lease origin <branch>` after confirming `<branch>` is
agent-owned and is not `main`; never force-push `main` or another author's
branch. If a push is rejected with "stale info", restore the full refspec and
re-fetch before retrying (`git config remote.origin.fetch
'+refs/heads/*:refs/remotes/origin/*'` then `git fetch origin --prune`), and
inspect `git branch -vv` upstream wiring before assuming the server blocks the
push.

## PR ownership

Repository ownership is recorded in .github/CODEOWNERS. Assign maintenance PRs to
@youneshenniwrites and apply relevant scope labels. Agents use the
ecommerce-pr-ownership skill and its checked helper after PR creation. Authorship
is the actual GitHub account that opens the PR; do not forge a different author.

## Review and merge

Use the PR template headings and reference the GitHub issue. Use Closes #N
for completed tickets and Refs #N for partial work. Never invent a ticket reference.

Explain the problem and resulting behavior, then give the commands/results and
material limitations. Keep the Review section to a brief self-review disclosure
and links to current-head Codex review and CI evidence, stating their actual
status. Assignment and labels belong in the sidebar. Include relevant screenshots for UI changes, or API/test
output for backend changes. Do not include tokens, passwords, or customer data.

Review the exact pushed revision. Address actionable findings and rerun affected
checks. A self-review must say it is a self-review; it is not independent approval.
All applicable CI jobs must pass before merge. Follow the
[Codex review policy](docs/codex-review.md); the status is informational pending #38. A verified clean external review replaces a human approval; ticket
acceptance must still be checked. Eligible dependency updates follow the explicit
[automated dependency policy](docs/dependabot.md); all other updates retain normal review.

Merge permission does not authorize cloud provisioning. Cloud deployments need
an agreed environment, budget, secrets/identity design, and rollback plan.
Report vulnerabilities privately through [SECURITY.md](SECURITY.md).

## Delivery tracking

Follow [delivery workflow](docs/delivery.md) for issue scope, board transitions,
PR linkage and completion evidence. The project board is the live work queue.

## Agent framework references and checkpoints

Use [framework guidance](docs/framework-agent-guidance.md) for installed-version
Next.js documentation and the official FastAPI skill. Follow AGENTS.md for small
coherent commits and regular verified pushes within the authorized task. Review
these references when upgrading dependencies; preserve local architectural rules.

The exact-head review instructions above have one exception: the owner-authorized
[pure-main-sync carry-forward procedure](docs/codex-review.md#review-carry-forward-for-a-pure-main-sync).
Apply every evidence and CI condition before omitting a repeat review; all other
changes require current-head review. Branch protection remains enforced.

## Automated dependency exception

The owner-authorized [Dependabot policy](docs/dependabot.md) allows eligible dependency-only
npm/uv patch and minor PRs to receive automated policy approval and protected
auto-merge without per-PR Codex review. Other PRs retain the normal review rules.
Bot PRs retain upstream titles; VIN-172 tracks the policy.
