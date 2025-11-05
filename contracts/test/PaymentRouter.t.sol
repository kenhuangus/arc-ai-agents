// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import "../src/PaymentRouter.sol";

contract PaymentRouterTest is Test {
    PaymentRouter public router;

    address public owner;
    address public oracle = address(0x2);
    address public payer = address(0x3);
    address public payee = address(0x4);

    bytes32 public constant AP2_MANDATE_1 = keccak256("mandate1");
    bytes32 public constant AP2_MANDATE_2 = keccak256("mandate2");

    function setUp() public {
        router = new PaymentRouter();
        owner = address(this);
    }

    function testAuthorizeOracle() public {
        router.authorizeOracle(oracle);
        assertTrue(router.isAuthorizedOracle(oracle));
    }

    function testRevokeOracle() public {
        router.authorizeOracle(oracle);
        assertTrue(router.isAuthorizedOracle(oracle));

        router.revokeOracle(oracle);
        assertFalse(router.isAuthorizedOracle(oracle));
    }

    function testRegisterMandate() public {
        router.registerMandate(AP2_MANDATE_1);
        assertTrue(router.isMandateValid(AP2_MANDATE_1));
    }

    function testRevokeMandate() public {
        router.registerMandate(AP2_MANDATE_1);
        assertTrue(router.isMandateValid(AP2_MANDATE_1));

        router.revokeMandate(AP2_MANDATE_1);
        assertFalse(router.isMandateValid(AP2_MANDATE_1));
    }

    function testRecordPaymentVerification() public {
        // Setup
        router.authorizeOracle(oracle);
        router.registerMandate(AP2_MANDATE_1);

        // Record payment
        string memory stripePaymentId = "pi_test123";
        uint256 amount = 1000;

        vm.prank(oracle);
        router.recordPaymentVerification(
            stripePaymentId,
            amount,
            payer,
            payee,
            AP2_MANDATE_1
        );

        // Verify payment was recorded
        PaymentRouter.PaymentVerification memory verification = router.getPaymentVerification(
            stripePaymentId
        );

        assertEq(verification.amount, amount);
        assertEq(verification.payer, payer);
        assertEq(verification.payee, payee);
        assertEq(verification.ap2MandateId, AP2_MANDATE_1);
        assertTrue(verification.verified);
    }

    function testRecordPaymentWithInvalidMandate() public {
        router.authorizeOracle(oracle);

        string memory stripePaymentId = "pi_test123";
        uint256 amount = 1000;

        vm.prank(oracle);
        vm.expectRevert(PaymentRouter.InvalidMandate.selector);
        router.recordPaymentVerification(
            stripePaymentId,
            amount,
            payer,
            payee,
            AP2_MANDATE_1 // Not registered
        );
    }

    function testRecordPaymentUnauthorizedOracle() public {
        router.registerMandate(AP2_MANDATE_1);

        string memory stripePaymentId = "pi_test123";
        uint256 amount = 1000;

        vm.prank(oracle); // Not authorized
        vm.expectRevert(PaymentRouter.Unauthorized.selector);
        router.recordPaymentVerification(
            stripePaymentId,
            amount,
            payer,
            payee,
            AP2_MANDATE_1
        );
    }

    function testVerifyPayment() public {
        router.authorizeOracle(oracle);
        router.registerMandate(AP2_MANDATE_1);

        string memory stripePaymentId = "pi_test123";
        uint256 amount = 1000;

        vm.prank(oracle);
        router.recordPaymentVerification(
            stripePaymentId,
            amount,
            payer,
            payee,
            AP2_MANDATE_1
        );

        // Verify with exact amount
        assertTrue(router.verifyPayment(stripePaymentId, amount));

        // Verify with lower expected amount
        assertTrue(router.verifyPayment(stripePaymentId, amount - 100));

        // Verify with higher expected amount (should fail)
        assertFalse(router.verifyPayment(stripePaymentId, amount + 100));
    }

    function testCannotRecordDuplicatePayment() public {
        router.authorizeOracle(oracle);
        router.registerMandate(AP2_MANDATE_1);

        string memory stripePaymentId = "pi_test123";
        uint256 amount = 1000;

        vm.startPrank(oracle);

        router.recordPaymentVerification(
            stripePaymentId,
            amount,
            payer,
            payee,
            AP2_MANDATE_1
        );

        vm.expectRevert(PaymentRouter.PaymentAlreadyVerified.selector);
        router.recordPaymentVerification(
            stripePaymentId,
            amount,
            payer,
            payee,
            AP2_MANDATE_1
        );

        vm.stopPrank();
    }

    function testTransferOwnership() public {
        address newOwner = address(0x999);
        router.transferOwnership(newOwner);

        // Old owner should not be able to authorize oracle anymore
        vm.expectRevert(PaymentRouter.Unauthorized.selector);
        router.authorizeOracle(oracle);

        // New owner should be able to authorize oracle
        vm.prank(newOwner);
        router.authorizeOracle(oracle);
        assertTrue(router.isAuthorizedOracle(oracle));
    }

    function testRecordPaymentWithZeroAmount() public {
        router.authorizeOracle(oracle);
        router.registerMandate(AP2_MANDATE_1);

        string memory stripePaymentId = "pi_test123";

        vm.prank(oracle);
        vm.expectRevert(PaymentRouter.InvalidAmount.selector);
        router.recordPaymentVerification(
            stripePaymentId,
            0, // Zero amount
            payer,
            payee,
            AP2_MANDATE_1
        );
    }
}
