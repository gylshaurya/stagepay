# Stagepay

Draft for the existing Devpost entry. Not approved for final submission. Deployment and video links are still pending.

## Tagline

Agree on freelance milestones, review the work, and release test payments with a clear record of each decision.

## Inspiration

Small freelance jobs often use one chat for the scope, another place for the files, and a separate payment record. When the work changes, it can be hard to tell which version both people agreed to. Stagepay puts the agreement, delivery and payment decision together.

## What it does

A client creates up to three milestones and sets aside test tokens. The freelancer agrees to the scope, then submits a link and a short note for each delivery. The client can accept the work or ask for a revision. Acceptance makes that milestone's payment available once. A revision does not pay.

Both people can agree to change the unpaid scope. Work that was already accepted stays paid, while unpaid milestones need new evidence. If there is a dispute, both people must agree on a split of the remaining tokens before the agreement closes. There is no hidden administrator who can choose the winner.

## How it was built

The browser interface uses JavaScript, CSS and locally served Source Sans 3 fonts. A Python service stores the readable records in SQLite. Solidity contracts handle escrow, acceptance and withdrawals. OpenZeppelin provides the token implementation, safe transfers and reentrancy guard. Foundry runs the contract checks and the local Anvil chain.

Each acceptance checks the agreed scope and submitted evidence hashes. The service saves real local transaction receipts beside the work. The current version uses clearly labelled demo roles and test tokens. It is not a production payment service.

## Challenges

Changing the scope after some work is paid creates a difficult boundary. Stagepay keeps accepted milestones intact and clears only unpaid evidence when both people agree to a new scope. Another risk is an interrupted transaction: the service journals the attempt and pauses later writes when its result is uncertain.

## What works today

The local workflow covers funding, agreement, delivery, revisions, acceptance, scope changes, mutual settlement, withdrawal and receipt export. The repository includes contract and service checks. A browser walkthrough has produced confirmed local receipts for funding, agreement, delivery, acceptance and withdrawal, and the records survived a service restart.

## What is next

Add public testnet wallet signing, finish receipt recovery and verify a free deployment. Public deployment and the final demo video are not ready yet. Disputed tokens can remain locked if the people never agree, so this prototype should only use its test asset.

## Links and built with

- Source: https://github.com/gylshaurya/stagepay
- Local setup: docs/SETUP.md
- Public application: pending verified deployment
- Demo video: pending recording and playback review
- Built with: Solidity, OpenZeppelin Contracts, Foundry, Anvil, Python, SQLite, JavaScript, CSS, Source Sans 3.

The event rules checked on 6 September do not name a required sponsor product. Stagepay uses smart-contract escrow as its blockchain component. Do not describe EAS, thirdweb or another sponsor SDK as integrated when the current code does not use it. Recheck the final rules and any organizer reply before preparing the exact submission package.
