import pytest
import sys
import os

# 将项目根目录加入 sys.path，方便导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.logging_config import setup_logging

@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """测试时使用 DEBUG 日志输出到控制台"""
    setup_logging(log_level='DEBUG', log_file=None)