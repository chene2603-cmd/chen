#!/usr/bin/env python3
"""
OpenOracle 交互式终端工具
提供更友好的对话式操作
"""
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import requests

API_BASE = "http://localhost:8000/api/v1"

def main():
    commands = WordCompleter(['predict', 'feedback', 'propose', 'votes', 'help', 'exit'])
    print("欢迎使用 OpenOracle 交互终端。输入 'help' 查看命令。")
    
    while True:
        try:
            user_input = prompt('oracle> ', completer=commands).strip()
            if not user_input:
                continue
                
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            
            if cmd == 'exit':
                print("再见！")
                break
            elif cmd == 'help':
                print("\n可用命令:")
                print("  predict <问题>       - 提交预测问题")
                print("  feedback             - 交互式提交反馈")
                print("  propose              - 创建治理提案")
                print("  votes                - 查看投票列表")
                print("  exit                 - 退出\n")
            elif cmd == 'predict':
                question = parts[1] if len(parts) > 1 else prompt("问题: ")
                resp = requests.post(f"{API_BASE}/predict", json={"question": question})
                print(format_response(resp))
            elif cmd == 'votes':
                resp = requests.get(f"{API_BASE}/governance/votes")
                print(format_response(resp))
            elif cmd == 'feedback':
                pred_id = prompt("预测ID: ")
                user = prompt("你的昵称: ")
                reasoning = prompt("理由: ")
                scores = {
                    "evidence_support": float(prompt("证据支撑度 (0-1): ") or 0.5),
                    "reasoning_clarity": float(prompt("推理清晰度 (0-1): ") or 0.5)
                }
                resp = requests.post(f"{API_BASE}/community/feedback", json={
                    "prediction_id": pred_id,
                    "user_id": user,
                    "scores": scores,
                    "reasoning": reasoning
                })
                print(format_response(resp))
            elif cmd == 'propose':
                title = prompt("标题: ")
                desc = prompt("描述: ")
                mods = prompt("影响的模块 (逗号分隔): ").split(',')
                resp = requests.post(f"{API_BASE}/governance/propose", json={
                    "title": title,
                    "description": desc,
                    "modifications": [m.strip() for m in mods],
                    "author": "interactive_user"
                })
                print(format_response(resp))
            else:
                print("未知命令，输入 help 查看帮助")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

def format_response(resp):
    if resp.status_code == 200:
        import json
        return json.dumps(resp.json(), indent=2, ensure_ascii=False)
    else:
        return f"错误 {resp.status_code}: {resp.text}"

if __name__ == "__main__":
    main()