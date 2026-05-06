import pytest
from src.core.question_processor import QuestionProcessor
from src.core.prediction_engine import PredictionEngine
from src.core.license_oracle import LicenseOracleGate
from src.core.evidence_chain import EvidenceChain
from src.core.community_calibration import CommunityCalibrationDNA

class TestQuestionProcessor:
    def test_valid_question(self):
        qp = QuestionProcessor()
        dna = qp.process("2026年比特币会涨吗？")
        assert dna['question_id'].startswith('Q')
        assert dna['raw_text'] == '2026年比特币会涨吗'
        assert 0 <= dna['resolvability_score'] <= 1
        assert 'domain_tags' in dna

    def test_short_question_raises(self):
        qp = QuestionProcessor()
        with pytest.raises(ValueError):
            qp.process("短")

class TestPredictionEngine:
    def test_predict_basic(self):
        engine = PredictionEngine()
        dna = {
            "question_id": "Qtest",
            "raw_text": "测试问题",
            "resolvability_score": 0.8
        }
        result = engine.predict(dna)
        assert 'prediction_id' in result
        assert 0 <= result['probability'] <= 1
        assert result['agent_count'] >= 1

class TestLicenseOracle:
    def test_approve_valid_prediction(self):
        gate = LicenseOracleGate()
        pred = {
            "prediction_id": "P001",
            "probability": 0.7,
            "uncertainty": 0.3,
            "reasoning": "多智能体综合分析的结论，有证据支持。",
            "timestamp": "2026-05-07T12:00:00Z",
            "ethical_flags": []
        }
        result = gate.validate(pred)
        assert result['status'] == 'APPROVED'

    def test_reject_high_uncertainty(self):
        gate = LicenseOracleGate()
        pred = {
            "prediction_id": "P002",
            "probability": 0.5,
            "uncertainty": 0.95,  # 超过阈值 0.9
            "reasoning": "极不确定",
            "timestamp": "2026-05-07T12:00:00Z",
            "ethical_flags": []
        }
        result = gate.validate(pred)
        assert result['status'] == 'REJECTED'
        assert 'UNCERTAINTY_TOO_HIGH' in result['failure_code']

class TestEvidenceChain:
    def test_build_chain(self):
        chain = EvidenceChain()
        node = chain.add_node("测试证据", "test.com", 0.9)
        chain.add_edge(node.id, node.id, "SUPPORTS", 0.8, "自我支持测试")
        output = chain.build_chain_for_prediction("Ptest")
        assert len(output['evidence_chain']['nodes']) == 1
        assert len(output['evidence_chain']['edges']) == 1

class TestCommunityCalibration:
    def test_no_feedback_yields_no_calibration(self):
        calib = CommunityCalibrationDNA()
        pred = {
            "prediction_id": "Pno",
            "probability": 0.75,
            "domain_tags": ["科技"],
            "complexity": 0.5
        }
        report = calib.calibrate_prediction(pred)
        # 没有反馈时校准因子应为1，置信度较低
        assert report['calibration_factor'] == 1.0
        assert report['calibration_confidence'] <= 0.5