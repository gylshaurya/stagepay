# Public wallet workspace

The static workspace in `public-app/` implements Ethereum Sepolia wallet actions. It shares the escrow contract with the local workspace but does not expose the Python service, SQLite records, local demo accounts or deployment keys.

`npm run build:public` compiles contracts and produces `dist/`. `node scripts/build-public.mjs` bundles the checked-in ABI for static hosting. GitHub Pages publishes `dist/` from the pinned workflow. The release now records actual Sepolia deployment addresses and code hashes in `public-app/config.json`. Both contracts received exact source matches from Sourcify. If deployment configuration is absent, the public page shows setup pending and cannot send transactions.

Connect an Ethereum wallet on Sepolia. The client mints free DEMO tokens, approves the exact deposit, then creates an agreement for a different freelancer wallet. Each action needs a wallet confirmation and testnet gas. Never use real funds. Public Anvil keys are never used for Sepolia.

The client exports project text and shares that JSON with the freelancer. The freelancer opens the agreement ID and imports the text. Scope and delivery text must hash to the current on-chain values. Project names and milestone names are labels, not proof of identity. Share updated text after submitting work or proposing a scope change. Both parties can inspect real receipts, request revisions, agree to scope changes, dispute, settle, and withdraw credit. Settlement requires both wallets and can remain locked if they cannot agree.

Text stays in browser storage on that device and origin. Export a backup before clearing browser data. No encrypted cloud storage or automatic cross-device sync is claimed. The browser never uploads the private text to the RPC; contract calls contain hashes and token amounts. Explorer links contain public transaction hashes. External delivered-work links may have their own privacy policies.

Pending wallet actions are stored before signing. A missing response pauses later actions. Check pending receipts matches sender, nonce, destination and calldata; it never resends. Lost hashes are searched in at most 128 recent blocks. Unmatched or older cases stay paused for inspection. Web Locks serialize actions from multiple tabs on the same origin. Wallet replacement transactions with different intent are not silently accepted.

The release pins chain 11155111, deployed bytecode hashes, and the escrow's token address. A changed RPC chain or deployment stops writes. `tests/test_public.mjs` exercises the public core against separate real local contracts and wallets, including exchanged JSON, invalid imported text, wrong-wallet rejection, revisions, partial acceptance, scope changes, dispute settlement, withdrawals and lost-response recovery. This is integration evidence, not a claim of public Sepolia deployment.

## Encrypted deployment wallets

`node scripts/testnet-wallet.mjs --create` creates two project-only encrypted test wallets under ignored `.wallets/`. Their passwords stay in macOS Keychain entries `stagepay-testnet-client-v1` and `stagepay-testnet-freelancer-v1`. The command prints only public addresses. It never prints private keys or writes them to `.env`. Do not move these accounts to mainnet or send real funds to them. If Keychain access is unavailable, stop wallet actions and continue work that does not need signing.

Deployment receipts: [JSON](sepolia-deployment.json). Escrow: `0xc7455caAC7f58d2Ed5BBe2f084b7b90A883862c2`. Token: `0x38Ac218BA630C23D1E2003C4530740A4acb77551`. Both use free Sepolia faucet gas.

## Verified public walkthrough

[Walkthrough evidence](sepolia-walkthrough.json) records 13 confirmed Sepolia transactions, including partial acceptance, a mutually accepted scope change, dispute, settlement and both withdrawals. The final agreement is closed with zero remaining escrow and zero credit for both parties. The public page offers this illustrative agreement without requiring a wallet; its text and receipts are rechecked when opened. Browser-wallet signing still requires an installed wallet and a real confirmation.
