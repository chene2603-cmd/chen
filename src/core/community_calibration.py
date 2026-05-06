"""
社区校准回路 DNA
基于自动化评分标准搜索 + 去中心化反馈池，对原始预测进行众包校准。
"""
import hashlib
import math
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
from src.utils.logging_config import get_logger

logger = get_logger('openoracle.community_calibration')


class AutomatedRubricSearch:
    """
    根据预测的领域和复杂度，自动生成评价维度（评分标准）。
    """
    def __init__(self):
        # 基础评分维度模板
        self.base_rubrics = [
            {"name": "evidence_support", "description": "证据支撑度", "weight": 0.3},
            {"name": "reasoning_clarity", "description": "推理清晰度", "weight": 0.2},
            {"name": "source_reliability", "description": "来源可靠性", "weight": 0.2},
            {"name": "bias_awareness", "description": "偏见意识", "weight": 0.15},
            {"name": "timeliness", "description": "时效性", "weight": 0.15},
        ]
        # 领域特化调整
        self.domain_modifiers = {
            "科技": [
                {"name": "technical_feasibility", "weight": 0.15},
            ],
            "经济": [
                {"name": "macro_consistency", "weight": 0.15},
            ],
            "政治": [
                {"name": "geopolitical_context", "weight": 0.15},
            ],
        }

    def generate(self, domain_tags: List[str], complexity: float) -> List[Dict]:
        """
        生成适用于当前预测的评价维度。
        Args:
            domain_tags: 问题领域标签列表
            complexity: 复杂度分数 (0-1)
        Returns:
            评分标准列表，每个元素包含 name, description, weight
        """
        rubrics = self.base_rubrics.copy()
        # 根据领域附加特定维度
        for tag in domain_tags:
            if tag in self.domain_modifiers:
                for mod in self.domain_modifiers[tag]:
                    rubrics.append({
                        "name": mod["name"],
                        "description": f"领域特定维度: {mod['name']}",
                        "weight": mod["weight"],
                    })
        # 如果复杂度高，增加“不确定性处理”维度
        if complexity > 0.7:
            rubrics.append({
                "name": "uncertainty_handling",
                "description": "不确定性处理",
                "weight": 0.1,
            })
        # 归一化权重，使总和为1
        total_weight = sum(r["weight"] for r in rubrics)
        for r in rubrics:
            r["weight"] = round(r["weight"] / total_weight, 4)
        logger.debug(f"生成评分标准，维度数: {len(rubrics)}")
        return rubrics


class DecentralizedFeedbackPool:
    """
    模拟去中心化反馈池，收集社区成员对预测的打分和理由。
    实际生产中可接入 IPFS + 链下签名聚合。
    """
    def __init__(self):
        # 存储反馈: prediction_id -> list of feedback items
        self.feedback_db = defaultdict(list)

    def collect(self, prediction_id: str, rubrics: List[Dict]) -> List[Dict]:
        """
        从反馈池中获取对该预测的反馈（如果已有记录）。
        这里返回已存储的反馈；实际应触发社区征集。
        """
        return self.feedback_db.get(prediction_id, [])

    def add_feedback(self, prediction_id: str, user_id: str,
                     scores: Dict[str, float], reasoning: str,
                     new_evidence: Optional[List[Dict]] = None):
        """
        添加一条社区反馈。
        Args:
            prediction_id: 预测ID
            user_id: 用户标识
            scores: 各维度得分映射，如 {"evidence_support": 0.8, ...}
            reasoning: 反馈理由
            new_evidence: 用户提供的新证据列表
        """
        feedback = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "scores": scores,
            "reasoning": reasoning,
            "new_evidence": new_evidence or [],
        }
        self.feedback_db[prediction_id].append(feedback)
        logger.info(f"收到社区反馈", extra={
            "prediction_id": prediction_id,
            "user_id": user_id,
            "evidence_provided": len(new_evidence) if new_evidence else 0
        })


class CommunityCalibrationDNA:
    """
    社区校准主类：整合评分标准搜索、反馈聚合、校准因子计算。
    """

    def __init__(self):
        self.rubric_search = AutomatedRubricSearch()
        self.feedback_pool = DecentralizedFeedbackPool()

    def calibrate_prediction(self, prediction_dna: Dict) -> Dict:
        """
        执行完整的社区校准流程：
        1. 生成评价维度
        2. 收集（现有）反馈
        3. 计算校准因子与置信度
        4. 生成校准报告
        """
        pred_id = prediction_dna.get("prediction_id", "unknown")
        domain_tags = prediction_dna.get("domain_tags", [])
        complexity = prediction_dna.get("complexity", 0.5)  # 可从问题DNA获取

        # 1. 生成评分标准
        rubrics = self.rubric_search.generate(domain_tags, complexity)
        logger.debug(f"校准开始，预测ID: {pred_id}, 维度: {[r['name'] for r in rubrics]}")

        # 2. 收集反馈（目前从内存池）
        feedbacks = self.feedback_pool.collect(pred_id)

        # 3. 计算校准因子
        calibration_factor, calibration_confidence = self._compute_calibration(
            prediction_dna, feedbacks, rubrics
        )

        # 4. 提取多数意见和少数报告
        consensus_reasoning, contrarian_views = self._extract_opinions(feedbacks)

        # 5. 合并新证据
        updated_evidence = self._merge_new_evidence(feedbacks)

        calibrated_prob = round(prediction_dna.get("probability", 0.5) * calibration_factor, 4)

        # 构造校准报告
        report = {
            "original_prediction": prediction_dna.get("probability"),
            "calibrated_prediction": calibrated_prob,
            "calibration_factor": round(calibration_factor, 4),
            "calibration_confidence": round(calibration_confidence, 4),
            "majority_reasoning": consensus_reasoning,
            "minority_reports": contrarian_views,
            "updated_evidence": updated_evidence,
            "feedback_count": len(feedbacks),
            "rubrics_used": rubrics,
            "calibration_timestamp": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(f"社区校准完成", extra={
            "prediction_id": pred_id,
            "original": prediction_dna.get("probability"),
            "calibrated": calibrated_prob,
            "factor": calibration_factor,
            "feedback_count": len(feedbacks)
        })
        return report

    def _compute_calibration(self, prediction_dna: Dict,
                             feedbacks: List[Dict],
                             rubrics: List[Dict]) -> tuple:
        """
        核心校准逻辑：
        - 如果反馈数量不足，校准因子接近 1.0（不调整），置信度低。
        - 如果有足够反馈，根据加权得分计算方向性校准因子。
        Returns:
            (calibration_factor, confidence) 校准因子 (0.5~1.5) 和置信度 (0~1)
        """
        MIN_FEEDBACK = 3  # 最少反馈数
        if len(feedbacks) < MIN_FEEDBACK:
            logger.debug("反馈数量不足，返回未校准结果")
            return 1.0, 0.2  # 未校准，置信度低

        # 对每条反馈计算综合得分
        feedback_scores = []
        for fb in feedbacks:
            total_score = 0.0
            total_weight = 0.0
            for rubric in rubrics:
                dim = rubric["name"]
                if dim in fb["scores"]:
                    total_score += fb["scores"][dim] * rubric["weight"]
                    total_weight += rubric["weight"]
            if total_weight > 0:
                feedback_scores.append(total_score / total_weight)

        if not feedback_scores:
            return 1.0, 0.0

        # 平均得分（0-1），映射为校准因子：
        # 若平均得分高 (>0.7)，说明社区认为预测质量好，稍降低概率（保守化）或保持不变
        # 若平均得分低 (<0.3)，说明社区认为质量差，应大幅降低概率（向0.5回归）
        avg_score = sum(feedback_scores) / len(feedback_scores)

        # 校准因子公式：当平均得分偏离0.5时，向中性方向微调
        # 这里采用简单线性映射：因子 = 1.0 + (avg_score - 0.5) * 0.5
        # 结果范围大约在 0.75 ~ 1.25 之间，然后根据原始概率调节
        factor = 1.0 + (avg_score - 0.5) * 0.5

        # 如果原始概率极端 (>0.8 或 <0.2)，社区平均得分低会往0.5拉
        original_prob = prediction_dna.get("probability", 0.5)
        if original_prob > 0.8 and avg_score < 0.4:
            factor = 0.8  # 强制回调
        elif original_prob < 0.2 and avg_score < 0.4:
            factor = 1.2  # 调高

        # 计算置信度：基于反馈数量与反馈一致性
        # 一致性用方差倒数衡量
        variance = 0.0
        for s in feedback_scores:
            variance += (s - avg_score) ** 2
        variance /= len(feedback_scores)
        # 方差小，一致性好，置信度上升
        consistency = 1.0 / (1.0 + variance * 10)
        count_factor = min(len(feedbacks) / 10, 1.0)  # 最多到10条满分
        confidence = 0.5 * consistency + 0.5 * count_factor

        return factor, min(confidence, 1.0)

    def _extract_opinions(self, feedbacks: List[Dict]) -> tuple:
        """
        提取共识推理（多数意见）和反对意见（少数报告）。
        简化为按反馈数量划分：超过半数视为多数。
        """
        if not feedbacks:
            return "暂无社区反馈", []

        # 简单处理：收集所有 reasoning 文本，按出现频率排序
        from collections import Counter
        reasoning_texts = [fb["reasoning"] for fb in feedbacks if fb["reasoning"]]
        reasoning_counter = Counter(reasoning_texts)

        # 多数意见
        if reasoning_counter:
            consensus = reasoning_counter.most_common(1)[0][0]
        else:
            consensus = "无具体共识"

        # 少数报告：取出现次数小于等于1或非主流的
        minority = []
        for fb in feedbacks:
            if fb["reasoning"] != consensus and fb["reasoning"]:
                minority.append({
                    "user_id": fb["user_id"],
                    "reasoning": fb["reasoning"],
                    "timestamp": fb["timestamp"],
                })

        return consensus, minority

    def _merge_new_evidence(self, feedbacks: List[Dict]) -> List[Dict]:
        """
        汇总社区提供的新证据，去重并添加元数据。
        """
        evidence_list = []
        seen_hashes = set()
        for fb in feedbacks:
            for ev in fb.get("new_evidence", []):
                ev_hash = hashlib.sha256(str(ev).encode()).hexdigest()
                if ev_hash not in seen_hashes:
                    ev["submitted_by"] = fb["user_id"]
                    ev["timestamp"] = fb["timestamp"]
                    evidence_list.append(ev)
                    seen_hashes.add(ev_hash)
        return evidence_list


# 自测

if __name__ == "__main__":
    from src.utils.logging_config import setup_logging
    setup_logging(log_level="DEBUG", log_file=None)

    calib = CommunityCalibrationDNA()

    # 创建一条示例预测
    pred = {
        "prediction_id": "P123",
        "question_id": "Q001",
        "probability": 0.75,
        "domain_tags": ["科技"],
        "complexity": 0.6,
    }

    # 模拟社区添加反馈
    calib.feedback_pool.add_feedback(
        "P123", "user1",
        scores={"evidence_support": 0.9, "reasoning_clarity": 0.8},
        reasoning="证据充分，推理合理",
        new_evidence=[{"content": "新报告显示技术进步加速", "source": "news.com"}]
    )
    calib.feedback_pool.add_feedback(
        "P123", "user2",
        scores={"evidence_support": 0.4, "reasoning_clarity": 0.6},
        reasoning="依赖单一来源，有偏见风险",
    )

    # 执行校准
    report = calib.calibrate_prediction(pred)
    import json
    print(json.dumps(report, indent=2, ensure_ascii=False))