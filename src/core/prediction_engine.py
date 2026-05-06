"""
预测推理引擎：EchoZ-1.0 风格 MAP-REDUCE 架构
"""
import hashlib
import random
from datetime import datetime
from typing import Dict, List
from src.utils.logging_config import get_logger

logger = get_logger('openoracle.prediction')

class PredictionEngine:
    """
    MAP-REDUCE 多智能体预测框架
    符合蓝图：TRAIN_ON_FUTURE，只在未来事件上训练
    """

    def __init__(self):
        self.agents = [
            EvidenceExtractorAgent(),
            HistoricalAnalogyAgent(),
            CausalChainAgent(),
            CounterfactualAgent(),
            UncertaintyQuantifierAgent()
        ]

    def predict(self, question_dna: Dict) -> Dict:
        """
        主入口：执行 MAP-REDUCE 推理
        """
        question_id = question_dna.get('question_id', 'unknown')
        logger.info(f"开始预测推理", extra={
            'question_id': question_id,
            'question_text': question_dna.get('raw_text', '')[:100]
        })

        # MAP 阶段：多智能体分解
        agent_analyses = self._map_phase(question_dna)
        logger.debug(f"MAP 阶段完成，共 {len(agent_analyses)} 个分析结果")

        # REDUCE 阶段：证据融合
        consensus = self._reduce_phase(agent_analyses)
        logger.debug(f"REDUCE 阶段完成")

        # 格式化为预测 DNA
        prediction = self._format_prediction_dna(question_dna, consensus)
        
        logger.info(f"预测生成成功", extra={
            'question_id': question_id,
            'prediction_id': prediction['prediction_id'],
            'probability': prediction['probability']
        })
        return prediction

    def _map_phase(self, question: Dict) -> List[Dict]:
        """多智能体分解问题"""
        analyses = []
        for agent in self.agents:
            try:
                analysis = agent.analyze(question)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"智能体 {agent.name} 分析失败: {str(e)}")
                analyses.append({
                    "agent": agent.name,
                    "error": str(e),
                    "probability": None
                })
        return analyses

    def _reduce_phase(self, agent_analyses: List[Dict]) -> Dict:
        """
        证据融合阶段
        简易加权平均，并计算共识度
        """
        probs = [a['probability'] for a in agent_analyses if a.get('probability') is not None]
        if not probs:
            return {
                "probability": 0.5,
                "uncertainty": 1.0,
                "agent_count": 0,
                "consensus_strength": 0.0,
                "reasoning": "所有智能体均无法给出有效概率。"
            }

        avg_prob = sum(probs) / len(probs)
        variance = sum((p - avg_prob) ** 2 for p in probs) / len(probs)
        uncertainty = min(1.0, variance * 10)  # 简单映射
        consensus_strength = 1.0 - uncertainty

        # 收集推理文本
        reasoning_parts = []
        for a in agent_analyses:
            if 'reasoning' in a:
                reasoning_parts.append(f"[{a.get('agent', 'unknown')}]: {a['reasoning']}")
        combined_reasoning = " | ".join(reasoning_parts)

        return {
            "probability": avg_prob,
            "uncertainty": uncertainty,
            "agent_count": len(probs),
            "consensus_strength": consensus_strength,
            "reasoning": combined_reasoning
        }

    def _format_prediction_dna(self, question_dna: Dict, consensus: Dict) -> Dict:
        """封装标准预测输出格式"""
        now = datetime.utcnow().isoformat() + "Z"
        prediction_id = "P" + hashlib.sha256(
            (question_dna['question_id'] + str(consensus['probability']) + now).encode()
        ).hexdigest()[:16]

        return {
            "prediction_id": prediction_id,
            "question_id": question_dna['question_id'],
            "timestamp": now,
            "probability": round(consensus['probability'], 4),
            "confidence_interval": [
                round(max(0, consensus['probability'] - consensus['uncertainty']*0.5), 4),
                round(min(1, consensus['probability'] + consensus['uncertainty']*0.5), 4)
            ],
            "uncertainty": round(consensus['uncertainty'], 4),
            "consensus_strength": round(consensus['consensus_strength'], 4),
            "agent_count": consensus['agent_count'],
            "reasoning": consensus['reasoning'],
            "method": "MAP-REDUCE-AGENT"
        }


# --------------------------------------------------
# 内置智能体（简化的模拟实现）
# --------------------------------------------------
class EvidenceExtractorAgent:
    name = "EvidenceExtractor"

    def analyze(self, question: Dict) -> Dict:
        # 模拟根据问题中的关键词给出概率
        raw = question.get('raw_text', '')
        prob = 0.5
        if "突破" in raw:
            prob = 0.65
        return {
            "agent": self.name,
            "probability": prob,
            "reasoning": "基于历史突破事件模式的相似度分析。"
        }


class HistoricalAnalogyAgent:
    name = "HistoricalAnalogy"

    def analyze(self, question: Dict) -> Dict:
        prob = 0.55
        if "价格" in question.get('raw_text', ''):
            prob = 0.7
        return {
            "agent": self.name,
            "probability": prob,
            "reasoning": "找到3个类似历史事件，平均概率0.7。"
        }


class CausalChainAgent:
    name = "CausalChain"

    def analyze(self, question: Dict) -> Dict:
        prob = random.uniform(0.4, 0.6)
        return {
            "agent": self.name,
            "probability": prob,
            "reasoning": "因果模型推演，取决于多个外部变量。"
        }


class CounterfactualAgent:
    name = "Counterfactual"

    def analyze(self, question: Dict) -> Dict:
        prob = random.uniform(0.45, 0.55)
        return {
            "agent": self.name,
            "probability": prob,
            "reasoning": "反事实分析：若无政策干预，概率会更高。"
        }


class UncertaintyQuantifierAgent:
    name = "UncertaintyQuantifier"

    def analyze(self, question: Dict) -> Dict:
        prob = 0.5
        uncertainty = 0.3
        return {
            "agent": self.name,
            "probability": prob,
            "uncertainty": uncertainty,
            "reasoning": f"综合不确定性为{uncertainty}，信息量不足。"
        }


if __name__ == "__main__":
    from src.utils.logging_config import setup_logging
    setup_logging(log_level='DEBUG', log_file=None)

    engine = PredictionEngine()
    sample_dna = {
        "question_id": "Q123abc",
        "raw_text": "2026年比特币价格会突破10万美元吗？",
        "resolvability_score": 0.8
    }
    result = engine.predict(sample_dna)
    print(result)