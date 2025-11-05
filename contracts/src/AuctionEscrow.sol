// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./IntentRegistry.sol";
import "./PaymentRouter.sol";

/**
 * @title AuctionEscrow
 * @notice Handles atomic escrow for matched intents with auction-based settlement
 * @dev Supports bid/ask matching with pre-funded escrow and dispute resolution
 */
contract AuctionEscrow {
    /// @notice Reference to IntentRegistry contract
    IntentRegistry public immutable intentRegistry;

    /// @notice Reference to PaymentRouter contract
    PaymentRouter public immutable paymentRouter;

    /// @notice Match structure for auction-based settlement
    struct Match {
        bytes32 bidIntentId;         // Buy-side intent ID
        bytes32 askIntentId;         // Sell-side intent ID
        address bidder;              // Bidder address
        address asker;               // Asker address
        uint256 matchPrice;          // Agreed settlement price
        uint256 bidAmount;           // Bid amount escrowed
        uint256 askAmount;           // Ask amount escrowed
        uint256 createdAt;           // Match creation timestamp
        uint256 settleBy;            // Settlement deadline
        MatchStatus status;          // Current match status
        bytes32 ap2ProofHash;        // Hash of AP2 payment proof
    }

    /// @notice Match status enum
    enum MatchStatus {
        Pending,       // Match created, awaiting settlement
        Funded,        // Both parties funded escrow
        Settled,       // Settlement completed
        Disputed,      // Under dispute
        Cancelled      // Match cancelled
    }

    /// @notice Mapping from match ID to Match data
    mapping(bytes32 => Match) public matches;

    /// @notice Escrow balances for each match participant
    mapping(bytes32 => mapping(address => uint256)) public escrowBalances;

    /// @notice Dispute window in seconds (24 hours)
    uint256 public constant DISPUTE_WINDOW = 24 hours;

    /// @notice Settlement timeout in seconds (48 hours)
    uint256 public constant SETTLEMENT_TIMEOUT = 48 hours;

    /// @notice Events
    event MatchCreated(
        bytes32 indexed matchId,
        bytes32 indexed bidIntentId,
        bytes32 indexed askIntentId,
        address bidder,
        address asker,
        uint256 matchPrice
    );

    event EscrowFunded(
        bytes32 indexed matchId,
        address indexed party,
        uint256 amount
    );

    event MatchSettled(
        bytes32 indexed matchId,
        bytes32 ap2ProofHash
    );

    event MatchDisputed(
        bytes32 indexed matchId,
        address indexed initiator,
        string reason
    );

    event MatchCancelled(bytes32 indexed matchId);

    event FundsReleased(
        bytes32 indexed matchId,
        address indexed recipient,
        uint256 amount
    );

    /// @notice Errors
    error MatchAlreadyExists();
    error MatchNotFound();
    error InvalidIntents();
    error InsufficientEscrow();
    error UnauthorizedParty();
    error InvalidMatchStatus();
    error SettlementTimeoutNotReached();
    error DisputeWindowExpired();
    error InvalidPaymentProof();

    /**
     * @notice Constructor
     * @param _intentRegistry Address of IntentRegistry contract
     * @param _paymentRouter Address of PaymentRouter contract
     */
    constructor(address _intentRegistry, address _paymentRouter) {
        intentRegistry = IntentRegistry(_intentRegistry);
        paymentRouter = PaymentRouter(_paymentRouter);
    }

    /**
     * @notice Create a new match between bid and ask intents
     * @param _bidIntentId Buy-side intent ID
     * @param _askIntentId Sell-side intent ID
     * @param _matchPrice Agreed settlement price
     * @return matchId Unique identifier for the match
     */
    function createMatch(
        bytes32 _bidIntentId,
        bytes32 _askIntentId,
        uint256 _matchPrice
    ) external returns (bytes32 matchId) {
        // Validate intents are active
        if (!intentRegistry.isIntentValid(_bidIntentId)) revert InvalidIntents();
        if (!intentRegistry.isIntentValid(_askIntentId)) revert InvalidIntents();

        // Get intent metadata
        IntentRegistry.IntentMetadata memory bidIntent = intentRegistry.getIntent(_bidIntentId);
        IntentRegistry.IntentMetadata memory askIntent = intentRegistry.getIntent(_askIntentId);

        // Generate match ID
        matchId = keccak256(
            abi.encodePacked(
                _bidIntentId,
                _askIntentId,
                _matchPrice,
                block.timestamp
            )
        );

        if (matches[matchId].createdAt != 0) revert MatchAlreadyExists();

        // Create match
        matches[matchId] = Match({
            bidIntentId: _bidIntentId,
            askIntentId: _askIntentId,
            bidder: bidIntent.actor,
            asker: askIntent.actor,
            matchPrice: _matchPrice,
            bidAmount: 0,
            askAmount: 0,
            createdAt: block.timestamp,
            settleBy: block.timestamp + SETTLEMENT_TIMEOUT,
            status: MatchStatus.Pending,
            ap2ProofHash: bytes32(0)
        });

        // Mark intents as matched
        intentRegistry.markAsMatched(_bidIntentId);
        intentRegistry.markAsMatched(_askIntentId);

        emit MatchCreated(
            matchId,
            _bidIntentId,
            _askIntentId,
            bidIntent.actor,
            askIntent.actor,
            _matchPrice
        );

        return matchId;
    }

    /**
     * @notice Fund escrow for a match
     * @param _matchId ID of the match
     */
    function fundEscrow(bytes32 _matchId) external payable {
        Match storage matchData = matches[_matchId];

        if (matchData.createdAt == 0) revert MatchNotFound();
        if (matchData.status != MatchStatus.Pending) revert InvalidMatchStatus();

        address party = msg.sender;
        uint256 requiredAmount = matchData.matchPrice;

        if (party != matchData.bidder && party != matchData.asker) {
            revert UnauthorizedParty();
        }

        if (msg.value < requiredAmount) revert InsufficientEscrow();

        // Record escrow balance
        escrowBalances[_matchId][party] = msg.value;

        // Update match amounts
        if (party == matchData.bidder) {
            matchData.bidAmount = msg.value;
        } else {
            matchData.askAmount = msg.value;
        }

        emit EscrowFunded(_matchId, party, msg.value);

        // Check if both parties have funded
        if (matchData.bidAmount >= requiredAmount && matchData.askAmount >= requiredAmount) {
            matchData.status = MatchStatus.Funded;
        }
    }

    /**
     * @notice Settle a match with AP2 payment proof
     * @param _matchId ID of the match
     * @param _ap2ProofHash Hash of the AP2 payment proof
     * @param _stripePaymentIntentId Stripe payment intent ID for verification
     */
    function settleMatch(
        bytes32 _matchId,
        bytes32 _ap2ProofHash,
        string calldata _stripePaymentIntentId
    ) external {
        Match storage matchData = matches[_matchId];

        if (matchData.createdAt == 0) revert MatchNotFound();
        if (matchData.status != MatchStatus.Funded) revert InvalidMatchStatus();

        // Verify AP2 payment proof via PaymentRouter
        bool isValid = paymentRouter.verifyPayment(
            _stripePaymentIntentId,
            matchData.matchPrice
        );

        if (!isValid) revert InvalidPaymentProof();

        // Update match status
        matchData.status = MatchStatus.Settled;
        matchData.ap2ProofHash = _ap2ProofHash;

        // Release funds to asker (seller)
        uint256 totalFunds = matchData.bidAmount + matchData.askAmount;
        escrowBalances[_matchId][matchData.asker] = 0;
        escrowBalances[_matchId][matchData.bidder] = 0;

        (bool success, ) = payable(matchData.asker).call{value: totalFunds}("");
        require(success, "Transfer failed");

        emit MatchSettled(_matchId, _ap2ProofHash);
        emit FundsReleased(_matchId, matchData.asker, totalFunds);
    }

    /**
     * @notice Initiate a dispute for a match
     * @param _matchId ID of the match
     * @param _reason Reason for dispute
     */
    function disputeMatch(bytes32 _matchId, string calldata _reason) external {
        Match storage matchData = matches[_matchId];

        if (matchData.createdAt == 0) revert MatchNotFound();
        if (matchData.status != MatchStatus.Funded && matchData.status != MatchStatus.Settled) {
            revert InvalidMatchStatus();
        }

        if (msg.sender != matchData.bidder && msg.sender != matchData.asker) {
            revert UnauthorizedParty();
        }

        // Check dispute window
        if (block.timestamp > matchData.createdAt + DISPUTE_WINDOW) {
            revert DisputeWindowExpired();
        }

        matchData.status = MatchStatus.Disputed;

        emit MatchDisputed(_matchId, msg.sender, _reason);
    }

    /**
     * @notice Cancel a match (only if timeout reached and not settled)
     * @param _matchId ID of the match
     */
    function cancelMatch(bytes32 _matchId) external {
        Match storage matchData = matches[_matchId];

        if (matchData.createdAt == 0) revert MatchNotFound();
        if (block.timestamp < matchData.settleBy) revert SettlementTimeoutNotReached();
        if (matchData.status == MatchStatus.Settled) revert InvalidMatchStatus();

        matchData.status = MatchStatus.Cancelled;

        // Refund escrowed funds
        uint256 bidderRefund = escrowBalances[_matchId][matchData.bidder];
        uint256 askerRefund = escrowBalances[_matchId][matchData.asker];

        escrowBalances[_matchId][matchData.bidder] = 0;
        escrowBalances[_matchId][matchData.asker] = 0;

        if (bidderRefund > 0) {
            (bool success1, ) = payable(matchData.bidder).call{value: bidderRefund}("");
            require(success1, "Bidder refund failed");
            emit FundsReleased(_matchId, matchData.bidder, bidderRefund);
        }

        if (askerRefund > 0) {
            (bool success2, ) = payable(matchData.asker).call{value: askerRefund}("");
            require(success2, "Asker refund failed");
            emit FundsReleased(_matchId, matchData.asker, askerRefund);
        }

        emit MatchCancelled(_matchId);
    }

    /**
     * @notice Get match details
     * @param _matchId ID of the match
     * @return matchData Match structure
     */
    function getMatch(bytes32 _matchId) external view returns (Match memory matchData) {
        if (matches[_matchId].createdAt == 0) revert MatchNotFound();
        return matches[_matchId];
    }

    /**
     * @notice Get escrow balance for a party in a match
     * @param _matchId ID of the match
     * @param _party Address of the party
     * @return balance Escrow balance
     */
    function getEscrowBalance(bytes32 _matchId, address _party)
        external
        view
        returns (uint256 balance)
    {
        return escrowBalances[_matchId][_party];
    }
}
