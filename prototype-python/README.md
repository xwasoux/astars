# Python Prototype (Frozen Reference)

This directory holds the original pure-Python implementation of Astars (`v0.1.0` line).
It is kept as a **frozen reference** for the Rust core migration — see
[`docs/STRATEGY.ja.md`](../docs/STRATEGY.ja.md) and [`docs/ACTION_ITEMS.ja.md`](../docs/ACTION_ITEMS.ja.md).

It is not under active development. New work happens in `crates/astars-core` and `bindings/`
at the repository root. Design decisions already validated here (source mapping behavior,
edge cases, tie-breaker policy) carry over into the Rust design; see
[`docs/SOURCE_MAPPING_PLAN.ja.md`](../docs/SOURCE_MAPPING_PLAN.ja.md) for the resolved decisions.
