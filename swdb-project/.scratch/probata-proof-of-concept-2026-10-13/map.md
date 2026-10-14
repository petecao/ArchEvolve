# Map: Extensa Probata proof of concept

Created: 2026-10-14 00:45 ET
Spec: [spec.md](spec.md). Tickets: [issues/](issues/). Integration branch: `probata-poc/integration`.

## Context pointers

One line per resolved ticket: number, one-line result, commit.

- 02 — campaign entry links every certification record as `certification.records` (`{contract, record[, refusal]}` per contract, in order); fixture adapter writes one per contract; `campaign.certification_links` reads old entries; 4c77c651 (`probata-poc/t02`).
