// standards模块 - zh-CN翻译
export default {
  "standards": {
    "title": "规范管理",
    "tabs": {
      "purpose_limits": "兑换提醒",
      "receipt_files": "票据文件",
      "balance_alerts": "余额报警"
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
    }
  }
} 