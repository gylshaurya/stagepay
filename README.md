# Stagepay

Stagepay is a milestone desk for student freelancers. The client sets aside test tokens, both people agree on the work, and each payment becomes available when the client accepts the submitted evidence.

The local workspace includes agreement funding, delivery links, revision requests, milestone acceptance, scope changes, mutual settlement and receipt history. It calls real contracts on an isolated Anvil chain and saves project records in SQLite. Public testnet deployment and the final video are still being built.

## Run the workspace

Install Node.js, Python 3.10 or newer, and Foundry. Ensure `forge`, `cast` and `anvil` are on your PATH.

```sh
npm ci --ignore-scripts
npm run chain
npm start
```

Open http://127.0.0.1:4321. Use the Client demo role to fund a project, switch to Freelancer to agree and submit work, then return to Client to review it. The role switch is a local demonstration, not account authentication. The server binds only to loopback. Do not expose it with a tunnel or deploy this local signer service to a public host.

`npm stop` stops only the owned workspace process. `npm run dev` runs it in the foreground instead. The chain uses its own loopback port 18545 and persists under ignored `.local/`. The startup script refuses to take over an unrelated process. No wallet secret or API key is needed: Anvil supplies public, unlocked demo accounts. These accounts must never receive real funds.

The network panel shows the actual contract and demo wallet addresses. Sepolia is explicitly unconfigured. A public version needs a wallet signer and a separate authenticated service before it can be deployed.

## Verify the service

With the local chain running:

```sh
npm run test:service
```

Integration tests deploy separate test contracts so they do not alter workspace agreements. They check real transaction receipts, exact payment amounts, repeat acceptance, revisions, changed scope, disputes, cancellation, stale decisions, request replay and uncertain transaction handling.

Project text and history live in `.local/workspace.sqlite3`. `Export record` downloads the selected project's scope, evidence and confirmed receipt history. Available wallet credit covers all projects for that wallet.

## Interrupted transactions

The service journals the intended transaction, sender nonce and original action before broadcasting. A missing response or receipt pauses later writes, preventing an automatic duplicate payment. Read-only project records remain available. A pending action requires reconciliation against the local node before writes resume; automatic recovery is not implemented yet. Do not delete the database or retry funding to clear it. Preserve `.local/` and inspect the recorded nonce and receipt first.

The local HTTP service checks its Host and Origin headers and accepts only JSON writes. These checks reduce accidental cross-site actions; they do not turn local demo roles into multi-user authentication.

## Run the contract checks

Install Node.js and Foundry, then run:

```sh
npm ci --ignore-scripts
npm run test:contracts
```

Solidity is pinned to 0.8.30. OpenZeppelin Contracts is pinned to 5.6.1. The contracts use its ERC20 implementation, safe token transfers and reentrancy guard.

## What the agreement does

- A client funds one to three milestones with DEMO tokens. The freelancer accepts the exact scope hash before work starts.
- The freelancer submits an evidence hash. The client accepts that exact evidence and scope, or asks for a revision without releasing tokens.
- Each acceptance credits the freelancer once. The freelancer withdraws those tokens to a chosen wallet.
- Either person can propose a scope change. The other must agree. Already accepted work stays paid. Unpaid work must be submitted again against the new scope.
- Before the freelancer joins, the client can cancel and withdraw a full refund. After joining, cancellation needs both people to agree on how to split the remaining tokens.
- Either person can raise a dispute. This freezes further acceptance until both agree on a settlement. Earlier accepted payments stay available.

The contract has no owner who can take funds or decide who is right. If the two people cannot agree, disputed tokens remain locked. There is no automatic timeout or outside arbitrator. The interface must show this limit before a deposit.

## Data and network limits

Scope text, files and review notes belong off chain. The chain stores hashes, addresses, amounts and status events. Wallet transactions record who agreed; they do not prove that a file is truthful or that work meets a legal standard.

DEMO tokens have no cash value. Anyone can mint them. The token can only be deployed on local chain 31337 or Ethereum Sepolia 11155111. Stagepay is intended to use this fixed demo asset. Rebasing, taxed and malicious tokens are not supported. Deposit balance checks reject short transfers, but this is not a general purpose token compatibility layer.

No API key or wallet secret is needed for local tests. Future deployment must use an encrypted wallet or interactive signer. Never save a deployment private key in an env file or commit it.

## Guides and demo preparation

- [Step-by-step local setup](docs/SETUP.md)
- [Contract behavior and limits](docs/CONTRACT.md)
- [Draft project explanation](submission.md)
- [Captioned demo plans](demo/README.md)
- [Submission evidence still needed](docs/READINESS.md)
- [Brief presentation outline](docs/PRESENTATION-OUTLINE.md)

The demo plans are not a recorded video. Public deployment, playback and final submission approval remain pending.

## Sources

- [OpenZeppelin ERC20 contracts](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20)
- [3rd-Web-Hack rules](https://3rd-web-hack.devpost.com/rules)

This is a test-token hackathon prototype. It has not had an independent security audit.
