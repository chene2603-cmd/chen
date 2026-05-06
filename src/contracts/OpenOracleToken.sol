// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title OpenOracleToken
 * @dev 通证激励 DNA，支持多重角色和奖惩机制
 */
contract OpenOracleToken is ERC20, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant REWARDER_ROLE = keccak256("REWARDER_ROLE");

    // 用户角色枚举
    enum UserRole {
        QUESTIONER,
        VALIDATOR,
        EVIDENCE_PROVIDER,
        DEVELOPER,
        AUDITOR
    }

    // 奖励规则结构
    struct RewardRule {
        uint256 baseReward;         // 基础奖励 (最小单位)
        uint256 qualityMultiplier;  // 质量乘数 (除以 100)
        uint256 stakeRequired;      // 所需质押
        uint256 penaltyForFraud;    // 欺诈罚没
    }

    // 各角色对应的奖励规则
    mapping(UserRole => RewardRule) public rewardRules;

    // 用户贡献记录
    mapping(address => uint256) public totalEarned;
    mapping(address => uint256) public reputationScore;

    // 事件
    event RewardDistributed(address indexed user, UserRole indexed role, uint256 amount, uint256 qualityScore);
    event PenaltyApplied(address indexed user, uint256 penalty);
    event RuleUpdated(UserRole indexed role, RewardRule rule);

    constructor() ERC20("OpenOracle Token", "ORACLE") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(REWARDER_ROLE, msg.sender);

        // 初始化默认规则 (示例)
        rewardRules[UserRole.QUESTIONER] = RewardRule(100 * 1e18, 100, 0, 50 * 1e18);
        rewardRules[UserRole.VALIDATOR] = RewardRule(200 * 1e18, 100, 500 * 1e18, 100 * 1e18);
        rewardRules[UserRole.EVIDENCE_PROVIDER] = RewardRule(150 * 1e18, 100, 200 * 1e18, 80 * 1e18);
        rewardRules[UserRole.DEVELOPER] = RewardRule(300 * 1e18, 100, 0, 0);
        rewardRules[UserRole.AUDITOR] = RewardRule(250 * 1e18, 100, 300 * 1e18, 120 * 1e18);
    }

    /**
     * @dev 设置某一角色的奖励规则（仅管理员）
     */
    function setRewardRule(UserRole role, RewardRule calldata rule) external onlyRole(DEFAULT_ADMIN_ROLE) {
        rewardRules[role] = rule;
        emit RuleUpdated(role, rule);
    }

    /**
     * @dev 发放奖励（由 REWARDER_ROLE 调用）
     * @param user 接收者
     * @param role 角色
     * @param qualityScore 质量分 (0-100)
     */
    function rewardUser(address user, UserRole role, uint256 qualityScore) external onlyRole(REWARDER_ROLE) {
        require(qualityScore <= 100, "Quality score must be 0-100");
        RewardRule memory rule = rewardRules[role];
        uint256 reward = (rule.baseReward * qualityScore) / 100;

        // 铸造代币并发送
        _mint(user, reward);
        totalEarned[user] += reward;
        reputationScore[user] += qualityScore;

        emit RewardDistributed(user, role, reward, qualityScore);
    }

    /**
     * @dev 执行惩罚（罚没质押，假设质押由其他模块管理）
     * @param user 受处罚者
     * @param penalty 罚没数量
     */
    function applyPenalty(address user, uint256 penalty) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _burn(user, penalty);  // 销毁代币作为惩罚
        emit PenaltyApplied(user, penalty);
    }

    /**
     * @dev 查看用户声誉分
     */
    function getReputation(address user) external view returns (uint256) {
        return reputationScore[user];
    }
}