# Framework guidance for coding agents

Repository instructions are stored in Git so agents can discover them in any
checkout. AGENTS.md defines working rules, scoped AGENTS.md files route framework
work, and .agents/skills contains repeatable workflows. The Wiki explains these
rules and should link here instead of duplicating them.

## Next.js

Follow the [official AI coding agent guide](https://nextjs.org/docs/app/guides/ai-agents).
After installing the locked frontend dependencies, read the relevant files under
`frontend/node_modules/next/dist/docs/`. They match the installed Next.js version.
Use local documentation before assuming an API from memory or newer online docs.
If missing, restore locked dependencies first; otherwise consult official docs
for the installed version and state any remaining version uncertainty.

For runtime changes, inspect compilation errors, browser console and network
failures and the actual rendered page. Use the existing development server when
appropriate; check its port/process before starting another. The Next.js dev
server exposes framework diagnostics through `/_next/mcp` when supported; browser
verification complements these diagnostics. Use available runtime tools rather
than requiring a particular editor or silently installing global integrations.
Follow documented error remedies and retain production CI and browser regression
checks. Do not enable caching or other architectural features merely because a
generic guide demonstrates them.

## FastAPI

Use the [official FastAPI skill](https://github.com/fastapi/fastapi/blob/master/fastapi/.agents/skills/fastapi/SKILL.md).
Prefer the copy shipped with the locked installed package over the moving master
branch. From the repository root, locate it without hard-coding a Python version
or a developer's home directory:

```sh
backend/.venv/bin/python -c 'import pathlib, fastapi; print(pathlib.Path(fastapi.__file__).parent / ".agents/skills/fastapi/SKILL.md")'
```

Read that file and resolve its reference links relative to its containing folder.
The existing ecommerce-backend skill routes agents to it; no machine-specific
symlink, copied upstream skill or global installation is required. In another
virtual environment, substitute that environment's Python interpreter.
If the package does not include the skill, use the official documentation matched
to the installed release; do not upgrade dependencies solely to obtain a skill.

Use compatible dependency injection, Pydantic validation, response filtering and
sync/async patterns. Our SQLAlchemy 2 persistence, Decimal money, authorization,
transaction boundaries and migration rules remain in force. An upstream preference
for SQLModel or another tool is not approval to replace working architecture.

## Maintenance and delivery

When upgrading a framework, inspect changes to its bundled guidance along with
release notes and rerun relevant checks. Keep upstream reference content upstream;
commit our routing instructions, project decisions and workflow rules here.

Make small coherent commits with clear Conventional Commit messages. Keep each
behavior and its necessary tests together; generated files may make a legitimate
commit larger. After relevant checks and staged-diff review, push verified
milestones regularly within the user's existing authorization. Do not force-push
or weaken CI to meet this cadence. Re-request current-head review after changes.
