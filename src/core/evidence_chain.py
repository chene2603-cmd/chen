"""
证据链 DNA：基于有向无环图 (DAG) 的证据网络
"""
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

class EvidenceNode:
    """证据图中的一个节点"""
    def __init__(self, evidence_id: str, content: str, source: str,
                 reliability_score: float, extraction_method: str = "manual"):
        self.id = evidence_id
        self.content = content
        self.source = source
        self.reliability_score = reliability_score
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.extraction_method = extraction_method

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "reliability_score": self.reliability_score,
            "timestamp": self.timestamp,
            "extraction_method": self.extraction_method
        }

class EvidenceEdge:
    """证据图中的边，表示支持或反驳关系"""
    def __init__(self, from_node: str, to_node: str, relation: str,
                 strength: float, reasoning: str):
        self.from_id = from_node
        self.to_id = to_node
        self.relation = relation  # "SUPPORTS" | "REFUTES" | "MITIGATES"
        self.strength = strength
        self.reasoning = reasoning

    def to_dict(self) -> Dict:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "relation": self.relation,
            "strength": self.strength,
            "reasoning": self.reasoning
        }

class EvidenceChain:
    """
    证据链 DNA，维护一个有向无环图（DAG）
    聚合规则默认使用贝叶斯网络简化版
    """
    def __init__(self):
        self.nodes: Dict[str, EvidenceNode] = {}
        self.edges: List[EvidenceEdge] = []

    def add_node(self, content: str, source: str,
                 reliability_score: float, extraction_method: str = "manual") -> EvidenceNode:
        evidence_id = f"E{hashlib.sha256(content.encode()).hexdigest()[:16]}"
        node = EvidenceNode(evidence_id, content, source, reliability_score, extraction_method)
        self.nodes[evidence_id] = node
        return node

    def add_edge(self, from_id: str, to_id: str, relation: str,
                 strength: float, reasoning: str):
        if from_id not in self.nodes or to_id not in self.nodes:
            raise ValueError("节点不存在")
        edge = EvidenceEdge(from_id, to_id, relation, strength, reasoning)
        self.edges.append(edge)

    def build_chain_for_prediction(self, prediction_id: str) -> Dict:
        """导出符合蓝图格式的证据链 JSON"""
        chain = {
            "prediction_id": prediction_id,
            "evidence_chain": {
                "type": "DIRECTED_ACYCLIC_GRAPH",
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "edges": [e.to_dict() for e in self.edges],
                "aggregation_rule": "BAYESIAN_NETWORK"
            }
        }
        return chain

    def calculate_influence(self, conclusion_node_id: str) -> float:
        """
        简易贝叶斯聚合：根据支持/反驳边的强度计算对结论的影响。
        这里简化：将支持边强度相加，反驳边强度相乘（取补）。
        实际系统应使用贝叶斯网络推理库。
        """
        support_sum = 0.0
        refute_product = 1.0
        for edge in self.edges:
            if edge.to_id == conclusion_node_id:
                if edge.relation == "SUPPORTS":
                    support_sum += edge.strength
                elif edge.relation == "REFUTES":
                    refute_product *= (1 - edge.strength)
        # 简单融合：支持度升高，反驳度降低
        base = 0.5
        influence = base + (1 - base) * min(support_sum, 1.0) * refute_product
        return min(1.0, max(0.0, influence))


if __name__ == "__main__":
    chain = EvidenceChain()
    node1 = chain.add_node("2026年3月SpaceX星舰IFT-5成功入轨",
                           "https://nasa.gov/spacex/ift5", 0.95)
    node_conclusion = chain.add_node("SpaceX 2026年将完成至少5次星舰发射",
                                     "综合推断", 0.7)
    chain.add_edge(node1.id, node_conclusion.id, "SUPPORTS", 0.8,
                   "历史成功率是未来表现的重要指标")
    print(chain.build_chain_for_prediction("P001"))