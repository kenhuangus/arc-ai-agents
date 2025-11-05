// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/**
 * @title IntentRegistry
 * @notice Stores intent hashes and metadata on-chain with minimal footprint
 * @dev Intents are signed, timestamped objects with AP2 mandate references
 */
contract IntentRegistry {
    /// @notice Intent metadata structure
    struct IntentMetadata {
        bytes32 intentHash;          // Hash of the full intent payload
        address actor;               // Intent creator address
        uint256 timestamp;           // Creation timestamp
        uint256 validUntil;          // Expiration timestamp
        bytes32 ap2MandateId;        // Reference to AP2 mandate credential
        string settlementAsset;      // Asset type for settlement (e.g., "USD", "ETH")
        bool isActive;               // Intent status
        bool isMatched;              // Whether intent has been matched
    }

    /// @notice Mapping from intent ID to metadata
    mapping(bytes32 => IntentMetadata) public intents;

    /// @notice Mapping from actor to their intent IDs
    mapping(address => bytes32[]) public actorIntents;

    /// @notice Total number of intents registered
    uint256 public totalIntents;

    /// @notice Events
    event IntentRegistered(
        bytes32 indexed intentId,
        bytes32 indexed intentHash,
        address indexed actor,
        uint256 timestamp,
        uint256 validUntil,
        bytes32 ap2MandateId,
        string settlementAsset
    );

    event IntentCancelled(bytes32 indexed intentId, address indexed actor);
    event IntentMatched(bytes32 indexed intentId, address indexed actor);

    /// @notice Errors
    error IntentAlreadyExists();
    error IntentNotFound();
    error IntentExpired();
    error IntentNotActive();
    error UnauthorizedActor();
    error InvalidTimestamp();

    /**
     * @notice Register a new intent on-chain
     * @param _intentHash Hash of the full intent payload (stored off-chain)
     * @param _validUntil Expiration timestamp for the intent
     * @param _ap2MandateId Reference to the AP2 payment mandate
     * @param _settlementAsset Asset type for settlement
     * @return intentId Unique identifier for the intent
     */
    function registerIntent(
        bytes32 _intentHash,
        uint256 _validUntil,
        bytes32 _ap2MandateId,
        string calldata _settlementAsset
    ) external returns (bytes32 intentId) {
        if (_validUntil <= block.timestamp) revert InvalidTimestamp();

        // Generate unique intent ID from hash components
        intentId = keccak256(
            abi.encodePacked(
                _intentHash,
                msg.sender,
                block.timestamp,
                totalIntents
            )
        );

        if (intents[intentId].timestamp != 0) revert IntentAlreadyExists();

        // Store intent metadata
        intents[intentId] = IntentMetadata({
            intentHash: _intentHash,
            actor: msg.sender,
            timestamp: block.timestamp,
            validUntil: _validUntil,
            ap2MandateId: _ap2MandateId,
            settlementAsset: _settlementAsset,
            isActive: true,
            isMatched: false
        });

        // Track actor's intents
        actorIntents[msg.sender].push(intentId);
        totalIntents++;

        emit IntentRegistered(
            intentId,
            _intentHash,
            msg.sender,
            block.timestamp,
            _validUntil,
            _ap2MandateId,
            _settlementAsset
        );

        return intentId;
    }

    /**
     * @notice Cancel an active intent
     * @param _intentId ID of the intent to cancel
     */
    function cancelIntent(bytes32 _intentId) external {
        IntentMetadata storage intent = intents[_intentId];

        if (intent.timestamp == 0) revert IntentNotFound();
        if (intent.actor != msg.sender) revert UnauthorizedActor();
        if (!intent.isActive) revert IntentNotActive();

        intent.isActive = false;

        emit IntentCancelled(_intentId, msg.sender);
    }

    /**
     * @notice Mark an intent as matched (called by AuctionEscrow)
     * @param _intentId ID of the intent to mark as matched
     */
    function markAsMatched(bytes32 _intentId) external {
        IntentMetadata storage intent = intents[_intentId];

        if (intent.timestamp == 0) revert IntentNotFound();
        if (!intent.isActive) revert IntentNotActive();

        intent.isMatched = true;

        emit IntentMatched(_intentId, intent.actor);
    }

    /**
     * @notice Get intent metadata
     * @param _intentId ID of the intent
     * @return metadata Intent metadata structure
     */
    function getIntent(bytes32 _intentId)
        external
        view
        returns (IntentMetadata memory metadata)
    {
        if (intents[_intentId].timestamp == 0) revert IntentNotFound();
        return intents[_intentId];
    }

    /**
     * @notice Check if an intent is valid and active
     * @param _intentId ID of the intent
     * @return valid True if intent is active and not expired
     */
    function isIntentValid(bytes32 _intentId) external view returns (bool valid) {
        IntentMetadata storage intent = intents[_intentId];

        return
            intent.timestamp != 0 &&
            intent.isActive &&
            !intent.isMatched &&
            intent.validUntil > block.timestamp;
    }

    /**
     * @notice Get all intent IDs for an actor
     * @param _actor Address of the actor
     * @return intentIds Array of intent IDs
     */
    function getActorIntents(address _actor)
        external
        view
        returns (bytes32[] memory intentIds)
    {
        return actorIntents[_actor];
    }
}
