// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/**
 * @title PaymentRouter
 * @notice Routes and verifies AP2 payment credentials using Stripe integration
 * @dev Oracle-based verification of off-chain payment proofs with on-chain anchoring
 */
contract PaymentRouter {
    /// @notice Payment verification structure
    struct PaymentVerification {
        string stripePaymentIntentId; // Stripe payment intent ID
        uint256 amount;               // Payment amount in smallest currency unit
        address payer;                // Payer address
        address payee;                // Payee address
        uint256 timestamp;            // Verification timestamp
        bool verified;                // Verification status
        bytes32 ap2MandateId;         // AP2 mandate credential reference
    }

    /// @notice Authorized oracle addresses for payment verification
    mapping(address => bool) public authorizedOracles;

    /// @notice Mapping from payment ID to verification data
    mapping(string => PaymentVerification) public verifications;

    /// @notice Mapping from AP2 mandate ID to validity status
    mapping(bytes32 => bool) public validMandates;

    /// @notice Contract owner
    address public owner;

    /// @notice Events
    event PaymentVerified(
        string indexed stripePaymentIntentId,
        address indexed payer,
        address indexed payee,
        uint256 amount,
        bytes32 ap2MandateId
    );

    event OracleAuthorized(address indexed oracle);
    event OracleRevoked(address indexed oracle);
    event MandateRegistered(bytes32 indexed mandateId);
    event MandateRevoked(bytes32 indexed mandateId);

    /// @notice Errors
    error Unauthorized();
    error PaymentAlreadyVerified();
    error PaymentNotVerified();
    error InvalidMandate();
    error InvalidAmount();

    /// @notice Modifiers
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    modifier onlyOracle() {
        if (!authorizedOracles[msg.sender]) revert Unauthorized();
        _;
    }

    /**
     * @notice Constructor
     */
    constructor() {
        owner = msg.sender;
        authorizedOracles[msg.sender] = true;
    }

    /**
     * @notice Authorize an oracle address
     * @param _oracle Address to authorize
     */
    function authorizeOracle(address _oracle) external onlyOwner {
        authorizedOracles[_oracle] = true;
        emit OracleAuthorized(_oracle);
    }

    /**
     * @notice Revoke oracle authorization
     * @param _oracle Address to revoke
     */
    function revokeOracle(address _oracle) external onlyOwner {
        authorizedOracles[_oracle] = false;
        emit OracleRevoked(_oracle);
    }

    /**
     * @notice Register a valid AP2 mandate
     * @param _mandateId AP2 mandate credential ID
     */
    function registerMandate(bytes32 _mandateId) external onlyOwner {
        validMandates[_mandateId] = true;
        emit MandateRegistered(_mandateId);
    }

    /**
     * @notice Revoke an AP2 mandate
     * @param _mandateId AP2 mandate credential ID
     */
    function revokeMandate(bytes32 _mandateId) external onlyOwner {
        validMandates[_mandateId] = false;
        emit MandateRevoked(_mandateId);
    }

    /**
     * @notice Verify and record a Stripe payment (called by authorized oracle)
     * @param _stripePaymentIntentId Stripe payment intent ID
     * @param _amount Payment amount
     * @param _payer Payer address
     * @param _payee Payee address
     * @param _ap2MandateId AP2 mandate credential reference
     */
    function recordPaymentVerification(
        string calldata _stripePaymentIntentId,
        uint256 _amount,
        address _payer,
        address _payee,
        bytes32 _ap2MandateId
    ) external onlyOracle {
        if (verifications[_stripePaymentIntentId].timestamp != 0) {
            revert PaymentAlreadyVerified();
        }

        if (!validMandates[_ap2MandateId]) revert InvalidMandate();
        if (_amount == 0) revert InvalidAmount();

        verifications[_stripePaymentIntentId] = PaymentVerification({
            stripePaymentIntentId: _stripePaymentIntentId,
            amount: _amount,
            payer: _payer,
            payee: _payee,
            timestamp: block.timestamp,
            verified: true,
            ap2MandateId: _ap2MandateId
        });

        emit PaymentVerified(
            _stripePaymentIntentId,
            _payer,
            _payee,
            _amount,
            _ap2MandateId
        );
    }

    /**
     * @notice Verify a payment exists and matches expected amount
     * @param _stripePaymentIntentId Stripe payment intent ID
     * @param _expectedAmount Expected payment amount
     * @return verified True if payment is verified and amount matches
     */
    function verifyPayment(
        string calldata _stripePaymentIntentId,
        uint256 _expectedAmount
    ) external view returns (bool verified) {
        PaymentVerification storage verification = verifications[_stripePaymentIntentId];

        return
            verification.verified &&
            verification.amount >= _expectedAmount &&
            verification.timestamp != 0;
    }

    /**
     * @notice Get payment verification details
     * @param _stripePaymentIntentId Stripe payment intent ID
     * @return verification Payment verification structure
     */
    function getPaymentVerification(string calldata _stripePaymentIntentId)
        external
        view
        returns (PaymentVerification memory verification)
    {
        if (verifications[_stripePaymentIntentId].timestamp == 0) {
            revert PaymentNotVerified();
        }
        return verifications[_stripePaymentIntentId];
    }

    /**
     * @notice Check if a mandate is valid
     * @param _mandateId AP2 mandate credential ID
     * @return valid True if mandate is valid
     */
    function isMandateValid(bytes32 _mandateId) external view returns (bool valid) {
        return validMandates[_mandateId];
    }

    /**
     * @notice Check if an address is an authorized oracle
     * @param _oracle Address to check
     * @return authorized True if address is an authorized oracle
     */
    function isAuthorizedOracle(address _oracle) external view returns (bool authorized) {
        return authorizedOracles[_oracle];
    }

    /**
     * @notice Transfer ownership
     * @param _newOwner New owner address
     */
    function transferOwnership(address _newOwner) external onlyOwner {
        if (_newOwner == address(0)) revert Unauthorized();
        owner = _newOwner;
    }
}
