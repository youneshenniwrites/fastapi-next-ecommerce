# Decision 0001: explicit GBP decimal prices

Status: accepted. Implemented in PR #4.

The owner selected GBP as the launch currency. Product prices previously used
floating-point storage, which was unsuitable as the source of truth for money.

Use Python Decimal and PostgreSQL NUMERIC(12, 2). The API serializes price as a
two-place decimal string and returns currency GBP. GBP is the only accepted
currency; this does not implement foreign exchange or multi-currency checkout.

Requests reject values outside 0.00–9999999999.99 or with more than two decimal
places. Database constraints enforce nonnegative bounded prices, stock, currency,
and catalog field limits. Checkout arithmetic must continue using Decimal
and order items must snapshot the price used at purchase time.

Migration 0002 checks legacy values before conversion, labels them GBP, and refuses
values requiring rounding/correction. PostgreSQL locks the product table during
preflight and conversion. A backup and an application-compatible rollback plan are
required for production rollout. This is the migration decision at introduction;
current deployment acceptance belongs to the canonical plan. The API price type
changed from a JSON number to a string, so frontend contracts must reflect it.
The storefront now consumes
generated API types and represents GBP amounts in integer pennies.

If another currency is introduced, revisit its minor-unit precision, validation,
order/payment schema, and migration strategy in a new decision and PR.
