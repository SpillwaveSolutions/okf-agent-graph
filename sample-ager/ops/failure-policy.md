---
type: FailurePolicy
title: Default failure policy
description: Classify errors and route to retry, DLQ, human, or exhaust.
ager_version: "0.3.0"
routes:
  transient:
    action: retry
    retry_policy: /ops/retry-policy.md
  permanent:
    action: dead_letter
  policy:
    action: fail
  budget:
    action: exhaust
  human:
    action: escalate_human
  unknown:
    action: retry
    retry_policy: /ops/retry-policy.md
status: active
timestamp: 2026-08-04T00:00:00Z
---

# Failure policy
