"""
ZauriScore Backend Tests
Run with: pytest backend/tests/ -v
"""
import pytest
from unittest.mock import patch, MagicMock

# ===========================================================================
# Decision Engine Tests
# ===========================================================================

def test_decision_engine_go():
    from app.services.decision_engine import DecisionEngine
    engine = DecisionEngine()
    result = engine.calculate(static_score=10, heuristic_score=15, ml_score=5)
    assert result["risk_score"] < 40
    assert result["decision"] == "GO"


def test_decision_engine_review():
    from app.services.decision_engine import DecisionEngine
    engine = DecisionEngine()
    result = engine.calculate(static_score=50, heuristic_score=45, ml_score=40)
    assert 40 <= result["risk_score"] < 70
    assert result["decision"] == "REVIEW"


def test_decision_engine_nogo():
    from app.services.decision_engine import DecisionEngine
    engine = DecisionEngine()
    result = engine.calculate(static_score=90, heuristic_score=80, ml_score=75)
    assert result["risk_score"] >= 70
    assert result["decision"] == "NO-GO"


def test_decision_engine_formula():
    from app.services.decision_engine import DecisionEngine
    engine = DecisionEngine()
    result = engine.calculate(static_score=100, heuristic_score=0, ml_score=0)
    assert result["risk_score"] == 50.0  # 0.5 * 100 + 0 + 0


def test_decision_engine_confidence_range():
    from app.services.decision_engine import DecisionEngine
    engine = DecisionEngine()
    result = engine.calculate(static_score=50, heuristic_score=50, ml_score=50)
    assert 50 <= result["confidence"] <= 100


# ===========================================================================
# Heuristics Engine Tests
# ===========================================================================

SAFE_CONTRACT = """
pragma solidity ^0.8.0;
contract Safe {
    mapping(address => uint256) public balances;
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok);
    }
}
"""

RISKY_CONTRACT = """
pragma solidity ^0.8.0;
contract Risky {
    address owner;
    function mint(address to, uint256 amount) public {
        // unrestricted mint
    }
    function kill() public {
        selfdestruct(payable(owner));
    }
    function checkOrigin() public view returns (bool) {
        return tx.origin == owner;
    }
}
"""


def test_heuristics_finds_selfdestruct():
    from app.services.heuristics_engine import HeuristicsEngine
    engine = HeuristicsEngine()
    result = engine.analyze(RISKY_CONTRACT)
    detectors = [f["detector"] for f in result["findings"]]
    assert "selfdestruct_present" in detectors


def test_heuristics_finds_mint():
    from app.services.heuristics_engine import HeuristicsEngine
    engine = HeuristicsEngine()
    result = engine.analyze(RISKY_CONTRACT)
    detectors = [f["detector"] for f in result["findings"]]
    assert "admin_can_mint" in detectors


def test_heuristics_finds_txorigin():
    from app.services.heuristics_engine import HeuristicsEngine
    engine = HeuristicsEngine()
    result = engine.analyze(RISKY_CONTRACT)
    detectors = [f["detector"] for f in result["findings"]]
    assert "tx_origin_auth" in detectors


def test_heuristics_safe_contract_low_score():
    from app.services.heuristics_engine import HeuristicsEngine
    engine = HeuristicsEngine()
    result = engine.analyze(SAFE_CONTRACT)
    assert result["score"] < 40


def test_heuristics_risky_contract_high_score():
    from app.services.heuristics_engine import HeuristicsEngine
    engine = HeuristicsEngine()
    result = engine.analyze(RISKY_CONTRACT)
    assert result["score"] >= 30


# ===========================================================================
# Rate Limiter Tests
# ===========================================================================

def test_rate_limiter_enterprise_unlimited():
    from app.services.rate_limiter import RateLimiter
    limiter = RateLimiter()
    with patch.object(limiter, "client") as mock_client:
        allowed, used, limit = limiter.check_and_consume("user-123", "enterprise")
        assert allowed is True
        assert limit == -1


def test_rate_limiter_free_blocks_at_limit():
    from app.services.rate_limiter import RateLimiter
    limiter = RateLimiter()
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value.__enter__ = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [6, True]  # 6th scan = over limit
    mock_redis.pipeline.return_value = mock_pipeline
    limiter._client = mock_redis
    allowed, used, limit = limiter.check_and_consume("user-456", "free")
    assert allowed is False
    assert limit == 5


# ===========================================================================
# Security Tests
# ===========================================================================

def test_password_hash_verify():
    from app.core.security import hash_password, verify_password
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_jwt_create_decode():
    from app.core.security import create_access_token, decode_token
    token = create_access_token("user-id-123")
    assert isinstance(token, str)
    payload = decode_token(token)
    assert payload["sub"] == "user-id-123"


def test_jwt_invalid_token_raises():
    from app.core.security import decode_token
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        decode_token("this.is.not.a.valid.token")


# ===========================================================================
# Schema Validation Tests
# ===========================================================================

def test_scan_create_valid_address():
    from app.schemas.schemas import ScanCreate
    scan = ScanCreate(address="0xdAC17F958D2ee523a2206206994597C13D831ec7", chain_id=1)
    assert scan.address == "0xdac17f958d2ee523a2206206994597c13d831ec7"


def test_scan_create_invalid_address():
    from app.schemas.schemas import ScanCreate
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ScanCreate(address="not-an-address", chain_id=1)


def test_scan_create_unsupported_chain():
    from app.schemas.schemas import ScanCreate
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ScanCreate(address="0xdAC17F958D2ee523a2206206994597C13D831ec7", chain_id=999)


def test_user_register_weak_password():
    from app.schemas.schemas import UserRegister
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UserRegister(email="test@test.com", password="short")
