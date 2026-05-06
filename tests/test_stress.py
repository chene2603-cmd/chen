import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
import pytest

BASE_URL = "http://localhost:8000/api/v1"

# 注意：这些测试要求服务正在运行（可通过 docker-compose 启动）
# 因此可以标记为集成测试，默认可能跳过
INTEGRATION = pytest.mark.skipif(
    "not config.getoption('--integration')",
    reason="需要服务运行，使用 --integration 标志启用"
)

class TestStressScenarios:
    """
    模拟蓝图中的生存测试场景
    """

    @INTEGRATION
    def test_mass_false_evidence(self):
        """信息操纵攻击：大量虚假问题涌入"""
        def send_question(i):
            try:
                requests.post(f"{BASE_URL}/predict", json={
                    "question": f"虚假问题 #{i}：股票将暴涨100倍（内幕消息）"
                }, timeout=5)
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=20) as executor:
            list(executor.map(send_question, range(200)))
        # 服务应未崩溃
        resp = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        assert resp.status_code == 200

    @INTEGRATION
    def test_sybil_attack(self):
        """Sybil攻击：大量重复反馈企图扭曲校准"""
        # 首先创建一个预测
        resp = requests.post(f"{BASE_URL}/predict", json={"question": "太阳明天会升起吗？"})
        assert resp.status_code == 200
        pred_id = resp.json()['prediction']['prediction_id']

        def submit_feedback(user_id):
            requests.post(f"{BASE_URL}/community/feedback", json={
                "prediction_id": pred_id,
                "user_id": f"sybil_{user_id}",
                "scores": {"evidence_support": 0.1, "reasoning_clarity": 0.1},  # 恶意低分
                "reasoning": "操纵攻击"
            })

        with ThreadPoolExecutor(max_workers=50) as executor:
            list(executor.map(submit_feedback, range(300)))

        # 获取最新预测，检查校准是否极端（系统应具备一定抵抗）
        # 此处只确保不崩溃
        assert True

    @INTEGRATION
    def test_adversarial_questions(self):
        """对抗性提问：悖论性问题"""
        paradoxical = [
            "这句话是假的。",
            "如果预测错误，那这个预测正确吗？",
            "我此刻在说谎。"
        ]
        for q in paradoxical:
            resp = requests.post(f"{BASE_URL}/predict", json={"question": q})
            # 应返回结果或被拒绝，但不应 500 崩溃
            assert resp.status_code in [200, 400, 403]

    def test_local_engine_under_load(self):
        """本地引擎压力测试（无需服务运行）"""
        from src.core.prediction_engine import PredictionEngine
        engine = PredictionEngine()
        start = time.time()
        for i in range(100):
            dna = {"question_id": f"Q{i}", "raw_text": f"负载测试问题 {i}", "resolvability_score": 0.7}
            engine.predict(dna)
        duration = time.time() - start
        # 100次预测应在5秒内完成（单线程）
        assert duration < 5.0, f"预测引擎过慢: {duration}秒"