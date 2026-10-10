# 0007: A free public tool with no accounts or payments

Status: Accepted, October 2026

## Context
The SaaS playbook I follow covers authentication, payments and multi-tenancy. Tick & Tie answers questions about public filings, and nothing in it is per-user.

## Decision
No sign-up, no payments, no tenancy. Everyone uses the same read-only corpus.

## Alternatives considered
- User accounts with saved questions: adds authentication, privacy obligations and a store of personal data for little benefit.

## Consequences
- Authentication and payments are out of scope.
- Abuse protection relies on rate limiting (Task 7).
- The privacy policy can be short: no accounts and no personal data stored.
- Revisit only if the product changes.