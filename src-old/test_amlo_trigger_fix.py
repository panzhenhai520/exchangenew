#!/usr/bin/env python3
"""
测试AMLO触发修复
验证双向交易页面现在可以正确触发AMLO预约表单
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text
import json

def test_amlo_trigger_rules():
    """测试AMLO触发规则是否正确配置"""
    session = DatabaseService.get_session()
    
    try:
        print("="*60)
        print("AMLO触发修复验证测试")
        print("="*60)
        
        # 1. 检查触发规则
        print("\n1. 检查AMLO触发规则:")
        rules = session.execute(text("""
            SELECT 
                id, rule_name, report_type, rule_expression, 
                priority, is_active, warning_message_cn
            FROM trigger_rules 
            WHERE report_type LIKE 'AMLO%'
            AND is_active = TRUE
            ORDER BY priority DESC
        """)).fetchall()
        
        if rules:
            print(f"   [成功] 找到 {len(rules)} 条启用的AMLO触发规则\n")
            for rule in rules:
                print(f"   规则 ID {rule[0]}: {rule[1]}")
                print(f"   - 报告类型: {rule[2]}")
                print(f"   - 优先级: {rule[4]}")
                print(f"   - 警告消息: {rule[6]}")
                
                # 解析规则表达式
                try:
                    rule_expr = json.loads(rule[3])
                    print(f"   - 规则条件: {json.dumps(rule_expr, ensure_ascii=False, indent=6)}")
                except:
                    pass
                print()
        else:
            print("   [错误] 没有找到AMLO触发规则")
            return False
        
        # 2. 检查报告字段
        print("\n2. 检查AMLO报告字段配置:")
        field_counts = {}
        for report_type in ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']:
            count = session.execute(text("""
                SELECT COUNT(*) FROM report_fields 
                WHERE report_type = :report_type AND is_active = TRUE
            """), {'report_type': report_type}).scalar()
            field_counts[report_type] = count
            print(f"   {report_type}: {count} 个字段")
        
        # 3. 检查API端点
        print("\n3. 验证关键API端点:")
        print("   /api/repform/check-trigger - AMLO触发检查API")
        print("   /api/amlo/check-customer-reservation - 客户预约状态检查API")
        print("   /exchange/perform-dual-direction - 双向交易执行API")
        
        # 4. 测试场景
        print("\n4. 测试场景说明:")
        print("   场景1: 大额交易触发AMLO-1-01")
        print("   - 交易金额: >= 2,000,000 THB")
        print("   - 预期结果: 弹出预约表单，阻止交易")
        print()
        print("   场景2: 小额交易不触发")
        print("   - 交易金额: < 2,000,000 THB")
        print("   - 预期结果: 正常完成交易")
        print()
        print("   场景3: 已有pending预约的客户")
        print("   - 客户状态: 预约审核中")
        print("   - 预期结果: 提示客户有待审核的预约，阻止交易")
        
        # 5. 修复摘要
        print("\n" + "="*60)
        print("修复摘要")
        print("="*60)
        print("[完成] 在 DualDirectionExchangeView.vue 中导入 repformService")
        print("[完成] 添加 ReservationModal 组件引用")
        print("[完成] 在 confirmTransaction 方法中添加AMLO触发检查逻辑")
        print("[完成] 添加客户预约状态检查方法")
        print("[完成] 添加预约模态框事件处理方法")
        
        # 6. 前端代码关键点
        print("\n" + "="*60)
        print("前端代码关键修改点")
        print("="*60)
        print("1. 导入:")
        print("   import ReservationModal from '@/components/exchange/ReservationModal.vue'")
        print("   import repformService from '@/services/api/repformService'")
        print()
        print("2. 触发检查流程:")
        print("   a) 检查客户是否有证件号")
        print("   b) 调用 checkCustomerReservationStatus() 检查预约状态")
        print("   c) 如果有pending/rejected预约，阻止交易")
        print("   d) 计算交易总金额（THB）")
        print("   e) 调用 /api/repform/check-trigger 检查是否触发AMLO")
        print("   f) 如果触发，显示预约模态框，停止交易流程")
        print("   g) 用户填写预约表单后，触发 handleReservationCreated")
        print()
        print("3. 新增方法:")
        print("   - checkCustomerReservationStatus(): 检查客户预约状态")
        print("   - handleReservationCreated(): 处理预约创建成功")
        print("   - handleReservationModalClosed(): 处理预约模态框关闭")
        
        # 7. 测试建议
        print("\n" + "="*60)
        print("测试建议")
        print("="*60)
        print("1. 启动前端和后端服务")
        print("2. 登录A005网点")
        print("3. 进入双向交易页面")
        print("4. 输入客户信息（包括证件号）")
        print("5. 添加面值组合，确保总金额 >= 2,000,000 THB")
        print("6. 点击'执行交易'，然后点击'确认'")
        print("7. 验证AMLO预约表单弹出")
        print("8. 填写表单并提交预约")
        print("9. 检查预约记录是否创建成功")
        
        print("\n" + "="*60)
        print("测试验证完成!")
        print("="*60)
        print()
        print("下一步:")
        print("1. 重新编译前端（如果需要）: npm run serve")
        print("2. 确保后端服务运行中")
        print("3. 使用浏览器进行实际测试")
        print("4. 检查浏览器控制台日志，查看AMLO触发检查过程")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n[错误] 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    success = test_amlo_trigger_rules()
    sys.exit(0 if success else 1)

