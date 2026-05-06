import pytest

# 模拟合约逻辑的 Python 版本，用于验证 Brier Score 计算等

def mock_brier_score(prediction: int, actual: int) -> int:
    """复制 Solidity 合约的 Brier 分数计算（整数版本）"""
    diff = prediction - actual
    return (diff * diff) // 1_000_000

class TestMockContracts:
    def test_brier_score_perfect(self):
        # 预测 1.0 (1_000_000) 实际 1.0 -> 分数 0
        assert mock_brier_score(1_000_000, 1_000_000) == 0
        # 预测 0.0 实际 0.0 -> 0
        assert mock_brier_score(0, 0) == 0

    def test_brier_score_worst(self):
        # 预测 1.0 实际 0.0 -> 1_000_000
        assert mock_brier_score(1_000_000, 0) == 1_000_000

    def test_brier_score_moderate(self):
        # 预测 0.7 (700_000) 实际 1.0 (1_000_000) -> (300_000^2)/1e6 = 90_000
        assert mock_brier_score(700_000, 1_000_000) == 90_000

    def test_prediction_submission_validation(self):
        # 模拟合约中的有效性检查
        def valid_probability(prob):
            return 0 <= prob <= 1_000_000

        assert valid_probability(500_000)
        assert not valid_probability(1_000_001)
        assert not valid_probability(-1)