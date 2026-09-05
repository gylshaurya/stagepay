// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @notice Test-token milestone escrow. Both parties must agree to settle a dispute.
/// @dev Scope and evidence are hashes, not private documents stored on chain.
contract Stagepay is ReentrancyGuard {
    using SafeERC20 for IERC20;

    enum State { Pending, Submitted, Accepted }
    struct Milestone { uint256 amount; bytes32 evidence; State state; }
    struct Project {
        address client;
        address freelancer;
        bytes32 scope;
        uint256 remaining;
        uint8 count;
        bool joined;
        bool disputed;
        bool closed;
        bytes32 proposedScope;
        address scopeProposer;
        address settlementProposer;
        uint256 settlementPayout;
        uint256 proposalNonce;
    }

    IERC20 public immutable token;
    uint256 public nextProject = 1;
    uint256 public totalHeld;
    mapping(uint256 => Project) public projects;
    mapping(uint256 => mapping(uint8 => Milestone)) public milestones;
    mapping(address => uint256) public credits;

    error InvalidInput();
    error NotAllowed();
    error WrongState();
    error StaleProposal();
    error UnsupportedToken();

    event Created(uint256 indexed id, address indexed client, address indexed freelancer, bytes32 scope, uint256 deposit);
    event Joined(uint256 indexed id, bytes32 scope);
    event Submitted(uint256 indexed id, uint8 indexed milestone, bytes32 evidence);
    event Accepted(uint256 indexed id, uint8 indexed milestone, bytes32 scope, bytes32 evidence, uint256 amount);
    event RevisionRequested(uint256 indexed id, uint8 indexed milestone, bytes32 reason);
    event ScopeProposed(uint256 indexed id, address indexed proposer, bytes32 scope, uint256 nonce);
    event ScopeChanged(uint256 indexed id, bytes32 scope, uint256 nonce);
    event ProposalCleared(uint256 indexed id, uint256 nonce);
    event Disputed(uint256 indexed id, address indexed by, bytes32 reason);
    event SettlementProposed(uint256 indexed id, address indexed proposer, uint256 freelancerPayout, uint256 nonce);
    event Closed(uint256 indexed id, uint256 freelancerPayout, uint256 clientRefund);
    event Withdrawn(address indexed owner, address indexed recipient, uint256 amount);

    constructor(IERC20 asset) {
        if (address(asset).code.length == 0) revert InvalidInput();
        token = asset;
    }

    function create(address freelancer, bytes32 scope, uint256[] calldata amounts) external nonReentrant returns (uint256 id) {
        if (freelancer == address(0) || freelancer == msg.sender || scope == 0 || amounts.length == 0 || amounts.length > 3) revert InvalidInput();
        uint256 deposit;
        for (uint256 i; i < amounts.length; ++i) {
            if (amounts[i] == 0) revert InvalidInput();
            deposit += amounts[i];
        }
        uint256 beforeBalance = token.balanceOf(address(this));
        token.safeTransferFrom(msg.sender, address(this), deposit);
        if (token.balanceOf(address(this)) - beforeBalance != deposit) revert UnsupportedToken();
        id = nextProject++;
        Project storage p = projects[id];
        p.client = msg.sender;
        p.freelancer = freelancer;
        p.scope = scope;
        p.remaining = deposit;
        p.count = uint8(amounts.length);
        for (uint8 i; i < p.count; ++i) milestones[id][i].amount = amounts[i];
        totalHeld += deposit;
        emit Created(id, msg.sender, freelancer, scope, deposit);
    }

    function join(uint256 id, bytes32 expectedScope) external {
        Project storage p = projects[id];
        if (msg.sender != p.freelancer) revert NotAllowed();
        if (p.closed || p.joined) revert WrongState();
        if (expectedScope != p.scope) revert StaleProposal();
        p.joined = true;
        emit Joined(id, p.scope);
    }

    function submit(uint256 id, uint8 index, bytes32 evidence) external {
        Project storage p = projects[id];
        if (msg.sender != p.freelancer) revert NotAllowed();
        _active(p);
        if (index >= p.count || evidence == 0) revert InvalidInput();
        Milestone storage m = milestones[id][index];
        if (m.state == State.Accepted) revert WrongState();
        m.state = State.Submitted;
        m.evidence = evidence;
        emit Submitted(id, index, evidence);
    }

    /// @notice Expected hashes prevent accepting evidence that changed while a transaction was pending.
    function accept(uint256 id, uint8 index, bytes32 expectedScope, bytes32 expectedEvidence) external {
        Project storage p = projects[id];
        if (msg.sender != p.client) revert NotAllowed();
        _active(p);
        if (index >= p.count) revert InvalidInput();
        Milestone storage m = milestones[id][index];
        if (m.state != State.Submitted) revert WrongState();
        if (p.scope != expectedScope || m.evidence != expectedEvidence) revert StaleProposal();
        m.state = State.Accepted;
        p.remaining -= m.amount;
        credits[p.freelancer] += m.amount;
        emit Accepted(id, index, p.scope, m.evidence, m.amount);
        if (p.remaining == 0) {
            p.closed = true;
            emit Closed(id, 0, 0);
        }
    }

    function requestRevision(uint256 id, uint8 index, bytes32 expectedEvidence, bytes32 reason) external {
        Project storage p = projects[id];
        if (msg.sender != p.client) revert NotAllowed();
        _active(p);
        if (index >= p.count || reason == 0) revert InvalidInput();
        Milestone storage m = milestones[id][index];
        if (m.state != State.Submitted) revert WrongState();
        if (m.evidence != expectedEvidence) revert StaleProposal();
        m.state = State.Pending;
        emit RevisionRequested(id, index, reason);
    }

    function proposeScope(uint256 id, bytes32 scope) external {
        Project storage p = projects[id];
        _party(p);
        _active(p);
        if (scope == 0 || scope == p.scope) revert InvalidInput();
        p.proposedScope = scope;
        p.scopeProposer = msg.sender;
        emit ScopeProposed(id, msg.sender, scope, ++p.proposalNonce);
    }

    function agreeScope(uint256 id, bytes32 scope, uint256 nonce) external {
        Project storage p = projects[id];
        _party(p);
        if (p.closed || p.disputed || p.scopeProposer == address(0) || p.scopeProposer == msg.sender) revert WrongState();
        if (scope != p.proposedScope || nonce != p.proposalNonce) revert StaleProposal();
        p.scope = scope;
        p.scopeProposer = address(0);
        p.proposedScope = 0;
        // Accepted milestones stay paid. Unpaid work must be submitted against the new agreement.
        for (uint8 i; i < p.count; ++i) {
            Milestone storage m = milestones[id][i];
            if (m.state != State.Accepted) { m.state = State.Pending; m.evidence = 0; }
        }
        emit ScopeChanged(id, scope, nonce);
    }

    /// @notice Either party can reject a pending proposal, so proposals cannot freeze work forever.
    function clearProposal(uint256 id, uint256 nonce) external {
        Project storage p = projects[id];
        _party(p);
        if (p.closed || (p.scopeProposer == address(0) && p.settlementProposer == address(0))) revert WrongState();
        if (nonce != p.proposalNonce) revert StaleProposal();
        p.scopeProposer = address(0);
        p.proposedScope = 0;
        p.settlementProposer = address(0);
        p.settlementPayout = 0;
        emit ProposalCleared(id, nonce);
    }

    function dispute(uint256 id, bytes32 reason) external {
        Project storage p = projects[id];
        _party(p);
        if (!p.joined || p.closed || p.disputed || reason == 0) revert WrongState();
        p.disputed = true;
        // A dispute invalidates all earlier proposals. It can only end through a fresh mutual settlement.
        p.scopeProposer = address(0);
        p.proposedScope = 0;
        p.settlementProposer = address(0);
        p.settlementPayout = 0;
        ++p.proposalNonce;
        emit Disputed(id, msg.sender, reason);
    }

    function proposeSettlement(uint256 id, uint256 freelancerPayout) external {
        Project storage p = projects[id];
        _party(p);
        if (!p.joined || p.closed || p.scopeProposer != address(0) || p.settlementProposer != address(0)) revert WrongState();
        if (freelancerPayout > p.remaining) revert InvalidInput();
        p.settlementProposer = msg.sender;
        p.settlementPayout = freelancerPayout;
        emit SettlementProposed(id, msg.sender, freelancerPayout, ++p.proposalNonce);
    }

    function agreeSettlement(uint256 id, uint256 freelancerPayout, uint256 nonce) external {
        Project storage p = projects[id];
        _party(p);
        if (p.closed || p.settlementProposer == address(0) || msg.sender == p.settlementProposer) revert WrongState();
        if (nonce != p.proposalNonce || freelancerPayout != p.settlementPayout) revert StaleProposal();
        _close(id, p, freelancerPayout);
    }

    function cancelBeforeJoin(uint256 id) external {
        Project storage p = projects[id];
        if (msg.sender != p.client) revert NotAllowed();
        if (p.joined || p.closed) revert WrongState();
        _close(id, p, 0);
    }

    /// @notice Pull payments keep settlement separate from token transfer and allow an alternate recipient.
    function withdraw(address recipient) external nonReentrant {
        uint256 amount = credits[msg.sender];
        if (recipient == address(0) || recipient == address(this) || amount == 0) revert InvalidInput();
        credits[msg.sender] = 0;
        totalHeld -= amount;
        token.safeTransfer(recipient, amount);
        emit Withdrawn(msg.sender, recipient, amount);
    }

    function _close(uint256 id, Project storage p, uint256 payout) private {
        uint256 refund = p.remaining - payout;
        p.remaining = 0;
        p.closed = true;
        p.settlementProposer = address(0);
        p.settlementPayout = 0;
        credits[p.freelancer] += payout;
        credits[p.client] += refund;
        emit Closed(id, payout, refund);
    }

    function _party(Project storage p) private view {
        if (msg.sender != p.client && msg.sender != p.freelancer) revert NotAllowed();
    }

    function _active(Project storage p) private view {
        if (!p.joined || p.closed || p.disputed || p.scopeProposer != address(0) || p.settlementProposer != address(0)) revert WrongState();
    }
}
