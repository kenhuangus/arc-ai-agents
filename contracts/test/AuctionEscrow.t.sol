// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import "../src/IntentRegistry.sol";
import "../src/PaymentRouter.sol";
import "../src/AuctionEscrow.sol";

contract AuctionEscrowTest is Test {
    IntentRegistry public registry;
    PaymentRouter public paymentRouter;
    AuctionEscrow public escrow;

    address public bidder = address(0x1);
    address public asker = address(0x2);
    address public oracle = address(0x3);

    bytes32 public constant INTENT_HASH_1 = keccak256("bid_intent");
    bytes32 public constant INTENT_HASH_2 = keccak256("ask_intent");
    bytes32 public constant AP2_MANDATE_1 = keccak256("mandate1");
    bytes32 public constant AP2_MANDATE_2 = keccak256("mandate2");

    function setUp() public {
        registry = new IntentRegistry();
        paymentRouter = new PaymentRouter();
        escrow = new AuctionEscrow(address(registry), address(paymentRouter));

        // Setup oracle and mandates
        paymentRouter.authorizeOracle(oracle);
        paymentRouter.registerMandate(AP2_MANDATE_1);
        paymentRouter.registerMandate(AP2_MANDATE_2);

        // Give test addresses some ETH
        vm.deal(bidder, 10 ether);
        vm.deal(asker, 10 ether);
    }

    function testCreateMatch() public {
        // Create bid and ask intents
        vm.prank(bidder);
        bytes32 bidIntentId = registry.registerIntent(
            INTENT_HASH_1,
            block.timestamp + 1 hours,
            AP2_MANDATE_1,
            "USD"
        );

        vm.prank(asker);
        bytes32 askIntentId = registry.registerIntent(
            INTENT_HASH_2,
            block.timestamp + 1 hours,
            AP2_MANDATE_2,
            "USD"
        );

        // Create match
        uint256 matchPrice = 100 ether;
        bytes32 matchId = escrow.createMatch(bidIntentId, askIntentId, matchPrice);

        assertNotEq(matchId, bytes32(0), "Match ID should not be zero");

        AuctionEscrow.Match memory matchData = escrow.getMatch(matchId);
        assertEq(matchData.bidIntentId, bidIntentId);
        assertEq(matchData.askIntentId, askIntentId);
        assertEq(matchData.bidder, bidder);
        assertEq(matchData.asker, asker);
        assertEq(matchData.matchPrice, matchPrice);
        assertEq(uint(matchData.status), uint(AuctionEscrow.MatchStatus.Pending));
    }

    function testFundEscrow() public {
        // Setup intents and match
        vm.prank(bidder);
        bytes32 bidIntentId = registry.registerIntent(
            INTENT_HASH_1,
            block.timestamp + 1 hours,
            AP2_MANDATE_1,
            "USD"
        );

        vm.prank(asker);
        bytes32 askIntentId = registry.registerIntent(
            INTENT_HASH_2,
            block.timestamp + 1 hours,
            AP2_MANDATE_2,
            "USD"
        );

        uint256 matchPrice = 1 ether;
        bytes32 matchId = escrow.createMatch(bidIntentId, askIntentId, matchPrice);

        // Fund escrow from both parties
        vm.prank(bidder);
        escrow.fundEscrow{value: matchPrice}(matchId);

        vm.prank(asker);
        escrow.fundEscrow{value: matchPrice}(matchId);

        AuctionEscrow.Match memory matchData = escrow.getMatch(matchId);
        assertEq(uint(matchData.status), uint(AuctionEscrow.MatchStatus.Funded));
        assertEq(matchData.bidAmount, matchPrice);
        assertEq(matchData.askAmount, matchPrice);
    }

    function testSettleMatch() public {
        // Setup intents and match
        vm.prank(bidder);
        bytes32 bidIntentId = registry.registerIntent(
            INTENT_HASH_1,
            block.timestamp + 1 hours,
            AP2_MANDATE_1,
            "USD"
        );

        vm.prank(asker);
        bytes32 askIntentId = registry.registerIntent(
            INTENT_HASH_2,
            block.timestamp + 1 hours,
            AP2_MANDATE_2,
            "USD"
        );

        uint256 matchPrice = 1 ether;
        bytes32 matchId = escrow.createMatch(bidIntentId, askIntentId, matchPrice);

        // Fund escrow
        vm.prank(bidder);
        escrow.fundEscrow{value: matchPrice}(matchId);

        vm.prank(asker);
        escrow.fundEscrow{value: matchPrice}(matchId);

        // Record payment verification from oracle
        string memory stripePaymentId = "pi_test123";
        vm.prank(oracle);
        paymentRouter.recordPaymentVerification(
            stripePaymentId,
            matchPrice,
            bidder,
            asker,
            AP2_MANDATE_1
        );

        // Settle match
        uint256 askerBalanceBefore = asker.balance;
        bytes32 ap2ProofHash = keccak256("proof");

        escrow.settleMatch(matchId, ap2ProofHash, stripePaymentId);

        AuctionEscrow.Match memory matchData = escrow.getMatch(matchId);
        assertEq(uint(matchData.status), uint(AuctionEscrow.MatchStatus.Settled));
        assertEq(matchData.ap2ProofHash, ap2ProofHash);

        // Check asker received funds
        uint256 askerBalanceAfter = asker.balance;
        assertEq(askerBalanceAfter - askerBalanceBefore, matchPrice * 2);
    }

    function testCancelMatchAfterTimeout() public {
        // Setup intents and match
        vm.prank(bidder);
        bytes32 bidIntentId = registry.registerIntent(
            INTENT_HASH_1,
            block.timestamp + 100 hours,
            AP2_MANDATE_1,
            "USD"
        );

        vm.prank(asker);
        bytes32 askIntentId = registry.registerIntent(
            INTENT_HASH_2,
            block.timestamp + 100 hours,
            AP2_MANDATE_2,
            "USD"
        );

        uint256 matchPrice = 1 ether;
        bytes32 matchId = escrow.createMatch(bidIntentId, askIntentId, matchPrice);

        // Fund escrow
        vm.prank(bidder);
        escrow.fundEscrow{value: matchPrice}(matchId);

        uint256 bidderBalanceBefore = bidder.balance;

        // Fast forward past settlement timeout
        vm.warp(block.timestamp + 49 hours);

        // Cancel match
        escrow.cancelMatch(matchId);

        AuctionEscrow.Match memory matchData = escrow.getMatch(matchId);
        assertEq(uint(matchData.status), uint(AuctionEscrow.MatchStatus.Cancelled));

        // Check refunds
        uint256 bidderBalanceAfter = bidder.balance;
        assertEq(bidderBalanceAfter - bidderBalanceBefore, matchPrice);
    }

    function testDisputeMatch() public {
        // Setup and fund match
        vm.prank(bidder);
        bytes32 bidIntentId = registry.registerIntent(
            INTENT_HASH_1,
            block.timestamp + 1 hours,
            AP2_MANDATE_1,
            "USD"
        );

        vm.prank(asker);
        bytes32 askIntentId = registry.registerIntent(
            INTENT_HASH_2,
            block.timestamp + 1 hours,
            AP2_MANDATE_2,
            "USD"
        );

        uint256 matchPrice = 1 ether;
        bytes32 matchId = escrow.createMatch(bidIntentId, askIntentId, matchPrice);

        vm.prank(bidder);
        escrow.fundEscrow{value: matchPrice}(matchId);

        vm.prank(asker);
        escrow.fundEscrow{value: matchPrice}(matchId);

        // Dispute match
        vm.prank(bidder);
        escrow.disputeMatch(matchId, "Payment not received");

        AuctionEscrow.Match memory matchData = escrow.getMatch(matchId);
        assertEq(uint(matchData.status), uint(AuctionEscrow.MatchStatus.Disputed));
    }

    function testCannotSettleWithoutValidPayment() public {
        // Setup and fund match
        vm.prank(bidder);
        bytes32 bidIntentId = registry.registerIntent(
            INTENT_HASH_1,
            block.timestamp + 1 hours,
            AP2_MANDATE_1,
            "USD"
        );

        vm.prank(asker);
        bytes32 askIntentId = registry.registerIntent(
            INTENT_HASH_2,
            block.timestamp + 1 hours,
            AP2_MANDATE_2,
            "USD"
        );

        uint256 matchPrice = 1 ether;
        bytes32 matchId = escrow.createMatch(bidIntentId, askIntentId, matchPrice);

        vm.prank(bidder);
        escrow.fundEscrow{value: matchPrice}(matchId);

        vm.prank(asker);
        escrow.fundEscrow{value: matchPrice}(matchId);

        // Try to settle without payment verification
        bytes32 ap2ProofHash = keccak256("proof");
        vm.expectRevert(AuctionEscrow.InvalidPaymentProof.selector);
        escrow.settleMatch(matchId, ap2ProofHash, "invalid_payment_id");
    }
}
