// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import "../src/IntentRegistry.sol";

contract IntentRegistryTest is Test {
    IntentRegistry public registry;

    address public actor1 = address(0x1);
    address public actor2 = address(0x2);

    bytes32 public constant INTENT_HASH_1 = keccak256("intent1");
    bytes32 public constant INTENT_HASH_2 = keccak256("intent2");
    bytes32 public constant AP2_MANDATE_1 = keccak256("mandate1");
    bytes32 public constant AP2_MANDATE_2 = keccak256("mandate2");

    function setUp() public {
        registry = new IntentRegistry();
    }

    function testRegisterIntent() public {
        vm.startPrank(actor1);

        uint256 validUntil = block.timestamp + 1 hours;
        bytes32 intentId = registry.registerIntent(
            INTENT_HASH_1,
            validUntil,
            AP2_MANDATE_1,
            "USD"
        );

        assertNotEq(intentId, bytes32(0), "Intent ID should not be zero");

        IntentRegistry.IntentMetadata memory intent = registry.getIntent(intentId);
        assertEq(intent.intentHash, INTENT_HASH_1);
        assertEq(intent.actor, actor1);
        assertEq(intent.validUntil, validUntil);
        assertEq(intent.ap2MandateId, AP2_MANDATE_1);
        assertTrue(intent.isActive);
        assertFalse(intent.isMatched);

        vm.stopPrank();
    }

    function testRegisterIntentWithInvalidTimestamp() public {
        vm.startPrank(actor1);

        uint256 invalidValidUntil = block.timestamp - 1;

        vm.expectRevert(IntentRegistry.InvalidTimestamp.selector);
        registry.registerIntent(
            INTENT_HASH_1,
            invalidValidUntil,
            AP2_MANDATE_1,
            "USD"
        );

        vm.stopPrank();
    }

    function testCancelIntent() public {
        vm.startPrank(actor1);

        uint256 validUntil = block.timestamp + 1 hours;
        bytes32 intentId = registry.registerIntent(
            INTENT_HASH_1,
            validUntil,
            AP2_MANDATE_1,
            "USD"
        );

        registry.cancelIntent(intentId);

        IntentRegistry.IntentMetadata memory intent = registry.getIntent(intentId);
        assertFalse(intent.isActive);

        vm.stopPrank();
    }

    function testCancelIntentUnauthorized() public {
        vm.prank(actor1);
        uint256 validUntil = block.timestamp + 1 hours;
        bytes32 intentId = registry.registerIntent(
            INTENT_HASH_1,
            validUntil,
            AP2_MANDATE_1,
            "USD"
        );

        vm.prank(actor2);
        vm.expectRevert(IntentRegistry.UnauthorizedActor.selector);
        registry.cancelIntent(intentId);
    }

    function testMarkAsMatched() public {
        vm.prank(actor1);
        uint256 validUntil = block.timestamp + 1 hours;
        bytes32 intentId = registry.registerIntent(
            INTENT_HASH_1,
            validUntil,
            AP2_MANDATE_1,
            "USD"
        );

        registry.markAsMatched(intentId);

        IntentRegistry.IntentMetadata memory intent = registry.getIntent(intentId);
        assertTrue(intent.isMatched);
    }

    function testIsIntentValid() public {
        vm.prank(actor1);
        uint256 validUntil = block.timestamp + 1 hours;
        bytes32 intentId = registry.registerIntent(
            INTENT_HASH_1,
            validUntil,
            AP2_MANDATE_1,
            "USD"
        );

        assertTrue(registry.isIntentValid(intentId));

        // Cancel intent
        vm.prank(actor1);
        registry.cancelIntent(intentId);

        assertFalse(registry.isIntentValid(intentId));
    }

    function testGetActorIntents() public {
        vm.startPrank(actor1);

        uint256 validUntil = block.timestamp + 1 hours;

        bytes32 intentId1 = registry.registerIntent(
            INTENT_HASH_1,
            validUntil,
            AP2_MANDATE_1,
            "USD"
        );

        bytes32 intentId2 = registry.registerIntent(
            INTENT_HASH_2,
            validUntil,
            AP2_MANDATE_2,
            "ETH"
        );

        bytes32[] memory actorIntents = registry.getActorIntents(actor1);
        assertEq(actorIntents.length, 2);
        assertEq(actorIntents[0], intentId1);
        assertEq(actorIntents[1], intentId2);

        vm.stopPrank();
    }

    function testIntentExpiry() public {
        vm.prank(actor1);
        uint256 validUntil = block.timestamp + 1 hours;
        bytes32 intentId = registry.registerIntent(
            INTENT_HASH_1,
            validUntil,
            AP2_MANDATE_1,
            "USD"
        );

        assertTrue(registry.isIntentValid(intentId));

        // Fast forward past expiry
        vm.warp(validUntil + 1);

        assertFalse(registry.isIntentValid(intentId));
    }
}
