// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "../src/IntentRegistry.sol";
import "../src/PaymentRouter.sol";
import "../src/AuctionEscrow.sol";

/**
 * @title Deploy
 * @notice Deployment script for Arc Coordination System contracts
 * @dev Deploy to Arc testnet: forge script script/Deploy.s.sol:Deploy --rpc-url arc_testnet --broadcast --verify
 */
contract Deploy is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerPrivateKey);

        // Deploy IntentRegistry
        IntentRegistry intentRegistry = new IntentRegistry();
        console.log("IntentRegistry deployed at:", address(intentRegistry));

        // Deploy PaymentRouter
        PaymentRouter paymentRouter = new PaymentRouter();
        console.log("PaymentRouter deployed at:", address(paymentRouter));

        // Deploy AuctionEscrow
        AuctionEscrow auctionEscrow = new AuctionEscrow(
            address(intentRegistry),
            address(paymentRouter)
        );
        console.log("AuctionEscrow deployed at:", address(auctionEscrow));

        vm.stopBroadcast();

        // Save deployment addresses to file
        string memory deploymentInfo = string.concat(
            "# Arc Coordination System - Deployment Info\n\n",
            "## Contract Addresses\n\n",
            "- IntentRegistry: ", vm.toString(address(intentRegistry)), "\n",
            "- PaymentRouter: ", vm.toString(address(paymentRouter)), "\n",
            "- AuctionEscrow: ", vm.toString(address(auctionEscrow)), "\n",
            "\n## Deployment Details\n\n",
            "- Chain: ", vm.toString(block.chainid), "\n",
            "- Block: ", vm.toString(block.number), "\n",
            "- Timestamp: ", vm.toString(block.timestamp), "\n"
        );

        vm.writeFile("deployment-info.md", deploymentInfo);
        console.log("\nDeployment info saved to deployment-info.md");
    }
}
