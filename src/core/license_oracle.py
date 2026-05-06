"""
许可证神谕：预测输出前的伦理与质量检查
所有预测必须通过此检查才能对外发布。
"""
from typing import Dict, List
from src.utils.logging_config import get_logger

logger = get_logger('openoracle.license_oracle')

class LicenseOracleGate:
    """预测许可证守门人，执行五重检查"""

    REJECTION_CODES = {
        "NO_EVIDENCE": "缺乏可验证证据",
        "ETHICAL_VIOLATION": "违反伦理准则",
        "LOGICAL_CONTRADICTION": "逻辑矛盾",
        "TEMPORAL_PARADOX": "时间悖论",
        "UNCERTAINTY_TOO_HIGH": "不确定性过高"
    }

    def __init__(self, ethical_guardrails_path: str = "config/ethical_guardrails.json"):
        self.guardrails = self._load_guardrails(ethical_guardrails_path)

    def _load_guardrails(self, path: str) -> Dict:
        """加载伦理护栏配置"""
        # 默认内置最小护栏
        defaults = {
            "prohibited_categories": [
                "personal_privacy",
                "violence_prediction",
                "market_manipulation",
                "medical_diagnosis",
                "suicide_risk"
            ],
            "max_uncertainty_threshold": 0.9,
            "min_agent_count": 1
        }
        try:
            import json
            with open(path, 'r') as f:
                config = json.load(f)
                defaults.update(config)
        except FileNotFoundError:
            logger.warning(f"伦理护栏配置文件未找到：{path}，使用内置默认值")
        return defaults

    def validate(self, prediction: Dict) -> Dict:
        """
        执行许可证检查。
        如果通过，返回 {'status': 'APPROVED', 'prediction': prediction}
        如果拒绝，返回 {'status': 'REJECTED', 'reason': ..., 'suggestion': ...}
        """
        logger.info(f"开始许可证检查", extra={'prediction_id': prediction.get('prediction_id')})

        checks = {
            "verifiable_evidence": self._has_verifiable_evidence(prediction),
            "ethical_review": self._passes_ethical_review(prediction),
            "logical_consistency": self._is_logically_consistent(prediction),
            "temporal_plausibility": self._is_temporally_plausible(prediction),
            "reasonable_confidence": self._has_reasonable_confidence(prediction),
        }

        failures = [k for k, v in checks.items() if not v]

        if not failures:
            logger.info("许可证检查通过", extra={'prediction_id': prediction.get('prediction_id')})
            return {"status": "APPROVED", "prediction": prediction}

        # 识别失败原因
        failure_code = self._identify_failure(failures)
        reason = self.REJECTION_CODES.get(failure_code, "未知拒绝原因")
        suggestion = self._generate_suggestion(failure_code, failures)

        logger.warning(f"许可证检查未通过", extra={
            'prediction_id': prediction.get('prediction_id'),
            'failure_code': failure_code,
            'reason': reason
        })

        return {
            "status": "REJECTED",
            "reason": reason,
            "failure_code": failure_code,
            "suggestion": suggestion,
            "appeal_process": "可通过社区投票上诉此决定"
        }

    # ------- 五项检查的具体实现 -------
    def _has_verifiable_evidence(self, pred: Dict) -> bool:
        # 检查预测中是否关联了证据链（至少要有证据ID或引用）
        # 这里简化：如果预测包含 reasoning 且长度 > 20 则认为有基本证据
        reasoning = pred.get('reasoning', '')
        return len(reasoning) > 20

    def _passes_ethical_review(self, pred: Dict) -> bool:
        # 检查问题中是否触发了禁止类别
        # 实际应检查 question DNA，这里从预测中查找 ethical_flags（模拟）
        ethical_flags = pred.get('ethical_flags', [])
        prohibited = self.guardrails.get('prohibited_categories', [])
        for flag in ethical_flags:
            if flag in prohibited:
                return False
        return True

    def _is_logically_consistent(self, pred: Dict) -> bool:
        # 简单逻辑检查：概率必须在 [0,1] 之间
        prob = pred.get('probability')
        if prob is not None and (prob < 0 or prob > 1):
            return False
        # 如果 uncertainty 大于 1 也视为逻辑错误
        if pred.get('uncertainty', 0) > 1:
            return False
        return True

    def _is_temporally_plausible(self, pred: Dict) -> bool:
        # 检查预测时间戳是否在未来或合理
        # 这里简化：只要时间戳格式正确即可
        import re
        ts = pred.get('timestamp', '')
        if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', ts):
            return False
        return True

    def _has_reasonable_confidence(self, pred: Dict) -> bool:
        # 不确定性不能过高（> max_uncertainty_threshold）
        max_uncertainty = self.guardrails.get('max_uncertainty_threshold', 0.9)
        uncertainty = pred.get('uncertainty', 0)
        return uncertainty <= max_uncertainty

    def _identify_failure(self, failures: List[str]) -> str:
        # 根据失败的检查项返回拒绝代码
        if "verifiable_evidence" in failures:
            return "NO_EVIDENCE"
        if "ethical_review" in failures:
            return "ETHICAL_VIOLATION"
        if "logical_consistency" in failures:
            return "LOGICAL_CONTRADICTION"
        if "temporal_plausibility" in failures:
            return "TEMPORAL_PARADOX"
        if "reasonable_confidence" in failures:
            return "UNCERTAINTY_TOO_HIGH"
        return "UNKNOWN"

    def _generate_suggestion(self, failure_code: str, failures: List[str]) -> str:
        suggestions = {
            "NO_EVIDENCE": "请为预测提供至少一个可验证的证据源或更详细的推理。",
            "ETHICAL_VIOLATION": "预测问题涉及禁止类别，请修改问题或提供合理解释。",
            "LOGICAL_CONTRADICTION": "预测存在逻辑矛盾，请检查概率值或不确定性是否在合理范围。",
            "TEMPORAL_PARADOX": "时间戳格式不正确或预测指向过去，请修正。",
            "UNCERTAINTY_TOO_HIGH": "预测不确定性过高，建议收集更多证据后重新预测。"
        }
        return suggestions.get(failure_code, "请检查预测内容并重新提交。")


if __name__ == "__main__":
    from src.utils.logging_config import setup_logging
    setup_logging(log_level='DEBUG', log_file=None)

    gate = LicenseOracleGate()

    # 测试一个正常预测
    good_pred = {
        "prediction_id": "P001",
        "probability": 0.72,
        "uncertainty": 0.2,
        "reasoning": "基于历史数据和因果链分析，概率中等偏高。",
        "timestamp": "2026-05-07T12:00:00Z",
        "ethical_flags": []
    }
    print(gate.validate(good_pred))

    # 测试一个违规预测
    bad_pred = {
        "prediction_id": "P002",
        "probability": 0.9,
        "uncertainty": 0.95,  # 太高
        "reasoning": "短",
        "timestamp": "invalid",
        "ethical_flags": ["personal_privacy"]
    }
    print(gate.validate(bad_pred))