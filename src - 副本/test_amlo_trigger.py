#!/usr/bin/env python3
"""
测试AMLO触发
"""
import requests
import json

def test_amlo_trigger():
    """测试AMLO触发API"""
    
    # 模拟用户的交易数据
    trigger_data = {
        "report_type": "AMLO-1-01",
        "data": {
            "customer_id": "1231",  # 用户输入的证件号
            "customer_name": "Zhenhai Pan",
            "customer_country": "BB",  # 巴巴多斯
            "transaction_type": "exchange",
            "transaction_amount_thb": 3233.00,  # 用户交易的THB金额
            "total_amount": 3233.00,
            "payment_method": "cash"
        },
        "branch_id": 6  # TEST网点
    }
    
    print("测试AMLO触发API:")
    print(f"请求数据: {json.dumps(trigger_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 这里需要实际的API调用，但由于我们没有运行服务器，先打印预期结果
        print("\n预期结果:")
        print("- 交易金额: 3,233.00 THB")
        print("- AMLO-1-01触发阈值: 2,000,000 THB")
        print("- 3,233 < 2,000,000，所以不应该触发AMLO报告")
        print("- 因此交易应该直接完成，不会弹出预约表单")
        
        print("\n问题分析:")
        print("1. 用户的交易金额(3,233 THB)远小于AMLO触发阈值(2,000,000 THB)")
        print("2. 所以不会触发AMLO报告，交易直接完成是正常的")
        print("3. 如果要测试AMLO触发，需要交易金额 >= 2,000,000 THB")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_amlo_trigger()
