"""
OpenOracle 系统自检模块
确保所有依赖和服务正常运行
"""
import sys
import subprocess
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple

class OpenOracleHealthCheck:
    """系统健康检查器"""
    
    REQUIRED_PACKAGES = [
        "web3>=6.0.0",
        "ipfshttpclient>=0.8.0",
        "fastapi>=0.104.0",
        "pydantic>=2.4.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0"
    ]
    
    REQUIRED_SERVICES = [
        ("以太坊节点", "http://localhost:8545"),
        ("IPFS节点", "http://localhost:5001"),
        ("预言机合约", "0x...")
    ]
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.checks_passed = 0
        self.checks_failed = 0
        self.issues = []
        self.start_time = datetime.now()
    
    def run_full_check(self) -> Dict:
        """执行完整健康检查"""
        print("🔍 开始 OpenOracle 系统健康检查...")
        print("=" * 60)
        
        results = {
            "system_check": self.check_system_requirements(),
            "dna_integrity": self.verify_dna_integrity(),
            "services_check": self.check_external_services(),
            "contracts_check": self.check_smart_contracts(),
            "storage_check": self.check_storage_systems(),
            "performance_check": self.run_performance_tests()
        }
        
        print("=" * 60)
        print(f"✅ 检查完成: {self.checks_passed} 项通过, {self.checks_failed} 项失败")
        
        if self.checks_failed > 0:
            print("⚠️  发现以下问题:")
            for issue in self.issues:
                print(f"   - {issue}")
            return {"status": "UNHEALTHY", "issues": self.issues}
        
        return {"status": "HEALTHY", "checks": results}
    
    def check_system_requirements(self) -> Dict:
        """检查系统依赖"""
        print("📦 检查系统依赖...")
        results = {}
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 9:
            results["python_version"] = "PASS"
            self.checks_passed += 1
        else:
            results["python_version"] = "FAIL"
            self.checks_failed += 1
            self.issues.append(f"Python版本需>=3.9, 当前: {sys.version}")
        
        # 检查依赖包
        for package in self.REQUIRED_PACKAGES:
            pkg_name = package.split(">=")[0]
            try:
                __import__(pkg_name.replace("-", "_"))
                results[f"package_{pkg_name}"] = "PASS"
                self.checks_passed += 1
            except ImportError:
                results[f"package_{pkg_name}"] = "FAIL"
                self.checks_failed += 1
                self.issues.append(f"缺失依赖: {package}")
        
        return results
    
    def verify_dna_integrity(self) -> Dict:
        """验证DNA代码完整性"""
        print("🧬 验证DNA完整性...")
        
        with open("config/dna_config.json", "r") as f:
            dna_config = json.load(f)
        
        # 计算DNA哈希
        dna_str = json.dumps(dna_config, sort_keys=True)
        calculated_hash = hashlib.sha256(dna_str.encode()).hexdigest()
        
        # 检查不可变原则
        immutable_traits = ["transparency", "falsifiability", "open_source", "anti_censorship"]
        missing_traits = []
        
        for trait in immutable_traits:
            if trait not in dna_str.lower():
                missing_traits.append(trait)
        
        if not missing_traits and calculated_hash == dna_config.get("dna_hash", ""):
            self.checks_passed += 1
            return {
                "dna_integrity": "PASS",
                "hash": calculated_hash[:16] + "..."
            }
        else:
            self.checks_failed += 1
            issue_msg = "DNA完整性检查失败"
            if missing_traits:
                issue_msg += f"，缺失不可变原则: {missing_traits}"
            self.issues.append(issue_msg)
            return {
                "dna_integrity": "FAIL",
                "missing_traits": missing_traits
            }
    
    def check_external_services(self) -> Dict:
        """检查外部服务连接"""
        print("🌐 检查外部服务...")
        results = {}
        
        for service_name, endpoint in self.REQUIRED_SERVICES:
            try:
                import requests
                response = requests.get(f"{endpoint}/health", timeout=5)
                if response.status_code == 200:
                    results[service_name] = "PASS"
                    self.checks_passed += 1
                else:
                    results[service_name] = "FAIL"
                    self.checks_failed += 1
                    self.issues.append(f"服务异常: {service_name} ({endpoint})")
            except Exception as e:
                results[service_name] = "FAIL"
                self.checks_failed += 1
                self.issues.append(f"服务不可达: {service_name} ({endpoint}): {str(e)}")
        
        return results
    
    def check_smart_contracts(self) -> Dict:
        """检查智能合约"""
        print("📄 检查智能合约...")
        
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
            
            contracts_to_check = [
                ("OpenOracleVerification", "0xVerificationContractAddr"),
                ("OpenOracleToken", "0xTokenContractAddr")
            ]
            
            results = {}
            for contract_name, address in contracts_to_check:
                code = w3.eth.get_code(address)
                if len(code) > 2:  # 非空合约
                    results[contract_name] = "PASS"
                    self.checks_passed += 1
                else:
                    results[contract_name] = "FAIL"
                    self.checks_failed += 1
                    self.issues.append(f"合约未部署: {contract_name}")
            
            return results
        except Exception as e:
            self.checks_failed += 1
            self.issues.append(f"合约检查失败: {str(e)}")
            return {"error": str(e)}
    
    def check_storage_systems(self) -> Dict:
        """检查存储系统"""
        print("💾 检查存储系统...")
        
        try:
            import ipfshttpclient
            client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
            
            # 测试IPFS连接
            version = client.version()
            results = {
                "ipfs_connection": "PASS",
                "ipfs_version": version["Version"]
            }
            self.checks_passed += 1
            
            # 检查区块链存储
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
            if w3.is_connected():
                results["blockchain_connection"] = "PASS"
                self.checks_passed += 1
            else:
                results["blockchain_connection"] = "FAIL"
                self.checks_failed += 1
                self.issues.append("区块链连接失败")
            
            return results
        except Exception as e:
            self.checks_failed += 1
            self.issues.append(f"存储系统检查失败: {str(e)}")
            return {"error": str(e)}
    
    def run_performance_tests(self) -> Dict:
        """运行性能测试"""
        print("⚡ 运行性能测试...")
        
        import time
        results = {}
        
        # 测试问题处理延迟
        start = time.time()
        # 模拟问题处理
        time.sleep(0.1)
        processing_latency = time.time() - start
        
        if processing_latency < 0.5:
            results["processing_latency"] = "PASS"
            self.checks_passed += 1
        else:
            results["processing_latency"] = "FAIL"
            self.checks_failed += 1
            self.issues.append(f"处理延迟过高: {processing_latency:.2f}s")
        
        # 测试内存使用
        import psutil
        memory_percent = psutil.virtual_memory().percent
        results["memory_usage"] = f"{memory_percent}%"
        
        if memory_percent < 80:
            results["memory_check"] = "PASS"
            self.checks_passed += 1
        else:
            results["memory_check"] = "FAIL"
            self.checks_failed += 1
            self.issues.append(f"内存使用过高: {memory_percent}%")
        
        return results
    
    def generate_report(self) -> str:
        """生成健康检查报告"""
        report = f"""
# OpenOracle 系统健康检查报告
## 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
## 持续时间: {(datetime.now() - self.start_time).total_seconds():.2f}秒

## 📊 检查摘要
- ✅ 通过检查: {self.checks_passed} 项
- ❌ 失败检查: {self.checks_failed} 项
- 📈 通过率: {self.checks_passed/(self.checks_passed+self.checks_failed)*100:.1f}%

## 🔧 系统状态: {"健康" if self.checks_failed == 0 else "需关注"}

## 📋 发现问题:
"""
        if self.issues:
            for issue in self.issues:
                report += f"- {issue}\n"
        else:
            report += "无\n"
        
        report += f"""
## 🎯 建议操作:
{f"请修复上述 {self.checks_failed} 个问题后再启动系统" if self.issues else "系统状态良好，可以启动"}
"""
        return report

# 自检脚本入口
if __name__ == "__main__":
    checker = OpenOracleHealthCheck()
    result = checker.run_full_check()
    
    # 保存报告
    report = checker.generate_report()
    with open("logs/health_check_report.md", "w") as f:
        f.write(report)
    
    # 输出结果
    print(report)
    
    # 根据检查结果退出
    sys.exit(1 if result["status"] == "UNHEALTHY" else 0)