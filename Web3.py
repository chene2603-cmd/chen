# 伪代码示例
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
contract = w3.eth.contract(address=contract_address, abi=abi)
tx = contract.functions.submitPrediction(
    question_id, 
    int(probability * 1e6), 
    int(ci_lower * 1e6), 
    int(ci_upper * 1e6), 
    evidence_hash
).transact({'from': predictor_address})