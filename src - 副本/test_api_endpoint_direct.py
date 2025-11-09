# -*- coding: utf-8 -*-
"""
直接测试API端点，模拟HTTP请求
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from routes.app_repform import app_repform
from flask import g
import json

def test_api_endpoint():
    """测试API端点"""
    print("=" * 80)
    print("[测试] 直接调用Flask API端点")
    print("=" * 80)

    app = Flask(__name__)
    app.register_blueprint(app_repform)

    with app.test_client() as client:
        # 模拟请求数据
        request_data = {
            "report_type": "AMLO-1-01",
            "data": {
                "customer_id": "1234567890123",
                "customer_name": "Test",
                "customer_country": "TH",
                "transaction_type": "exchange",
                "transaction_amount_thb": 5844600,
                "total_amount": 5844600,
                "payment_method": "cash",
                "customer_age": None,
                "exchange_type": "normal"
            },
            "branch_id": 1
        }

        print("\n[请求数据]")
        print(json.dumps(request_data, indent=2, ensure_ascii=False))

        # 模拟认证token和用户信息
        headers = {
            'Content-Type': 'application/json'
        }

        # 因为有@token_required装饰器，我们需要模拟g.current_user
        with app.test_request_context():
            # 设置模拟用户
            g.current_user = {
                'id': 1,
                'name': 'Test User',
                'branch_id': 1,
                'role_id': 1
            }

            # 直接导入并调用函数
            from routes.app_repform import check_trigger

            # 创建mock request
            from unittest.mock import Mock
            import flask

            mock_request = Mock()
            mock_request.get_json.return_value = request_data

            # 临时替换flask.request
            original_request = flask.request
            flask.request = mock_request

            try:
                # 调用API函数
                response = check_trigger(g.current_user)

                # 解析响应
                if hasattr(response, 'get_json'):
                    result = response.get_json()
                elif isinstance(response, tuple):
                    result = response[0].get_json() if hasattr(response[0], 'get_json') else response[0]
                else:
                    result = response

                print("\n[API响应]")
                print(json.dumps(result, indent=2, ensure_ascii=False))

                print("\n[分析]")
                if result.get('success'):
                    print("✓ API调用成功")
                    if result.get('triggers', {}).get('amlo', {}).get('triggered'):
                        print("✓ AMLO已触发")
                        print(f"  report_type: {result['triggers']['amlo']['report_type']}")
                        print(f"  message_cn: {result['triggers']['amlo']['message_cn']}")
                    else:
                        print("✗ AMLO未触发 - 这是问题所在!")
                else:
                    print(f"✗ API失败: {result.get('message')}")

            except Exception as e:
                print(f"\n[错误] {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                flask.request = original_request

if __name__ == '__main__':
    test_api_endpoint()
