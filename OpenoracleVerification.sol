// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract OpenOracleVerification {
    struct PredictionRecord {
        uint256 timestamp;
        bytes32 evidenceHash;
        uint256 prediction;             // * 1e6
        uint256[2] confidenceInterval;
        bool isSettled;
        uint256 actualOutcome;
        int256 brierScore;
    }

    // questionId => predictor => record
    mapping(string => mapping(address => PredictionRecord)) public predictions;

    // 每个问题下的所有预测者
    mapping(string => address[]) private predictorsByQuestion;
    mapping(string => mapping(address => bool)) private hasPredicted;

    event PredictionSubmitted(
        string indexed questionId,
        address indexed predictor,
        uint256 prediction,
        bytes32 evidenceHash,
        uint256 timestamp
    );

    event PredictionSettled(
        string indexed questionId,
        address indexed predictor,
        uint256 actualOutcome,
        int256 brierScore
    );

    error AlreadyPredicted();
    error NotPredictor();
    error InvalidInput();
    error AlreadySettled();

    function submitPrediction(
        string memory questionId,
        uint256 prediction,
        uint256 lowerCI,
        uint256 upperCI,
        bytes32 evidenceHash
    ) external {
        if (prediction > 1_000_000 || lowerCI > upperCI || upperCI > 1_000_000) revert InvalidInput();
        if (hasPredicted[questionId][msg.sender]) revert AlreadyPredicted();

        predictions[questionId][msg.sender] = PredictionRecord({
            timestamp: block.timestamp,
            evidenceHash: evidenceHash,
            prediction: prediction,
            confidenceInterval: [lowerCI, upperCI],
            isSettled: false,
            actualOutcome: 0,
            brierScore: 0
        });

        hasPredicted[questionId][msg.sender] = true;
        predictorsByQuestion[questionId].push(msg.sender);

        emit PredictionSubmitted(questionId, msg.sender, prediction, evidenceHash, block.timestamp);
    }

    function settlePrediction(
        string memory questionId,
        address predictor,
        uint256 actualOutcome
    ) external {
        if (actualOutcome != 0 && actualOutcome != 1_000_000) revert InvalidInput();
        PredictionRecord storage record = predictions[questionId][predictor];
        if (record.timestamp == 0) revert NotPredictor();
        if (record.isSettled) revert AlreadySettled();

        record.actualOutcome = actualOutcome;
        record.isSettled = true;
        record.brierScore = _calculateBrier(record.prediction, actualOutcome);

        emit PredictionSettled(questionId, predictor, actualOutcome, record.brierScore);
    }

    function _calculateBrier(uint256 pred, uint256 actual) private pure returns (int256) {
        int256 diff = int256(pred) - int256(actual);
        return (diff * diff) / 1_000_000;
    }

    function getPredictors(string memory questionId) external view returns (address[] memory) {
        return predictorsByQuestion[questionId];
    }

    // 返回某一问题下，多个预测者的 Brier 分数
    function getBrierScores(string memory questionId, address[] memory addrs) external view returns (int256[] memory) {
        int256[] memory scores = new int256[](addrs.length);
        for (uint i = 0; i < addrs.length; i++) {
            PredictionRecord storage rec = predictions[questionId][addrs[i]];
            scores[i] = rec.isSettled ? rec.brierScore : type(int256).max; // 未结算的返回极大值
        }
        return scores;
    }
}