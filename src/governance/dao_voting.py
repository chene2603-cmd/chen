"""
DAO 投票 DNA
去中心化治理的简易实现，支持创建投票、投票、查询结果。
实际生产环境中应接入链上治理（如 Snapshot、Aragon 或自建合约）。
"""
import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.utils.logging_config import get_logger

logger = get_logger('openoracle.governance.dao')


class DAOVoting:
    """
    简易链下 DAO 投票系统，用于原型阶段。
    """

    def __init__(self):
        # 存储所有投票
        self.votes: Dict[str, Dict] = {}

    def create_vote(
        self,
        title: str,
        description: str,
        options: List[str],
        voting_period_days: int = 7,
        required_majority: float = 0.666
    ) -> str:
        """
        创建一个新投票。
        :param title: 投票标题
        :param description: 投票描述
        :param options: 投票选项列表，如 ["APPROVE", "REJECT"]
        :param voting_period_days: 投票持续时间（天）
        :param required_majority: 通过所需的多数比例（例如 0.666 表示 2/3）
        :return: vote_id
        """
        vote_id = f"VOTE-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow()
        self.votes[vote_id] = {
            "title": title,
            "description": description,
            "options": options,
            "created_at": now.isoformat() + "Z",
            "deadline": (now + timedelta(days=voting_period_days)).isoformat() + "Z",
            "required_majority": required_majority,
            "ballots": {},          # {voter_address: option_index}
            "total_tokens_voted": 0, # 模拟代币权重
            "is_finalized": False,
            "result": None,
        }
        logger.info(f"创建新投票", extra={
            "vote_id": vote_id,
            "title": title,
            "deadline": self.votes[vote_id]["deadline"]
        })
        return vote_id

    def cast_vote(self, vote_id: str, voter: str, option: str, token_weight: float = 1.0) -> Dict:
        """
        为投票投出选票。
        """
        vote = self.votes.get(vote_id)
        if not vote:
            return {"success": False, "error": "投票ID不存在"}

        if vote["is_finalized"]:
            return {"success": False, "error": "投票已结束"}

        if datetime.utcnow() > datetime.fromisoformat(vote["deadline"].replace("Z", "+00:00")):
            return {"success": False, "error": "投票已截止"}

        if option not in vote["options"]:
            return {"success": False, "error": f"无效选项，可选: {vote['options']}"}

        vote["ballots"][voter] = {
            "option": option,
            "weight": token_weight,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        vote["total_tokens_voted"] += token_weight

        logger.info(f"投票已记录", extra={
            "vote_id": vote_id,
            "voter": voter,
            "option": option
        })
        return {"success": True, "message": "投票成功"}

    def get_vote_result(self, vote_id: str) -> Dict:
        """
        获取投票结果。如果投票期限已过，自动结算。
        """
        vote = self.votes.get(vote_id)
        if not vote:
            return {"error": "投票ID不存在"}

        # 检查是否已到截止时间
        if datetime.utcnow() > datetime.fromisoformat(vote["deadline"].replace("Z", "+00:00")) and not vote["is_finalized"]:
            self._finalize_vote(vote_id)

        # 如果尚未结束，返回当前中间结果
        if not vote["is_finalized"]:
            return self._get_intermediate_result(vote_id)

        return vote["result"]

    def _finalize_vote(self, vote_id: str):
        """内部结算投票"""
        vote = self.votes[vote_id]

        # 统计各选项权重
        option_counts = {opt: 0.0 for opt in vote["options"]}
        total_weight = 0.0
        for ballot in vote["ballots"].values():
            option = ballot["option"]
            if option in option_counts:
                option_counts[option] += ballot["weight"]
                total_weight += ballot["weight"]

        # 找出最高票选项
        if total_weight == 0:
            winner = "ABSTAIN"
            winner_ratio = 0.0
        else:
            max_opt = max(option_counts, key=option_counts.get)
            max_votes = option_counts[max_opt]
            winner_ratio = max_votes / total_weight
            winner = max_opt

        required = vote["required_majority"]
        passed = winner_ratio >= required

        result = {
            "is_finalized": True,
            "finalized_at": datetime.utcnow().isoformat() + "Z",
            "total_votes_weight": total_weight,
            "option_breakdown": option_counts,
            "winner": winner,
            "winner_ratio": round(winner_ratio, 4),
            "required_majority": required,
            "passed": passed,
        }
        vote["is_finalized"] = True
        vote["result"] = result

        logger.info(f"投票已最终结算", extra={
            "vote_id": vote_id,
            "winner": winner,
            "passed": passed
        })

    def _get_intermediate_result(self, vote_id: str) -> Dict:
        """获取投票进行中的中间结果"""
        vote = self.votes[vote_id]
        option_counts = {opt: 0.0 for opt in vote["options"]}
        total_weight = 0.0
        for ballot in vote["ballots"].values():
            option = ballot["option"]
            if option in option_counts:
                option_counts[option] += ballot["weight"]
                total_weight += ballot["weight"]

        # 当前领先者
        if total_weight == 0:
            leader = "N/A"
            leader_ratio = 0.0
        else:
            max_opt = max(option_counts, key=option_counts.get)
            leader = max_opt
            leader_ratio = option_counts[max_opt] / total_weight

        return {
            "is_finalized": False,
            "total_votes_weight": total_weight,
            "option_breakdown": option_counts,
            "current_leader": leader,
            "leader_ratio": round(leader_ratio, 4),
            "deadline": vote["deadline"],
        }


# 自测
if __name__ == "__main__":
    from src.utils.logging_config import setup_logging
    setup_logging(log_level="DEBUG", log_file=None)

    dao = DAOVoting()

    # 创建一个测试投票
    vid = dao.create_vote(
        title="调整预测引擎参数",
        description="是否将 MAP 阶段的智能体数量从5增加到7？",
        options=["APPROVE", "REJECT"],
        voting_period_days=7,
        required_majority=0.6
    )

    # 模拟投票
    dao.cast_vote(vid, "alice", "APPROVE", 1.0)
    dao.cast_vote(vid, "bob", "REJECT", 1.0)
    dao.cast_vote(vid, "charlie", "APPROVE", 2.0)

    # 查询中间结果
    mid = dao.get_vote_result(vid)
    print("中间结果:", json.dumps(mid, indent=2))

    # 强制到期结算（手动调整时间或直接调用内部方法）
    # 这里演示手动结算前先修改 deadline（为测试方便）
    dao.votes[vid]["deadline"] = (datetime.utcnow() - timedelta(minutes=1)).isoformat() + "Z"
    final = dao.get_vote_result(vid)
    print("最终结果:", json.dumps(final, indent=2))