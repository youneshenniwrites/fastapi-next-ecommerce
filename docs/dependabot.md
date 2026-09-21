# Dependabot maintenance (VIN-172)

Owner-authorized on 21 September 2026: eligible npm/uv patch and minor updates
receive an automated policy approval and GitHub auto-merge after required CI and
branch protection. This is an explicit exception to per-PR Codex/CodeRabbit review,
not a claim of external review. The automation implementation itself still needs
normal external review before merge. No paid agent or scheduled agent runs.

Only same-repository, non-draft Dependabot PRs targeting main qualify. Metadata
verification stays enabled; all commits must be verified Dependabot commits and
all changed files must be the ecosystem's dependency manifests/lockfiles/export.
Major upgrades, GitHub Actions/workflow changes, Docker updates, unknown metadata,
human-modified branches and application changes retain ordinary review. Bot PRs
keep their upstream titles and authorship; VIN-172 is their standing policy ticket.

The privileged workflow checks out trusted base code only. It never installs or
executes PR dependencies/code. Required tests, audits, current-base protection and
conversation resolution remain enabled; no administrator bypass. A visible policy
approval is not a green CI claim. Failed CI prevents merging. Each new head clears
and re-evaluates auto-merge eligibility. Dependabot rebases its unchanged branches;
conflicts or human changes require attention rather than a force push.

Repository prerequisites: enable Allow auto-merge and Allow GitHub Actions to
create and approve pull requests. Keep default workflow permissions read-only;
only the scoped workflow receives contents/pull-requests write. First live success
must be recorded on VIN-172 before claiming operational automation.

Python updates can leave `backend/requirements.txt` stale. The consistency check
must continue failing until a maintainer exports it from the updated lockfile with
`uv export --locked --no-dev --no-emit-project --format requirements-txt --output-file requirements.txt`.
That human-modified branch requires ordinary review. Automatic export repair is
not implemented by this initial safe policy; these PRs remain visibly blocked.

Keep bot PRs out of the engineering delivery board; use GitHub's dependency PR
list (`is:pr is:open author:app/dependabot`) for maintenance. If configuring project
auto-add, exclude `label:dependencies` (or restrict auto-add to issues). The inspected
board had no cards for PRs #165–#171; they are in the repository PR list, which must
retain open updates until merged or deliberately declined. Do not close updates
just to hide them.

Reference: [GitHub Dependabot automation](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/automate-dependabot-with-actions).
