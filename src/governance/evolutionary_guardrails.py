"""
进化护栏 DNA
防止系统退化的保护机制：确保透明性、可证伪性、开源、反审查等不可变原则。
所有系统级变更必须通过此模块的社区投票流程。
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.utils.logging_config import get_logger
from src.governance.dao_voting import DAOVoting

logger = get_logger('openoracle.governance.evo_guard')


class ImmutableTraitViolation(Exception):
    """试图修改不可变原则时抛出"""
    pass


class EvolutionaryGuardrails:
    """
    进化护栏：维护系统的不可变核心，并为其他变更启动治理投票。
    """

    def __init__(self, dao_voting: Optional[DAOVoting] = None):
        # 这些原则永远不允许被修改或删除
        self.immutable_traits = [
            "transparency",      # 透明性
            "falsifiability",    # 可证伪性
            "open_source",       # 开源
            "anti_censorship"    # 反选择性（不隐藏失败预测）
        ]

        # 计算当前不可变原则的哈希，用于快速校验
        self.immutable_hash = self._compute_immutable_hash()

        # 治理投票模块（可以外部注入，也可内部实例化）
        self.dao = dao_voting or DAOVoting()

        # 存储已批准的变更历史
        self.approved_changes: List[Dict] = []

    def _compute_immutable_hash(self) -> str:
        """计算不可变原则的 SHA-256 哈希"""
        raw = "".join(sorted(self.immutable_traits)).encode('utf-8')
        return hashlib.sha256(raw).hexdigest()

    def propose_change(self, change_proposal: Dict) -> str:
        """
        提交一个系统变更提案。
        change_proposal 格式:
        {
            "title": str,
            "description": str,
            "author": str,
            "modifications": List[str],  # 受影响的模块/原则
            "patch": dict  # 具体的变更内容
        }

        返回: vote_id (提案投票ID)
        """
        # 1. 检查是否试图修改不可变原则
        modifications = change_proposal.get("modifications", [])
        for trait in self.immutable_traits:
            if trait in modifications:
                raise ImmutableTraitViolation(
                    f"原则 '{trait}' 是不可变的，任何人无权修改。"
                )

        # 2. 生成提案ID
        proposal_id = "PROP" + hashlib.sha256(
            (change_proposal["title"] + change_proposal["author"] + str(datetime.utcnow().timestamp())).encode()
        ).hexdigest()[:16]

        # 3. 启动 DAO 投票
        voting_period_days = 7
        vote_id = self.dao.create_vote(
            title=change_proposal["title"],
            description=change_proposal["description"],
            options=["APPROVE", "REJECT"],
            voting_period_days=voting_period_days,
            required_majority=0.666  # 需要2/3多数通过
        )

        logger.info(f"变更提案已发起投票", extra={
            "proposal_id": proposal_id,
            "vote_id": vote_id,
            "title": change_proposal["title"]
        })

        # 4. 记录提案与投票ID的关联 (可在链上或本地记录)
        # 这里简化，返回投票ID，调用者可通过DAO查询结果
        return vote_id

    def check_and_apply(self, vote_id: str, change_proposal: Dict) -> Dict:
        """
        检查投票结果，如果通过则应用变更（模拟）。
        返回应用结果。
        """
        result = self.dao.get_vote_result(vote_id)
        if not result["is_finalized"]:
            return {
                "status": "PENDING",
                "message": "投票尚未结束，请等待。"
            }

        if result["passed"]:
            self.approved_changes.append({
                "proposal": change_proposal,
                "vote_id": vote_id,
                "applied_at": datetime.utcnow().isoformat() + "Z",
                "result": result
            })
            logger.info(f"变更已通过并应用", extra={"vote_id": vote_id})
            return {
                "status": "APPLIED",
                "message": f"提案 '{change_proposal['title']}' 已通过并应用。"
            }
        else:
            logger.info(f"变更被社区拒绝", extra={"vote_id": vote_id})
            return {
                "status": "REJECTED",
                "message": f"提案 '{change_proposal['title']}' 被社区拒绝。"
            }

    def get_immutable_traits(self) -> List[str]:
        """返回当前不可变原则列表"""
        return self.immutable_traits.copy()

    def verify_system_integrity(self, current_principles: List[str]) -> bool:
        """
        外部调用：验证系统当前启用的原则是否包含所有不可变原则。
        """
        for trait in self.immutable_traits:
            if trait not in current_principles:
                logger.error(f"系统完整性检查失败: 缺少不可变原则 '{trait}'")
                return False
        # 哈希一致性检查
        current_hash = hashlib.sha256("".join(sorted(current_principles)).encode()).hexdigest()
        if current_hash != self.immutable_hash:
            logger.error("不可变原则哈希不匹配，系统可能已被篡改。")
            return False
        return True


# 自测
if __name__ == "__main__":
    from src.utils.logging_config import setup_logging
    setup_logging(log_level="DEBUG", log_file=None)

    guard = EvolutionaryGuardrails()

    # 测试1：尝试修改不可变原则（应抛出异常）
    try:
        guard.propose_change({
            "title": "移除透明性原则",
            "description": "我觉得透明性不重要",
            "author": "bad_actor",
            "modifications": ["transparency"]
        })
    except ImmutableTraitViolation as e:
        print(f"正确阻止: {e}")

    # 测试2：正常提案（不会触发异常）
    vote_id = guard.propose_change({
        "title": "增加新的预测智能体",
        "description": "添加一个基于NLP的新智能体",
        "author": "core_dev",
        "modifications": ["prediction_engine"]
    })
    print(f"提案投票ID: {vote_id}")

    # 测试3：检查系统完整性
    valid = guard.verify_system_integrity(
        ["transparency", "falsifiability", "open_source", "anti_censorship"]
    )
    print(f"系统完整性: {valid}")