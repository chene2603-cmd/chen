#!/usr/bin/env python3
"""
OpenOracle CLI - 命令行交互工具
用法: python oracle_cli.py [command] [options]
"""
import argparse
import json
import sys
import os
import requests
from typing import Optional, Dict

# 默认 API 地址
DEFAULT_API = "http://localhost:8000/api/v1"

class OracleCLI:
    def __init__(self, api_url: str = DEFAULT_API):
        self.api_url = api_url

    def predict(self, question: str) -> Dict:
        """提交预测问题"""
        response = requests.post(
            f"{self.api_url}/predict",
            json={"question": question, "source": "user_submitted"}
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict:
        """检查服务健康状态"""
        response = requests.get(f"{self.api_url.replace('/api/v1', '')}/health")
        return response.json()

    def format_prediction(self, result: Dict):
        """格式化输出预测结果"""
        if result.get("status") == "REJECTED":
            print(f"\n❌ 预测被拒绝：{result.get('message')}")
            return

        pred = result.get("prediction", {})
        prob = pred.get("calibrated_probability", pred.get("probability", 0))
        ci = pred.get("confidence_interval", [0, 0])
        uncertainty = pred.get("uncertainty", 0)

        print("\n" + "=" * 60)
        print("🔮 OpenOracle 预测结果")
        print("=" * 60)
        print(f"\n📊 预测概率:     {prob * 100:.1f}%")
        print(f"📏 置信区间:     {ci[0] * 100:.0f}% - {ci[1] * 100:.0f}%")
        print(f"❓ 不确定性:     {uncertainty * 100:.1f}%")
        print(f"\n💭 综合推理:")
        print(f"   {pred.get('reasoning', 'N/A')[:200]}...")

        if pred.get("calibration"):
            cal = pred["calibration"]
            print(f"\n👥 社区校准:")
            print(f"   校准后概率:   {cal.get('calibrated_prediction',