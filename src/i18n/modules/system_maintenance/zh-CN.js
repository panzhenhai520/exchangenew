export default {
  // 系统维护页面
  system_maintenance: {
    title: '系统维护',
    subtitle: '管理系统配置和基础数据',
    
    // 用户管理
    user_management: {
      title: '用户管理',
      subtitle: '管理系统用户、角色和权限',
      user_list: '用户列表',
      add_user: '添加用户',
      edit_user: '编辑用户',
      user_info: '用户信息',
      login_code: '登录代码',
      name: '姓名',
      role: '角色',
      role_names: {
        '系统管理员': '系统管理员',
        '网点管理员': '网点管理员',
        '分行管理员': '分行管理员',
        '窗口操作员': '窗口操作员',
        'TEST Role': '测试角色',
        'unassigned': '未分配'
      },
      branch: '所属网点',
      status: '状态',
      password: '密码',
      id_card_number: '身份证号',
      phone_number: '联系电话',
      mobile_number: '手机号码',
      address: '地址',
      email: '邮箱',
      status_options: {
        active: '激活',
        inactive: '未激活',
        locked: '已锁定',
        suspended: '暂停'
      },
      actions: {
        edit: '编辑',
        reset_password: '重置密码',
        disable: '停用',
        enable: '启用',
        delete: '删除该用户',
        view_permissions: '查看权限',
        hide_permissions: '隐藏权限'
      },
      permission_restrictions: {
        app_role_no_edit: 'App角色用户不允许编辑',
        app_role_no_reset_password: 'App角色用户不允许重置密码',
        app_role_no_status_change: 'App角色用户不允许修改状态',
        app_role_no_delete: 'App角色用户不允许删除'
      },
      form: {
        login_code_required: '请填写用户名',
        name_required: '请填写姓名',
        role_required: '请选择用户角色',
        branch_required: '请选择所属网点',
        password_required: '请设置初始密码',
        password_min_length: '密码长度至少6位',
        email_invalid: '邮箱格式不正确',
        phone_invalid: '联系电话格式不正确',
        mobile_invalid: '手机号码格式不正确',
        id_card_invalid: '身份证号码格式不正确'
      },
      messages: {
        create_success: '用户创建成功',
        update_success: '用户更新成功',
        delete_success: '用户删除成功',
        reset_password_success: '密码重置成功',
        operation_failed: '操作失败',
        business_check_failed: '检查用户业务失败'
      },
      no_permissions: '该用户暂无权限',
      personal_info: '个人信息',
      no_personal_info: '暂无个人信息',
      never_login: '从未登录',
      no_users_found: '没有找到用户',
      permissions: '权限',
      account_status: '账户状态',
      initial_password: '初始密码',
      optional: '可选',
      current_branch: '当前网点',
      can_only_create_for_current_branch: '您只能为当前网点创建用户',
      confirm_delete: '确认删除',
      confirm_delete_message: '您确定要删除用户 {user} 吗？此操作不可撤销。',
      delete_check_title: '删除前检查',
      delete_check_description: '系统将检查该用户是否有兑换业务、冲正业务、余额调节业务或余额初始化业务。如有业务流水，将不允许删除，建议停用用户。',
      reset_password: '重置密码',
      confirm_reset_password: '确认重置密码',
      reset_password_for_user: '您正在为用户 {name} ({code}) 重置密码。',
      password_will_be_reset_to: '密码将被重置为',
      recommend_change_password: '建议用户首次登录后立即修改密码',
      confirm_reset: '确认重置',
      status_update_success: '用户状态更新成功',
      status_update_failed: '状态更新失败',
      password_reset_success: '用户 {name} 的密码已重置为 123456',
      placeholder: {
        login_code: '请输入用户名',
        name: '请输入真实姓名',
        select_role: '请选择角色',
        select_branch: '请选择网点',
        set_initial_password: '请设置初始密码',
        id_card_number: '请输入身份证号码',
        email: '请输入邮箱地址',
        phone_number: '请输入联系电话',
        mobile_number: '请输入手机号码',
        address: '请输入联系地址'
      },
      validation: {
        fill_username_and_name: '请填写用户名和姓名',
        select_role: '请选择用户角色',
        select_branch: '请选择所属网点',
        branch_info_error: '网点信息异常，请刷新页面重试',
        set_initial_password: '请设置初始密码',
        password_min_length: '密码长度至少6位'
      }
    },
    
    // 网点管理
    branch_management: {
      title: '网点管理',
      subtitle: '管理系统网点和分支机构',
      branch_list: '网点列表',
      branch_info: '网点信息管理',
      current_branch: '当前网点',
      add_branch: '新增网点',
      edit_branch: '编辑网点',
      branch_code: '网点代码',
      branch_name: '网点名称',
      address: '地址',
      manager_name: '负责人',
      phone_number: '联系电话',
      base_currency: '本币',
      is_active: '是否激活',
      status: {
        active: '活动',
        inactive: '停用'
      },
      actions: {
        edit: '编辑',
        delete: '删除',
        view: '查看'
      },
      form: {
        branch_code_required: '请输入网点代码',
        branch_name_required: '请输入网点名称',
        address_required: '请输入地址',
        manager_required: '请输入负责人姓名',
        phone_required: '请输入联系电话',
        base_currency_required: '请选择本币'
      },
      messages: {
        save_success: '网点保存成功',
        save_failed: '网点保存失败',
        delete_success: '网点删除成功',
        delete_failed: '网点删除失败',
        code_exists: '网点代码已存在',
        invalid_code: '网点代码格式不正确'
      }
    },
    
    // 角色管理
    role_management: {
      title: '角色权限管理',
      subtitle: '管理系统角色和权限分配',
      role_list: '角色列表',
      add_role: '添加角色',
      edit_role: '编辑角色',
      role_name: '角色名称',
      description: '描述',
      permissions: '权限',
      permission_count: '权限数量',
      permission_preview: '权限预览',
      protected_role: '受保护',
      system_admin: '系统管理员',
      system_admin_description: '拥有系统所有权限',
      total_roles: '共 {count} 个角色',
      branch_admin: '分行管理员',
      branch_admin_description: '管理分行业务和操作员',
      window_operator: '窗口操作员',
      no_description: '暂无描述',
      actions: {
        edit: '编辑',
        delete: '删除',
        view: '查看',
        create: '创建'
      },
      form: {
        role_name_required: '请输入角色名称',
        role_name_max_length: '角色名称不能超过50个字符',
        no_permissions_warning: '未选择任何权限，确定要创建这个角色吗？',
        protected_role_name: '系统管理员角色名称不能修改',
        select_all: '全选',
        clear_all: '全不选',
        selected_count: '已选择 {count} 个权限'
      },
      messages: {
        create_success: '角色创建成功',
        update_success: '保存',
        delete_success: '角色删除成功',
        delete_failed: '删除失败',
        protected_role_delete: '系统管理员角色受保护，不能删除',
        confirm_delete: '确定要删除角色"{name}"吗？',
        load_data_failed: '加载数据失败',
        load_roles_failed: '加载角色失败',
        load_permissions_failed: '加载权限失败',
        save_role_failed: '保存角色失败',
        delete_role_failed: '删除角色失败',
        network_error: '网络连接失败，请检查网络连接',
        server_error: '服务器内部错误，请稍后重试',
        permission_denied: '您没有足够的权限执行此操作',
        login_expired: '登录已过期，请重新登录',
        request_error: '请求参数错误',
        unknown_error: '未知错误'
      }
    },
    
    // 表格相关
    table: {
      serial_number: '序号',
      actions: '操作',
      loading: '加载中...',
      no_data: '暂无数据',
      cannot_load: '无法加载数据',
      cannot_get_branch: '无法获取当前网点信息',
      edit_only: '仅可编辑',
      has_business_data: '该网点有业务数据，无法删除',
      delete_branch: '删除网点'
    },
    
    // 表单相关
    form: {
      required: '必填',
      select_currency: '请选择本币',
      enable_status: '启用状态',
      cancel: '取消',
      save: '保存',
      saving: '保存中...',
      understand: '明白了'
    },
    
    // 网点代码帮助
    branch_code_help: {
      title: '网点代码说明',
      existing_codes: '已有网点代码：',
      code_rules: '代码规则说明：',
      head_office: '总行使用 HO 开头，如：HO001',
      branch_office: '分行使用城市拼音首字母，如：',
      sub_branch: '支行在分行代码基础上增加序号，如：',
      examples: {
        beijing: '北京分行：BJ001',
        shanghai: '上海分行：SH001',
        guangzhou: '广州分行：GZ001',
        beijing_sub1: '北京分行第一支行：BJ101',
        beijing_sub2: '北京分行第二支行：BJ102'
      },
      code_format: '建议格式：地区代码 + 3位数字，如：BJ001'
    },
    
    // 权限相关
    permissions: {
      no_branch_manage: '您没有访问网点管理的权限，需要 branch_manage 或 system_manage 权限',
      no_branch_info: '无法获取当前网点信息，请联系系统管理员检查用户配置'
    },
    
    // 操作消息
    messages: {
      branch_update_success: '网点更新成功',
      branch_add_success: '网点添加成功',
      branch_delete_success: '网点删除成功',
      fetch_branches_failed: '获取网点列表失败',
      fetch_currencies_failed: '获取币种列表失败',
      save_failed: '保存失败',
      delete_failed: '删除失败',
      check_branch_data_failed: '检查网点数据失败',
      cannot_delete_branch: '无法删除该网点，原因：',
      confirm_delete: '确定要删除网点 "{name}" 吗？\n\n注意：删除后将无法恢复，请谨慎操作！'
    }
  },

  // 清空营业数据
  data_clear: {
    title: '清空营业数据',
    subtitle: '危险操作区域 - 需要系统管理权限',
    permission_denied: '权限不足：您没有系统管理权限，无法执行此操作。',
    clear_success: '清空成功！营业数据已成功清空，您可以重新进行期初设置。',
    clear_time: '清空时间',
    current_branch: '当前网点',
    branch_status: '网点状态',
    clear_reason: '清空原因',
    security_password: '安全密码',
    final_confirm: '我确认理解此操作的风险，并同意清空所有营业数据',
    confirm_clear: '确认清空',
    important_notes: '重要说明',
    danger_warning: '⚠️ 危险操作警告',
    danger_description: '此操作将永久删除以下数据：',
    data_to_clear: [
      '所有交易记录',
      '所有余额调节记录',
      '所有日结历史数据',
      '所有相关的业务数据'
    ],
    operation_irreversible: '此操作不可逆转，请慎重考虑！',
    usage_scenarios: '使用场景',
    scenarios: [
      '系统初始化',
      '测试数据清理',
      '重大错误修复',
      '网点重新开业'
    ],
    operation_consequences: '操作后果',
    consequences: [
      '网点状态重置为期初状态',
      '可以重新进行期初设置',
      '所有业务数据归零',
      '操作记录保留在系统日志中'
    ],
    warning_message: '您即将清空当前网点 {branch} 的所有营业数据！',
    clear_history: '清空历史记录',
    form: {
      reason_required: '请输入清空原因（至少10个字符）',
      reason_placeholder: '请详细说明清空营业数据的原因（至少10个字符）',
      password_required: '请输入安全密码',
      password_placeholder: '请输入安全密码',
      password_help: '请输入正确的安全密码以继续操作',
      confirm_required: '请确认清空操作'
    },
    messages: {
      clear_success: '当前网点营业数据清空成功！',
      clear_failed: '清空营业数据失败',
      invalid_password: '安全密码不正确',
      reason_too_short: '原因说明至少需要10个字符'
    },
    data_clear_operation: '数据清空操作',
    current_branch_info: '当前网点信息',
    clear_status: '清空状态',
    can_clear: '可清空',
    cannot_clear: '不可清空',
    data_stats: '数据统计',
    transactions: '交易记录',
    adjustments: '余额调节',
    eod_reports: '日结记录',
    blocking_reason: '无法清空原因',
    clearing: '正在清空...',
    clear_current_branch: '清空当前网点营业数据'
  },

  // 币种维护
  currency_maintenance: {
    title: '币种维护',
    subtitle: '管理系统支持的货币类型',
    currency_list: '币种列表',
    add_currency: '添加币种',
    edit_currency: '编辑币种',
    currency_code: '币种代码',
    currency_name: '币种名称',
    symbol: '符号',
    is_base: '是否本币',
    is_active: '是否激活',
    actions: {
      edit: '编辑',
      delete: '删除',
      view: '查看'
    },
    form: {
      currency_code_required: '请输入币种代码',
      currency_name_required: '请输入币种名称',
      symbol_required: '请输入币种符号'
    },
    messages: {
      save_success: '币种保存成功',
      save_failed: '币种保存失败',
      delete_success: '币种删除成功',
      delete_failed: '币种删除失败',
      code_exists: '币种代码已存在'
    }
  },

  // 规范管理
  specification_management: {
    title: '规范管理',
    subtitle: '管理系统业务规范和设置',
    tabs: {
      print_settings: '打印设置',
      receipt_files: '已打票据文件',
      other_settings: '其他设置'
    },
    print_settings: {
      title: '打印设置',
      printer_name: '打印机名称',
      paper_size: '纸张大小',
      orientation: '方向',
      margin: '边距',
      font_size: '字体大小'
    },
    receipt_files: {
      title: '已打票据文件',
      year: '年',
      month: '月',
      file_count: '文件数量',
      total_size: '总大小',
      last_modified: '最后修改'
    },
    other_settings: {
      title: '其他设置',
      system_name: '系统名称',
      company_name: '公司名称',
      contact_info: '联系信息'
    }
  }
} 