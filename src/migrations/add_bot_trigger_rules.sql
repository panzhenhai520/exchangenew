-- BOT触发规则配置SQL
-- 为BOT合规报告添加触发规则
-- 创建日期: 2025-10-08

USE exchange_system;

-- 插入BOT_BuyFX触发规则
INSERT INTO trigger_rules (
    rule_name,
    report_type,
    rule_expression,
    description_cn,
    description_en,
    description_th,
    priority,
    allow_continue,
    warning_message_cn,
    warning_message_en,
    warning_message_th,
    is_active,
    branch_id,
    created_at
) VALUES (
    'BOT买入外币触发(>=2万美元)',
    'BOT_BuyFX',
    '{"logic":"AND","conditions":[{"field":"direction","operator":"=","value":"buy"},{"field":"verification_amount","operator":">=","value":20000}]}',
    '买入外币金额达到或超过2万美元等值时，触发BOT_BuyFX报告',
    'When buying foreign currency reaches or exceeds USD $20,000 equivalent, trigger BOT_BuyFX report',
    'เมื่อซื้อเงินตราต่างประเทศถึงหรือเกินเทียบเท่า 20,000 ดอลลาร์สหรัฐ จะทำการรายงาน BOT_BuyFX',
    50,
    TRUE,
    '该笔交易需要生成BOT买入外币报告',
    'This transaction requires BOT BuyFX report',
    'ธุรกรรมนี้ต้องส่งรายงาน BOT BuyFX',
    TRUE,
    NULL,
    NOW()
);

-- 插入BOT_SellFX触发规则
INSERT INTO trigger_rules (
    rule_name,
    report_type,
    rule_expression,
    description_cn,
    description_en,
    description_th,
    priority,
    allow_continue,
    warning_message_cn,
    warning_message_en,
    warning_message_th,
    is_active,
    branch_id,
    created_at
) VALUES (
    'BOT卖出外币触发(>=2万美元)',
    'BOT_SellFX',
    '{"logic":"AND","conditions":[{"field":"direction","operator":"=","value":"sell"},{"field":"verification_amount","operator":">=","value":20000}]}',
    '卖出外币金额达到或超过2万美元等值时，触发BOT_SellFX报告',
    'When selling foreign currency reaches or exceeds USD $20,000 equivalent, trigger BOT_SellFX report',
    'เมื่อขายเงินตราต่างประเทศถึงหรือเกินเทียบเท่า 20,000 ดอลลาร์สหรัฐ จะทำการรายงาน BOT_SellFX',
    50,
    TRUE,
    '该笔交易需要生成BOT卖出外币报告',
    'This transaction requires BOT SellFX report',
    'ธุรกรรมนี้ต้องส่งรายงาน BOT SellFX',
    TRUE,
    NULL,
    NOW()
);

-- 插入BOT_FCD触发规则
INSERT INTO trigger_rules (
    rule_name,
    report_type,
    rule_expression,
    description_cn,
    description_en,
    description_th,
    priority,
    allow_continue,
    warning_message_cn,
    warning_message_en,
    warning_message_th,
    is_active,
    branch_id,
    created_at
) VALUES (
    'BOT FCD账户触发(>=5万美元)',
    'BOT_FCD',
    '{"logic":"AND","conditions":[{"field":"use_fcd","operator":"=","value":true},{"field":"verification_amount","operator":">=","value":50000}]}',
    '使用FCD账户且金额达到或超过5万美元等值时，触发BOT_FCD报告',
    'When using FCD account and amount reaches or exceeds USD $50,000 equivalent, trigger BOT_FCD report',
    'เมื่อใช้บัญชี FCD และจำนวนเงินถึงหรือเกินเทียบเท่า 50,000 ดอลลาร์สหรัฐ จะทำการรายงาน BOT_FCD',
    50,
    TRUE,
    '该笔交易使用FCD账户且需要生成BOT FCD报告',
    'This transaction uses FCD account and requires BOT FCD report',
    'ธุรกรรมนี้ใช้บัญชี FCD และต้องส่งรายงาน BOT FCD',
    TRUE,
    NULL,
    NOW()
);

-- 插入BOT_Provider触发规则（余额调节）
INSERT INTO trigger_rules (
    rule_name,
    report_type,
    rule_expression,
    description_cn,
    description_en,
    description_th,
    priority,
    allow_continue,
    warning_message_cn,
    warning_message_en,
    warning_message_th,
    is_active,
    branch_id,
    created_at
) VALUES (
    'BOT提供商触发(余额调节>=2万美元)',
    'BOT_Provider',
    '{"logic":"AND","conditions":[{"field":"adjustment_type","operator":"=","value":"increase"},{"field":"verification_amount","operator":">=","value":20000}]}',
    '增加外币余额且金额达到或超过2万美元等值时，触发BOT_Provider报告',
    'When increasing foreign currency balance and amount reaches or exceeds USD $20,000 equivalent, trigger BOT_Provider report',
    'เมื่อเพิ่มยอดคงเหลือเงินตราต่างประเทศและจำนวนเงินถึงหรือเกินเทียบเท่า 20,000 ดอลลาร์สหรัฐ จะทำการรายงาน BOT_Provider',
    50,
    TRUE,
    '该次余额调节需要生成BOT Provider报告',
    'This balance adjustment requires BOT Provider report',
    'การปรับยอดคงเหลือนี้ต้องส่งรายงาน BOT Provider',
    TRUE,
    NULL,
    NOW()
);

-- 验证插入结果
SELECT
    id,
    rule_name,
    report_type,
    priority,
    is_active,
    created_at
FROM trigger_rules
WHERE report_type IN ('BOT_BuyFX', 'BOT_SellFX', 'BOT_FCD', 'BOT_Provider')
ORDER BY report_type, id;
