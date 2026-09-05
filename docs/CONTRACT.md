# How the agreement works

A Stagepay agreement holds a fixed set of test-token amounts for one client and one freelancer. The contract stores hashes and payment decisions. SQLite keeps the readable scope, delivery links and review history. This lets someone check which exact scope and evidence were accepted without putting the full documents on chain.

## Actions and their effect

| Action | Who can do it | Required state | Result |
| --- | --- | --- | --- |
| Fund | Client | New agreement, 1 to 3 positive amounts | Tokens enter escrow; freelancer and scope hash are fixed |
| Join | Named freelancer | Not joined or closed; matching scope | Work can begin |
| Submit | Named freelancer | Joined, open, not disputed, no pending proposal | Saves evidence hash for an unpaid milestone |
| Accept | Client | Submitted milestone; matching current scope and evidence | Credits its exact amount once |
| Request revision | Client | Submitted milestone; matching evidence | Returns it to pending, with no payment |
| Propose scope | Either party | Active agreement; different nonzero scope hash | Pauses normal work until the proposal is agreed or cleared |
| Agree scope | The other party | Matching scope proposal and nonce; no dispute | Changes scope and clears unpaid evidence; paid milestones stay paid |
| Clear proposal | Either party | Matching current proposal nonce | Removes that proposal |
| Dispute | Either party | Joined, open, not already disputed | Pauses unpaid work and invalidates older proposals |
| Propose settlement | Either party | Joined, open, no pending proposal | Offers a payout from the remaining escrow, including zero if desired |
| Agree settlement | The other party | Matching payout and proposal nonce | Closes the agreement and credits payout and refund |
| Cancel before join | Client | Freelancer has not joined | Closes it and credits a full refund |
| Withdraw | Owner of positive credit | Valid recipient | Sends all that wallet's credit and sets it to zero |

A pending proposal prevents normal submission, acceptance and revision. Either party can clear it. A dispute needs a fresh mutual settlement; clearing a proposal does not clear the dispute. After joining, the client cannot take all remaining escrow back without the other person's agreement.

## Amounts and receipts

The UI accepts positive milestone amounts with two decimal places. The contract uses integer token units with 18 decimals. A 10.25 DEMO milestone is 10,250,000,000,000,000,000 units. Acceptance moves an amount from that project's remaining balance to the freelancer's credit. The tokens leave the contract only on withdrawal.

Credit is wallet-wide, so one withdrawal can include accepted payments from several agreements. Each project's history can show the withdrawal made while it was selected; that entry is not proof that the entire withdrawal came from that one project. The current history label and credit panel should be read together.

Every successful service action waits for a real local receipt before saving the resulting project state. A receipt proves that a local transaction executed. It does not prove that a linked file was good work or that the parties were independent people. The source includes receipt, role and conservation checks; it does not claim an independent security audit.

## Hashes and stale decisions

Scope is the Keccak-256 hash of the stored scope text. Evidence hashes the compact, sorted JSON containing the note and URL. Whitespace and link changes can produce a different evidence hash. Accept checks both the current scope and current evidence, preventing an old open review from approving changed work.

The local service also checks project versions and binds a request ID to the exact request. An exact completed replay returns its saved result. Reusing that ID for different details fails. If a transaction's result is uncertain, writes pause instead of automatically sending a second transaction.

## Limits

There is no administrator who decides a dispute, automatic timeout or outside arbitrator. If the people never agree, remaining disputed tokens stay locked. Scope changes affect the shared scope text; they do not change milestone amounts or already accepted work.

DEMO is freely mintable and has no cash value. Its constructor allows only local chain 31337 and Sepolia 11155111. The service currently permits only its dedicated local chain. Taxed, rebasing or malicious token behavior is outside the supported asset model. Balance checks reject short deposits, and OpenZeppelin's safe transfers and reentrancy guard protect token operations.

The chain adds a shared rule for who can release each payment. A database alone could keep notes and receipts, but its operator would also control those payment decisions. The local demo still trusts its service and role switch for convenience. A public implementation must replace that convenience with real wallet signing and appropriate access controls.

Implementation: [Stagepay.sol](../contracts/Stagepay.sol), [DemoToken.sol](../contracts/DemoToken.sol), [server.py](../server.py). Library reference: [OpenZeppelin ERC20](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20).
