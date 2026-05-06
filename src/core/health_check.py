"""
OpenOracle 系统健康检查模块
定期验证所有核心组件是否正常运行。
"""
import time
from src.utils.logging_config import get_logger
from src.core.question_processor import QuestionProcessor
from src.core.prediction_engine import PredictionEngine
from src.core.license_oracle import LicenseOracleGate

logger = get_logger('openoracle.health_check')

class HealthChecker:
    """系统自检，确保各个组件活跃"""

    def __init__(self):
        self.components = {
            "question_processor": QuestionProcessor(),
            "prediction_engine": PredictionEngine(),
            "license_oracle": LicenseOracleGate()
        }

    def run_all_checks(self) -> dict:
        results = {}
        for name, component in self.components.items():
            try:
                # 对每个组件执行简单的功能测试
                if name == "question_processor":
                    _ = component.process("健康检查测试问题：太阳明天会升起吗？")
                elif name == "prediction_engine":
                    test_dna = {
                        "question_id": "QHEALTH",
                        "raw_text": "健康检查",
                        "resolvability_score": 1.0
                    }
                    _ = component.predict(test_dna)
                elif name == "license_oracle":
                    test_pred = {
                        "prediction_id": "PHEALTH",
                        "probability": 0.99,
                        "uncertainty": 0.01,
                        "reasoning": "综合历史规律，极其可靠",
                        "timestamp": "2026-05-07T12:00:00Z",
                        "ethical_flags": []
                    }
                    _ = component.validate(test_pred)
                results[name] = "OK"
            except Exception as e:
                logger.error(f"组件 {name} 健康检查失败: {str(e)}")
                results[name] = f"FAIL: {str(e)}"
        return results

def periodic_health_check(interval_seconds: int = 300):
    """周期健康检查守护线程"""
    import threading
    checker = HealthChecker()

    def _run():
        while True:
            logger.info("开始定期健康检查")
            status = checker.run_all_checks()
            logger.info(f"健康检查结果: {status}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread