# Stagepay

Stagepay is a milestone desk for student freelancers. The client sets aside test tokens, both people agree on the work, and each payment becomes available when the client accepts the submitted evidence.

This first milestone implements the contracts. The product interface, public testnet deployment and video are still being built. No real payment service or live deployment is claimed here.

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

## Sources

- [OpenZeppelin ERC20 contracts](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20)
- [3rd-Web-Hack rules](https://3rd-web-hack.devpost.com/rules)

This is a test-token hackathon prototype. It has not had an independent security audit.
