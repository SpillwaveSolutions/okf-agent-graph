---
type: RetryPolicy
title: Transient retry
ager_version: "0.3.0"
max_attempts: 4
backoff: exp
base_ms: 500
max_ms: 15000
jitter: true
retry_on: [transient, HTTP_429, HTTP_503]
status: active
timestamp: {{TIMESTAMP}}
---

# Retry policy
