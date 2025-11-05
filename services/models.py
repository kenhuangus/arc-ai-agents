"""
Data models for Arc Coordination System
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    """Match status enum"""
    PENDING = "pending"
    FUNDED = "funded"
    SETTLED = "settled"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class Intent(BaseModel):
    """Intent data model"""
    intent_id: str
    intent_hash: str
    actor: str
    timestamp: int
    valid_until: int
    ap2_mandate_id: str
    settlement_asset: str
    is_active: bool = True
    is_matched: bool = False

    # Off-chain payload (not stored on-chain)
    constraints: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class Match(BaseModel):
    """Match data model"""
    match_id: str
    bid_intent_id: str
    ask_intent_id: str
    bidder: str
    asker: str
    match_price: int
    bid_amount: int = 0
    ask_amount: int = 0
    created_at: int
    settle_by: int
    status: MatchStatus = MatchStatus.PENDING
    ap2_proof_hash: Optional[str] = None
    stripe_payment_id: Optional[str] = None


class PaymentVerification(BaseModel):
    """Payment verification data model"""
    stripe_payment_intent_id: str
    amount: int
    payer: str
    payee: str
    timestamp: int
    verified: bool = False
    ap2_mandate_id: str


class AP2Mandate(BaseModel):
    """AP2 Mandate credential model"""
    mandate_id: str
    issuer: str
    subject: str
    scope: str
    valid_from: datetime
    valid_until: datetime
    is_revoked: bool = False
    metadata: dict = Field(default_factory=dict)


class IntentSubmission(BaseModel):
    """Intent submission request"""
    intent_payload: dict
    valid_until: int
    ap2_mandate_id: str
    settlement_asset: str
    constraints: dict = Field(default_factory=dict)


class MatchRequest(BaseModel):
    """Match creation request"""
    bid_intent_id: str
    ask_intent_id: str
    match_price: int
