# Run Stagepay locally

Stagepay keeps a small freelance agreement, the submitted work and test-payment receipts together. This version runs on your computer. It uses real contracts on a local Anvil chain; it is not a public payment service.

## Requirements

- Node.js and npm for pinned contract and font packages.
- Python 3.10 or newer. The service uses only the Python standard library.
- Foundry commands `forge`, `cast` and `anvil` on your PATH.
- Free local ports 4321 for the workspace and 18545 for its dedicated chain.

No API key, browser wallet or purchased token is needed. Anvil provides unlocked demo accounts. Their tokens have no cash value. The startup scripts refuse to take over a process that they do not own.

From the repository directory:

```sh
npm ci --ignore-scripts
npm run chain
npm start
```

Open http://127.0.0.1:4321. `npm start` runs the owned service in the background. Use `npm run dev` instead if you want a foreground process and its startup message in your terminal.

## Try the complete workflow

1. Select Client under Demo role. Choose New project. Write the scope and one to three milestones, with positive DEMO amounts and at most two decimal places. Read the funding limits, check the box and fund the agreement.
2. Switch to Freelancer and choose Agree and start work. The contract checks the exact scope hash.
3. Open an unpaid milestone. Add a real link to the work and a short note, then submit it.
4. Switch to Client. Accept the milestone or open Request a revision. A revision records a reason and releases no tokens. The freelancer can submit updated evidence.
5. After acceptance, switch to Freelancer. Wallet credit shows the total available across this wallet's projects. Withdraw test tokens sends that credit to its local wallet. A second withdrawal with no new credit fails.
6. Open Agreement options to propose a scope change. The other person must agree. Accepted work stays accepted. Unpaid milestones need fresh evidence tied to the new scope.
7. If needed, raise a dispute and propose a settlement. The other person must accept the proposed split. Neither person can settle alone.
8. Open a receipt to inspect its transaction hash, block and agreement fingerprint. Export record saves a JSON copy of the selected project's record.

The roles are a local demonstration. They are not separate signed-in accounts. The network panel shows the actual local wallets and contracts. Public Sepolia deployment remains unconfigured.

## Verify the code

```sh
npm run test:contracts
npm run test:service
```

The service checks need the local chain running. They deploy separate contracts and use a temporary database, leaving the workspace's agreements alone. Existing checks cover payments, revisions, scope changes, roles, settlement, cancellation, stale decisions and interrupted broadcasts.

## Stop, restart and preserve records

```sh
npm stop
npm start
```

Stopping the workspace keeps its local chain and records. Anvil saves chain state under `.local/`; SQLite stores project records in `.local/workspace.sqlite3`. Keep the whole directory together. Before making a backup, stop the workspace and ensure the chain state has been flushed. Do not copy only the database and treat it as a complete chain backup.

`npm run chain` reuses the saved local deployment if it is healthy. After an unclean shutdown, inspect the connection and receipts before making another decision. The startup script stops if the saved deployment and chain do not agree.

## If an action is interrupted

The service saves an intended transaction and sender nonce before broadcasting. If it cannot determine the result, later writes pause. This prevents an automatic second payment. Read-only records remain available.

Preserve `.local/`. Inspect the pending action, its sender nonce and any transaction hash against the local node. A confirmed transaction must be reconciled with the saved project state before writes resume. Automatic recovery is not implemented in this version. Deleting a pending row or sending the action again is not a recovery procedure.

If a second tab has an old project version, refresh it before deciding. If the local chain is unavailable, restart the owned chain and refresh the connection. If a port is occupied by another service, leave that service alone.

## Public deployment boundary

This server signs with unlocked local demo accounts and binds only to loopback. A public version needs a browser wallet signer, suitable account access controls, a verified testnet deployment, an allowed free hosting route and public receipt links. A tunnel to this local signer is not that public version. The current source and local demonstration can be reviewed without those unfinished parts.
