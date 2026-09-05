// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Stagepay} from "../contracts/Stagepay.sol";
import {DemoToken} from "../contracts/DemoToken.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

interface Vm {
    function prank(address) external;
    function startPrank(address) external;
    function stopPrank() external;
    function expectRevert(bytes4) external;
    function expectRevert() external;
    function chainId(uint256) external;
}

contract ShortTransferToken is ERC20 {
    constructor() ERC20("Short transfer", "SHORT") { _mint(msg.sender, 1000); }
    function _update(address from, address to, uint256 value) internal override {
        if (from != address(0) && to != address(0) && value > 0) {
            super._update(from, address(0), 1);
            value--;
        }
        super._update(from, to, value);
    }
}

contract StagepayTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant CLIENT = address(0xC1);
    address constant FREELANCER = address(0xF1);
    address constant STRANGER = address(0xBAD);
    bytes32 constant SCOPE = keccak256("three agreed milestones");
    bytes32 constant EVIDENCE = keccak256("first delivery");
    DemoToken token;
    Stagepay desk;
    uint256 id;

    function setUp() public {
        vm.chainId(31337);
        token = new DemoToken();
        desk = new Stagepay(token);
        token.mint(CLIENT, 1000 ether);
        vm.startPrank(CLIENT);
        token.approve(address(desk), type(uint256).max);
        uint256[] memory amounts = new uint256[](3);
        amounts[0] = 10 ether; amounts[1] = 20 ether; amounts[2] = 30 ether;
        id = desk.create(FREELANCER, SCOPE, amounts);
        vm.stopPrank();
    }

    function _join() internal { vm.prank(FREELANCER); desk.join(id, SCOPE); }
    function _submit(uint8 index) internal { vm.prank(FREELANCER); desk.submit(id, index, EVIDENCE); }
    function _accept(uint8 index) internal { vm.prank(CLIENT); desk.accept(id, index, SCOPE, EVIDENCE); }
    function _eq(uint256 a, uint256 b) internal pure { require(a == b, "amount mismatch"); }

    function testAcceptAndWithdrawExactlyOnce() public {
        _join(); _submit(0); _accept(0);
        _eq(desk.credits(FREELANCER), 10 ether);
        vm.expectRevert(Stagepay.WrongState.selector); _accept(0);
        vm.prank(FREELANCER); desk.withdraw(FREELANCER);
        _eq(token.balanceOf(FREELANCER), 10 ether);
        _eq(desk.totalHeld(), 50 ether);
        vm.expectRevert(Stagepay.InvalidInput.selector);
        vm.prank(FREELANCER); desk.withdraw(FREELANCER);
    }

    function testAllMilestonesCloseTheProject() public {
        _join();
        for (uint8 i; i < 3; i++) { _submit(i); _accept(i); }
        _eq(desk.credits(FREELANCER), 60 ether);
        vm.expectRevert(Stagepay.WrongState.selector);
        vm.prank(CLIENT); desk.proposeSettlement(id, 0);
        vm.prank(FREELANCER); desk.withdraw(FREELANCER);
        _eq(desk.totalHeld(), 0);
        _eq(token.balanceOf(address(desk)), 0);
    }

    function testRevisionDoesNotPayAndCanBeResubmitted() public {
        _join(); _submit(0);
        vm.prank(CLIENT); desk.requestRevision(id, 0, EVIDENCE, keccak256("missing mobile view"));
        _eq(desk.credits(FREELANCER), 0);
        vm.expectRevert(Stagepay.WrongState.selector); _accept(0);
        _submit(0); _accept(0);
        _eq(desk.credits(FREELANCER), 10 ether);
    }

    function testUnauthorizedActionsCannotMoveFunds() public {
        vm.expectRevert(Stagepay.NotAllowed.selector);
        vm.prank(STRANGER); desk.join(id, SCOPE);
        _join(); _submit(0);
        vm.expectRevert(Stagepay.NotAllowed.selector);
        vm.prank(STRANGER); desk.accept(id, 0, SCOPE, EVIDENCE);
        vm.expectRevert(Stagepay.NotAllowed.selector);
        vm.prank(CLIENT); desk.submit(id, 0, EVIDENCE);
        vm.expectRevert(Stagepay.NotAllowed.selector);
        vm.prank(STRANGER); desk.proposeSettlement(id, 60 ether);
        vm.expectRevert(Stagepay.InvalidInput.selector);
        vm.prank(STRANGER); desk.withdraw(STRANGER);
        _eq(desk.totalHeld(), 60 ether);
    }

    function testAcceptanceIsBoundToCurrentScopeAndEvidence() public {
        _join(); _submit(0);
        vm.prank(FREELANCER); desk.submit(id, 0, keccak256("changed delivery"));
        vm.expectRevert(Stagepay.StaleProposal.selector); _accept(0);
        vm.expectRevert(Stagepay.StaleProposal.selector);
        vm.prank(CLIENT); desk.accept(id, 0, keccak256("wrong scope"), keccak256("changed delivery"));
        _eq(desk.credits(FREELANCER), 0);
    }

    function testScopeChangeRequiresBothAndNewEvidence() public {
        _join(); _submit(0); _accept(0); _submit(1);
        bytes32 nextScope = keccak256("revised unpaid milestones");
        vm.prank(CLIENT); desk.proposeScope(id, nextScope);
        vm.expectRevert(Stagepay.WrongState.selector);
        vm.prank(CLIENT); desk.agreeScope(id, nextScope, 1);
        vm.expectRevert(Stagepay.WrongState.selector); _accept(1);
        vm.prank(FREELANCER); desk.agreeScope(id, nextScope, 1);
        vm.expectRevert(Stagepay.WrongState.selector);
        vm.prank(CLIENT); desk.accept(id, 1, nextScope, EVIDENCE);
        _submit(1);
        vm.prank(CLIENT); desk.accept(id, 1, nextScope, EVIDENCE);
        _eq(desk.credits(FREELANCER), 30 ether);
        (, , Stagepay.State first) = desk.milestones(id, 0);
        require(first == Stagepay.State.Accepted, "paid work was reset");
    }

    function testStaleScopeProposalCannotBeReplayed() public {
        _join(); bytes32 nextScope = keccak256("new scope");
        vm.prank(CLIENT); desk.proposeScope(id, nextScope);
        vm.prank(FREELANCER); desk.clearProposal(id, 1);
        vm.prank(CLIENT); desk.proposeScope(id, nextScope);
        vm.expectRevert(Stagepay.StaleProposal.selector);
        vm.prank(FREELANCER); desk.agreeScope(id, nextScope, 1);
        vm.prank(FREELANCER); desk.agreeScope(id, nextScope, 2);
    }

    function testClientCanCancelBeforeJoinOnly() public {
        vm.prank(CLIENT); desk.cancelBeforeJoin(id);
        _eq(desk.credits(CLIENT), 60 ether);
        vm.expectRevert(Stagepay.WrongState.selector); _join();
        vm.prank(CLIENT); desk.withdraw(CLIENT);
        _eq(token.balanceOf(CLIENT), 1000 ether);
        _eq(desk.totalHeld(), 0);
    }

    function testJoinedWorkNeedsMutualCancellation() public {
        _join();
        vm.expectRevert(Stagepay.WrongState.selector);
        vm.prank(CLIENT); desk.cancelBeforeJoin(id);
        vm.prank(CLIENT); desk.proposeSettlement(id, 12 ether);
        vm.expectRevert(Stagepay.WrongState.selector);
        vm.prank(CLIENT); desk.agreeSettlement(id, 12 ether, 1);
        vm.expectRevert(Stagepay.StaleProposal.selector);
        vm.prank(FREELANCER); desk.agreeSettlement(id, 13 ether, 1);
        vm.prank(FREELANCER); desk.agreeSettlement(id, 12 ether, 1);
        _eq(desk.credits(CLIENT), 48 ether);
        _eq(desk.credits(FREELANCER), 12 ether);
        vm.expectRevert(Stagepay.WrongState.selector);
        vm.prank(FREELANCER); desk.agreeSettlement(id, 12 ether, 1);
    }

    function testDisputeFreezesUnpaidWorkAndKeepsEarnedCredit() public {
        _join(); _submit(0); _accept(0); _submit(1);
        vm.prank(FREELANCER); desk.dispute(id, keccak256("scope disagreement"));
        vm.expectRevert(Stagepay.WrongState.selector); _accept(1);
        vm.expectRevert(Stagepay.WrongState.selector); _submit(2);
        vm.prank(FREELANCER); desk.withdraw(FREELANCER);
        vm.prank(CLIENT); desk.proposeSettlement(id, 15 ether);
        vm.prank(FREELANCER); desk.agreeSettlement(id, 15 ether, 2);
        _eq(desk.credits(FREELANCER), 15 ether);
        _eq(desk.credits(CLIENT), 35 ether);
    }

    function testDisputeInvalidatesOldSettlement() public {
        _join();
        vm.prank(CLIENT); desk.proposeSettlement(id, 0);
        vm.prank(FREELANCER); desk.dispute(id, keccak256("disagreement"));
        vm.expectRevert(Stagepay.WrongState.selector);
        vm.prank(FREELANCER); desk.agreeSettlement(id, 0, 1);
        vm.prank(CLIENT); desk.proposeSettlement(id, 0);
        vm.expectRevert(Stagepay.StaleProposal.selector);
        vm.prank(FREELANCER); desk.agreeSettlement(id, 0, 1);
        vm.prank(FREELANCER); desk.agreeSettlement(id, 0, 3);
    }

    function testProposalCanBeRejectedToResumeWork() public {
        _join();
        vm.prank(CLIENT); desk.proposeSettlement(id, 0);
        vm.expectRevert(Stagepay.WrongState.selector); _submit(0);
        vm.prank(FREELANCER); desk.clearProposal(id, 1);
        _submit(0); _accept(0);
    }

    function testShortTransferTokenIsRejectedAtomically() public {
        ShortTransferToken shortToken = new ShortTransferToken();
        Stagepay other = new Stagepay(shortToken);
        shortToken.approve(address(other), 100);
        uint256[] memory amounts = new uint256[](1); amounts[0] = 100;
        vm.expectRevert(Stagepay.UnsupportedToken.selector);
        other.create(FREELANCER, SCOPE, amounts);
        _eq(shortToken.balanceOf(address(this)), 1000);
        _eq(other.totalHeld(), 0);
    }

    function testInvalidDepositCannotCreateProject() public {
        uint256[] memory amounts = new uint256[](1);
        vm.expectRevert(Stagepay.InvalidInput.selector);
        vm.prank(CLIENT); desk.create(FREELANCER, SCOPE, amounts);
        amounts[0] = 1001 ether;
        vm.expectRevert();
        vm.prank(CLIENT); desk.create(FREELANCER, SCOPE, amounts);
        _eq(desk.nextProject(), 2);
        _eq(desk.totalHeld(), 60 ether);
    }

    function testNoWorkBeforeFreelancerAgrees() public {
        vm.expectRevert(Stagepay.WrongState.selector); _submit(0);
        vm.expectRevert(Stagepay.StaleProposal.selector);
        vm.prank(FREELANCER); desk.join(id, keccak256("wrong agreement"));
    }

    function testDemoTokenCannotDeployOnMainnet() public {
        vm.chainId(1);
        vm.expectRevert(); new DemoToken();
    }

    function testFuzzSettlementConservesDeposits(uint96 rawAmount, uint96 rawPayout) public {
        uint256 amount = uint256(rawAmount) + 1;
        uint256 payout = uint256(rawPayout) % (amount + 1);
        token.mint(CLIENT, amount);
        uint256[] memory amounts = new uint256[](1); amounts[0] = amount;
        vm.prank(CLIENT); uint256 second = desk.create(FREELANCER, SCOPE, amounts);
        vm.prank(FREELANCER); desk.join(second, SCOPE);
        vm.prank(FREELANCER); desk.proposeSettlement(second, payout);
        vm.prank(CLIENT); desk.agreeSettlement(second, payout, 1);
        _eq(desk.credits(FREELANCER) + desk.credits(CLIENT), amount);
        if (payout > 0) { vm.prank(FREELANCER); desk.withdraw(FREELANCER); }
        if (amount > payout) { vm.prank(CLIENT); desk.withdraw(CLIENT); }
        _eq(desk.totalHeld(), 60 ether);
        _eq(token.balanceOf(address(desk)), 60 ether);
    }
}
