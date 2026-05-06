from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.question_processor import QuestionProcessor
from src.core.prediction_engine import PredictionEngine
from src.core.license_oracle import LicenseOracleGate
from src.core.evidence_chain import EvidenceChain
from src.utils.logging_config import get_logger

logger = get_logger('openoracle.api')

router = APIRouter()

# 初始化核心组件（生产环境应使用依赖注入或单例管理）
question_processor = QuestionProcessor()
prediction_engine = PredictionEngine()
license_oracle = LicenseOracleGate()
evidence_chain = EvidenceChain()  # 简单全局实例，实际应按会话管理

class QuestionRequest(BaseModel):
    question: str
    source: str = "user_submitted"

class PredictionResponse(BaseModel):
    status: str
    prediction: dict = None
    message: str = None

@router.post("/predict", response_model=PredictionResponse)
async def create_prediction(request: QuestionRequest):
    """
    接收一个问题，返回经过完整管道处理后的预测。
    管道：问题处理 -> 预测引擎 -> 许可证神谕 -> 证据链构建
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
        
        # 4. 构建证据链（简单示例：将推理文本作为证据节点加入）
        # 在实际系统中，证据链应该从预测引擎各智能体的证据中提取。
        evidence_node = evidence_chain.add_node(
            prediction["reasoning"],
            "MAP-REDUCE综合推理",
            0.8,
            "automatic_extraction"
        )
        # 可以添加更多证据节点...
        chain_data = evidence_chain.build_chain_for_prediction(prediction["prediction_id"])
        
        # 将证据链信息附加到预测中
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