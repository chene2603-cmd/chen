from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.question_processor import QuestionProcessor
from src.core.prediction_engine import PredictionEngine
from src.core.license_oracle import LicenseOracleGate
from src.core.evidence_chain import EvidenceChain
from src.core.community_calibration import CommunityCalibrationDNA
from src.governance.evolutionary_guardrails import EvolutionaryGuardrails, ImmutableTraitViolation
from src.governance.dao_voting import DAOVoting
from src.utils.logging_config import get_logger

logger = get_logger('openoracle.api')

router = APIRouter()

# 初始化核心组件
question_processor = QuestionProcessor()
prediction_engine = PredictionEngine()
license_oracle = LicenseOracleGate()
evidence_chain = EvidenceChain()
community_calib = CommunityCalibrationDNA()
dao = DAOVoting()
guard = EvolutionaryGuardrails(dao)


class QuestionRequest(BaseModel):
    question: str
    source: str = "user_submitted"


class PredictionResponse(BaseModel):
    status: str
    prediction: dict = None
    message: str = None


class FeedbackRequest(BaseModel):
    prediction_id: str
    user_id: str
    scores: dict
    reasoning: str
    new_evidence: list = []


class ProposalRequest(BaseModel):
    title: str
    description: str
    modifications: list
    author: str


@router.post("/predict", response_model=PredictionResponse)
async def create_prediction(request: QuestionRequest):
    """
    接收一个问题，返回经过完整管道处理后的预测。
    管道：问题处理 -> 预测引擎 -> 许可证神谕 -> 社区校准 -> 证据链构建
    """
    try:
        # 1. 问题DNA编码
        question_dna = question_processor.process(request.question, request.source)

        # 2. 预测推理
        prediction = prediction_engine.predict(question_dna)

        # 3. 许可证检查
        license_result = license_oracle.validate(prediction)

        if license_result["status"] == "REJECTED":
            logger.info("预测被许可证神谕拒绝", extra={
                "question_id": question_dna["question_id"],
                "reason": license_result["reason"]
            })
            return PredictionResponse(
                status="REJECTED",
                message=license_result["reason"],
                prediction=license_result.get("prediction")
            )

        # 4. 社区校准
        calibrated_report = community_calib.calibrate_prediction(prediction)
        prediction["calibration"] = calibrated_report
        prediction["calibrated_probability"] = calibrated_report["calibrated_prediction"]

        # 5. 构建证据链
        evidence_node = evidence_chain.add_node(
            prediction["reasoning"],
            "MAP-REDUCE综合推理",
            0.8,
            "automatic_extraction"
        )
        chain_data = evidence_chain.build_chain_for_prediction(prediction["prediction_id"])
        prediction["evidence_chain"] = chain_data["evidence_chain"]

        return PredictionResponse(
            status="APPROVED",
            prediction=prediction
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("预测处理异常")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/community/feedback")
async def receive_feedback(feedback: FeedbackRequest):
    """接收社区反馈，存入反馈池"""
    try:
        community_calib.feedback_pool.add_feedback(
            feedback.prediction_id,
            feedback.user_id,
            feedback.scores,
            feedback.reasoning,
            feedback.new_evidence
        )
        return {"status": "received", "message": "反馈已记录"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/governance/propose")
async def create_proposal(proposal: ProposalRequest):
    """创建治理提案并启动投票"""
    try:
        vote_id = guard.propose_change(proposal.dict())
        return {"status": "PROPOSED", "vote_id": vote_id}
    except ImmutableTraitViolation as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/governance/votes")
async def get_active_votes():
    """获取所有投票状态"""
    votes_summary = []
    for vid, v in dao.votes.items():
        votes_summary.append({
            "vote_id": vid,
            "title": v["title"],
            "is_finalized": v["is_finalized"],
            "deadline": v["deadline"],
            "result": v.get("result")
        })
    return votes_summary