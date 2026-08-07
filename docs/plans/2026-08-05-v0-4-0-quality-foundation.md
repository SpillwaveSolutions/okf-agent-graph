---
date: 2026-08-05
slug: v0-4-0-quality-foundation
title: v0.4.0 Quality Foundation
epic: 01KZ9N0WTCXZ9SVGDJBPA0TZ3K
items: [01KZ9N0WV1VQNG0XQE3ZSNNM1B, 01KZ9N0WV1NMBQKSQH2PR9WZAQ, 01KZ9N0WV1PP6RX6B0X47N9KXT, 01KZ9N0WV145FC2EE07CVSEW42, 01KZ9N0WV254KNHPZKZ8KFETSG]
git_hash: "89ddccb5b9e318fff0fc699c44c7491d92c85616"
---

# v0.4.0 Quality Foundation

Deliver one release PR that makes AGER scaffolding reproducible, adds deterministic validation and CI, enables native Codex installation, and initializes WikiTicket SDD. Keep the document schema at `ager_version: "0.3.0"` because no breaking schema change is planned.

## Tasks

- [ ] (P0) Initialize WikiTicket SDD and capture the v0.4.0 release plan
- [ ] (P0) Build a complete deterministic AGER scaffold generator
- [ ] (P0) Add standard-library AGER domain validation
- [ ] (P0) Add tests, CI, and strict sample validation
- [ ] (P1) Add native Codex packaging and v0.4.0 documentation

## Acceptance criteria

- A generated scaffold passes AGER validation and OKF strict validation with zero warnings.
- Negative validator fixtures cover missing references, missing controls, unsafe irreversible tools, inline secrets, and incompatible versions.
- Plugin manifests stay version-locked at 0.4.0 while `ager_version` remains 0.3.0.
- All repository and plugin validation checks pass in GitHub Actions.
