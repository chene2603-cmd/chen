"""
问题处理引擎：将自然语言问题转化为标准 DNA 格式
"""
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.utils.logging_config import get_logger

logger = get_logger('openoracle.question')

class QuestionProcessor:
    """
    动态问题池 DNA 编码器
    负责验证、清洗、结构化用户提交的问题
    """

    def __init__(self):
        self.extraction_pipelines = {
            "user_submitted": self._process_user_question,
            "trend_analysis": self._extract_from_trends,
            "expert_curated": self._validate_expert_query
        }

    def process(self, raw_question: str, source: str = "user_submitted") -> Dict:
        """
        主入口：接收原始问题，返回编码后的问题 DNA
        """
        if source not in self.extraction_pipelines:
            raise ValueError(f"未知的问题来源: {source}")

        logger.info(f"收到新问题，来源：{source}",
                    extra={'question_text': raw_question[:100]})

        # 调用对应管道
        cleaned_question = self.extraction_pipelines[source](raw_question)
        
        # 编码为标准 DNA
        dna = self.encode_question_dna(cleaned_question)
        
        logger.info(f"问题 DNA 生成成功", extra={
            'question_id': dna['question_id'],
            'resolvability_score': dna['resolvability_score']
        })
        return dna

    def _process_user_question(self, raw: str) -> str:
        """用户提交问题的预处理"""
        # 简单的清洗：去除首尾空白、特殊符号等
        cleaned = raw.strip().rstrip('?').rstrip('？')
        if len(cleaned) < 10:
            raise ValueError("问题过于简短，无法编码")
        return cleaned

    def _extract_from_trends(self, trend_text: str) -> str:
        """从趋势分析中提取问题（简化实现）"""
        return trend_text

    def _validate_expert_query(self, query: str) -> str:
        """验证专家问题（简化实现）"""
        return query

    def encode_question_dna(self, raw_question: str) -> Dict:
        """
        将问题编码为标准 DNA 格式
        返回包含所有必要元信息的字典
        """
        question_id = f"Q{hashlib.sha256(raw_question.encode()).hexdigest()[:16]}"
        now = datetime.utcnow()

        dna = {
            "question_id": question_id,
            "raw_text": raw_question,
            "resolvability_score": self._calculate_resolvability(raw_question),
            "domain_tags": self._extract_domain_tags(raw_question),
            "required_evidence": self._infer_evidence_requirements(raw_question),
            "settlement_conditions": self._extract_settlement_conditions(raw_question),
            "expiration_timestamp": self._calculate_expiry(raw_question),
            "ethical_flags": self._check_ethical_compliance(raw_question),
            "created_at": now.isoformat() + "Z",
            "source": "user"
        }
        return dna

    def _calculate_resolvability(self, question: str) -> float:
        """
        计算问题可解决性分数（0-1）
        基于关键词、长度、是否存在明确时间等简单规则
        """
        score = 0.5
        if any(word in question for word in ["将", "会", "能否", "是否", "概率"]):
            score += 0.2
        if any(word in question for word in ["202", "203", "明年", "下个月", "本周"]):
            score += 0.2
        if len(question) > 20:
            score += 0.1
        return min(score, 1.0)

    def _extract_domain_tags(self, question: str) -> List[str]:
        """简单的领域标签提取"""
        tags = []
        domain_keywords = {
            "科技": ["AI", "人工智能", "芯片", "量子", "航天", "SpaceX"],
            "经济": ["股市", "GDP", "通胀", "利率", "房地产"],
            "政治": ["选举", "大选", "总统", "法案", "外交"],
            "体育": ["世界杯", "奥运", "球队", "冠军"],
            "环境": ["气候", "碳排放", "台风", "地震"]
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in question for kw in keywords):
                tags.append(domain)
        return tags if tags else ["通用"]

    def _infer_evidence_requirements(self, question: str) -> List[str]:
        """推断需要哪些类型的证据"""
        requirements = []
        if any(word in question for word in ["价格", "股价", "GDP", "指数"]):
            requirements.append("官方统计数据")
        if any(word in question for word in ["天气", "台风", "地震"]):
            requirements.append("气象/地质观测数据")
        if any(word in question for word in ["选举", "投票"]):
            requirements.append("权威媒体结果报道")
        return requirements if requirements else ["公开可验证数据"]

    def _extract_settlement_conditions(self, question: str) -> Dict:
        """提取预测结算条件"""
        return {
            "type": "客观事实",
            "description": f"通过公开、可追溯的证据确定'{question}'的结果",
            "evidence_sources": self._infer_evidence_requirements(question)
        }

    def _calculate_expiry(self, question: str) -> str:
        """估算问题过期时间（默认30天后）"""
        expiry = datetime.utcnow() + timedelta(days=30)
        return expiry.isoformat() + "Z"

    def _check_ethical_compliance(self, question: str) -> List[str]:
        """检查伦理合规性，返回触发的标签"""
        flags = []
        prohibited = {
            "个人隐私": ["身份证", "住址", "电话", "个人行踪"],
            "暴力预测": ["战争", "恐袭", "暴力冲突"],
            "市场操纵": ["拉盘", "砸盘", "内幕"],
            "医疗诊断": ["确诊", "病症", "病人"],
            "自杀风险": ["自杀", "自残", "轻生"]
        }
        for category, keywords in prohibited.items():
            if any(kw in question for kw in keywords):
                flags.append(category)
        return flags


# 简单测试
if __name__ == "__main__":
    # 需要先初始化日志
    from src.utils.logging_config import setup_logging
    setup_logging(log_level='DEBUG', log_file=None)

    processor = QuestionProcessor()
    result = processor.process("2026年比特币价格会突破10万美元吗？")
    print(result)