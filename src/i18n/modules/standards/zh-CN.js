// standards模块 - zh-CN翻译
export default {
  "standards": {
    "title": "规范管理",
    "tabs": {
      "purpose_limits": "兑换提醒",
      "receipt_files": "票据文件",
      "balance_alerts": "余额报警",
      "field_management": "字段管理",
      "trigger_rules": "触发规则配置",
      "test_trigger": "测试触发"
    },
    "purpose_limits": {
      "title": "兑换提醒信息维护",
      "add_button": "新增提醒",
      "loading": "加载中...",
      "no_data": "暂无兑换提醒信息",
      "currency_types": "种币种",
      "expand_hint": "点击展开/收起",
      "headers": {
        "sequence": "序号",
        "currency": "币种",
        "max_amount": "最大金额",
        "message": "提醒信息",
        "status": "状态",
        "actions": "操作"
      },
      "status": {
        "active": "启用",
        "inactive": "停用"
      },
      "actions": {
        "edit": "编辑",
        "delete": "删除"
      },
      "form": {
        "purpose_name": "用途名称",
        "currency_code": "币种代码",
        "max_amount": "最大金额",
        "display_message": "显示信息",
        "is_active": "是否启用",
        "purpose_name_placeholder": "请输入用途名称",
        "currency_code_placeholder": "请选择币种",
        "max_amount_placeholder": "请输入最大金额",
        "display_message_placeholder": "请输入显示信息"
      },
      "messages": {
        "save_success": "兑换提醒保存成功",
        "save_failed": "兑换提醒保存失败",
        "delete_success": "兑换提醒删除成功",
        "delete_failed": "兑换提醒删除失败",
        "confirm_delete": "确定要删除这个兑换提醒吗？",
        "fill_required_fields": "请填写所有必填字段"
      },
      "modal": {
        "title": "兑换提醒信息编辑",
        "purpose_name_label": "用途名称",
        "currency_label": "币种",
        "max_amount_label": "最大金额",
        "message_label": "显示信息",
        "active_label": "是否启用",
        "max_amount_placeholder": "请输入最大金额",
        "message_placeholder": "请输入显示信息",
        "cancel": "取消",
        "save": "保存",
        "saving": "保存中..."
      }
    },
    "receipt_files": {
      "year_label": "年份",
      "year_placeholder": "请选择年份",
      "year_suffix": "年",
      "month_label": "月份",
      "month_placeholder": "请选择月份",
      "month_suffix": "月",
      "query_button": "查询",
      "select_hint": "请选择年份和月份进行查询",
      "no_data": "该月份暂无票据文件",
      "headers": {
        "sequence": "序号",
        "filename": "文件名",
        "transaction_no": "交易号",
        "customer_name": "客户姓名",
        "amount": "金额",
        "created_time": "创建时间",
        "print_count": "打印次数",
        "actions": "操作"
      },
      "actions": {
        "preview": "预览",
        "print": "打印"
      },
      "messages": {
        "load_failed": "加载票据文件失败",
        "preview_failed": "预览文件失败",
        "print_failed": "打印文件失败"
      }
    },
    "balance_alerts": {
      "title": "网点余额报警设置",
      "add_button": "新增报警",
      "no_data": "暂无余额报警设置",
      "table": {
        "index": "序号",
        "currency": "币种",
        "min_threshold": "最小阈值",
        "max_threshold": "最大阈值",
        "status": "状态",
        "actions": "操作"
      },
      "headers": {
        "sequence": "序号",
        "currency": "币种",
        "min_threshold": "最小阈值",
        "max_threshold": "最大阈值",
        "status": "状态",
        "actions": "操作"
      },
      "status": {
        "active": "启用",
        "inactive": "停用"
      },
      "actions": {
        "edit": "编辑",
        "delete": "删除"
      },
      "form": {
        "currency_id": "币种",
        "min_threshold": "最小阈值",
        "max_threshold": "最大阈值",
        "is_active": "是否启用",
        "currency_placeholder": "请选择币种",
        "min_threshold_placeholder": "请输入最小阈值",
        "max_threshold_placeholder": "请输入最大阈值"
      },
      "messages": {
        "save_success": "余额报警保存成功",
        "save_failed": "余额报警保存失败",
        "delete_success": "余额报警删除成功",
        "delete_failed": "余额报警删除失败",
        "confirm_delete": "确定要删除这个余额报警吗？",
        "fill_required_fields": "请填写所有必填字段"
      },
      "modal": {
        "title": "余额报警编辑",
        "currency_label": "币种",
        "min_threshold_label": "最小阈值",
        "max_threshold_label": "最大阈值",
        "active_label": "是否启用",
        "cancel": "取消",
        "save": "保存",
        "saving": "保存中..."
      }
    },
    "transaction_report": {
      "title": "交易报告触发配置",
      "add_trigger": "添加触发器",
      "no_config": "暂无配置",
      "report_type": "报告类型",
      "trigger_amount": "触发金额",
      "currency": "适用币种",
      "enabled": "启用状态",
      "actions": "操作",
      "time_window": "时间窗口",
      "days": "天",
      "all_currencies": "所有币种",
      "add_config": "添加配置",
      "edit_config": "编辑配置",
      "threshold_amount": "阈值金额",
      "threshold_hint": "当交易金额达到此阈值时触发报告",
      "time_window_hint": "统计指定天数内的累计交易金额",
      "enable_trigger": "启用此触发器"
    },
    "trigger": {
      "simple_mode": "简单模式",
      "advanced_mode": "高级模式",
      "advanced_conditions": "高级条件配置",
      "all_conditions": "所有条件都满足",
      "any_condition": "任一条件满足",
      "field": "字段",
      "operator": "操作符",
      "value": "值",
      "field_amount": "交易金额",
      "field_currency": "币种代码",
      "field_country": "客户国家",
      "field_transaction_type": "交易类型",
      "field_payment_method": "付款方式",
      "field_time_window": "时间窗口(天)",
      "field_accumulated_amount": "累计金额",
      "equals": "等于",
      "not_equals": "不等于",
      "greater_equal": "大于等于",
      "less_equal": "小于等于",
      "greater": "大于",
      "less": "小于",
      "in_list": "在列表中",
      "not_in_list": "不在列表中",
      "multi_value_hint": "多个值用逗号分隔，如: USD,EUR,JPY",
      "all_countries": "所有国家",
      "thailand": "泰国",
      "china": "中国",
      "usa": "美国",
      "japan": "日本",
      "korea": "韩国",
      "buy": "买入",
      "sell": "卖出",
      "cash": "现金",
      "bank_transfer": "银行转账",
      "fcd_account": "外币账户",
      "other": "其他",
      "remove": "删除",
      "add_condition": "添加条件",
      "rule_preview": "规则预览"
    },
    "unified_report": {
      "title": "统一报告触发配置",
      "add_rule": "添加触发规则",
      "edit_rule": "编辑触发规则",
      "no_config": "暂无配置",
      "reports": "报告",
      "conditions": "个条件",
      "category": "报告类别",
      "report_type": "报告类型",
      "threshold_amount": "阈值金额",
      "currency": "适用币种",
      "priority": "优先级",
      "priority_hint": "数值越大优先级越高 (1-100)",
      "all_currencies": "所有币种",
      "enable_rule": "启用此规则",
      "anti_money_laundering": "反洗钱报告",
      "bank_of_thailand": "泰国银行报告",
      "amlo_reports": "AMLO报告类型",
      "bot_reports": "BOT报告类型",
      "cash_transaction": "现金交易报告",
      "asset_transaction": "资产交易报告",
      "suspicious_transaction": "可疑交易报告",
      "buy_foreign_currency": "买入外币",
      "sell_foreign_currency": "卖出外币",
      "foreign_currency_deposit": "外币存款",
      "balance_provider": "余额调节"
    }
  }
} 