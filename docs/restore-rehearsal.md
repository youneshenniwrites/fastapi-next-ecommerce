# Disposable demo restore rehearsal

[VIN-258](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/258)
proves the bounded database recovery outcome in the [portfolio plan](plans/portfolio-completion.md).
This is a local PostgreSQL rehearsal, not a hosted Neon restore or a production
backup service. Enterprise recovery objectives and point-in-time recovery remain
in [VIN-130](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/130).

## Run

Prerequisites: Docker running, PostgreSQL 17 image available, Python 3.12 and uv.
From a clean checkout of the reviewed revision:

```sh
make setup
docker pull postgres:17
make restore-rehearsal
```

The command accepts no database URL, archive or target overrides. It creates two
randomly named containers, fresh private credentials, loopback-only ephemeral
ports and memory-backed database storage. It never uses the Compose stack or its
volume. The application worker replaces `.env` settings before importing the
database/application: Sentry, Stripe and diagnostics are disabled, and the
authentication key is newly generated. No cloud resource or paid service is needed.

The source receives actual Alembic migrations and the existing fictional catalog,
two customer registrations, distinct carts, a placed order and a draft. PostgreSQL
17's `pg_dump -Fc` captures schema, rows and sequences into an in-memory archive.
An intentionally truncated archive must fail and leave the target empty. The full
archive is then restored into the separate empty target using `pg_restore
--single-transaction --exit-on-error --no-owner --no-privileges`; no overwrite or
`--clean` option is used. These are [PostgreSQL's dump](https://www.postgresql.org/docs/17/app-pgdump.html)
and [restore](https://www.postgresql.org/docs/17/app-pgrestore.html) tools.

Before any restored login or write, all table row digests and sequence values must
match the source. `alembic check` and migration-head agreement verify schema.
Local FastAPI TestClient requests then verify catalog values, valid/invalid
passwords, profiles, carts, order totals/status/history and cross-account 404s.
New customer/order writes exercise restored ID sequences. This exercises the API
and PostgreSQL together; it does not claim browser, network, Stripe or hosted recovery.

## Evidence and cleanup

Only after successful verification and cleanup does stdout receive a JSON report:
Git revision/dirty status, PostgreSQL version, distinct container names, UTC
start/end/checkpoint timestamps, archive size/SHA-256, row counts/digests,
observed restore duration, backup age at restore start and API results. Retain
that sanitized report with the source ticket. Acceptance runs must identify a
committed clean revision; a dirty exploratory run is not the final record.

The archive exists only in process memory; the private checkpoint directory is
temporary. Both labelled containers and their fictional accounts/data are removed
on success or failure. Cleanup refuses foreign ownership labels, attempts every
owned container and fails completion if deletion cannot be verified. Child logs
are withheld because they may contain private configuration. A daemon outage or
hard process kill can prevent cleanup: identify only this report/run's exact
`vin258.owner` label, inspect its containers, and remove those owned containers
with `docker rm -f -v`; never use a global prune or delete the development volume.

The report's `restore_seconds` measures only the restore command, not setup,
verification or incident response. Backup age measures elapsed time since this
archive finished; it is not an RPO guarantee. This tiny fictional dataset, local
hardware and one successful run cannot establish a service RTO, durable backup
retention, production-scale recovery, global roles or point-in-time recovery.

## Current free-host limits

Checked 3 October 2026 against [Neon's official Free plan documentation](https://github.com/neondatabase/website/blob/main/content/faqs/free-plan-limits-and-quotas.md),
updated 1 October: 10 branches per project, 100 CU-hours per project/month, 1 GB
PostgreSQL storage per project (20 GB total), 5 GB public transfer per project/month,
one manual snapshot and six hours of instant-restore history capped at 1 GB of
changes. Limits can change; recheck the provider before a hosted drill. This
rehearsal provisions no Neon branch, copies no hosted database and tests no provider
history window. No paid upgrade, recurring backup or continuous monitoring is implied.
