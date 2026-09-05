# Stagepay
<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
Delegated by the user for each project. Python standard-library HTTP service and SQLite for a durable local workspace, browser JavaScript/CSS, and the existing Solidity contracts on a dedicated local Anvil chain. This avoids new hosting or API costs. Public testnet deployment and wallet signing are a later verified milestone.

## Users
Student freelancers doing short projects and their clients. They agree on scope, submit evidence, request revisions, accept milestones and keep payment receipts together. This is the exact idea selected by the user.

## Product Purpose
Keep agreed work, review decisions and a test-token payment record in one place. Demonstrate partial milestones, mutual scope changes and a complete mutual-settlement path.

## Operating Context
The user delegated routine product and design decisions and asked not to repeat questions. A local judge demonstration switches between two explicitly labelled demo actors. That switch is not production authentication. Data persists in SQLite; on-chain actions must run against the actual contract and produce actual transaction receipts.

## Capabilities and Constraints
One to three funded milestones. Freelancer agrees before work starts. Exact evidence/scope acceptance credits a payment once. Revisions do not pay. Scope changes and post-join cancellation require both parties. Disputes freeze unpaid work until mutual settlement; indefinite lock is an explicit limitation. Test tokens have no cash value. No real funds, customer claims, deployment claims or invented proof.

## Brand Commitments
Simple name, plain explanatory English, no em dashes, professional product-specific UI, no generic AI decoration. Captions-only demo. User explicitly delegated stack and design per project.

## Evidence on Hand
Existing Stagepay and DemoToken contracts, 17 passing contract tests, public GitHub source. No production deployment or independent security audit.

## Product Principles
Make the next action clear. Keep the accepted agreement and evidence visible. Separate local receipts from public testnet evidence. Stop only work that depends on a missing fact or account step.
