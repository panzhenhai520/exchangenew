export default {
  profile: {
    title: '个人信息管理',
    subtitle: '管理您的账户信息和安全设置',
    
    // 账户信息部分
    account_info: {
      title: '账户信息',
      branch: '所属网点',
      role: '用户角色',
      status: '账户状态',
      last_login: '最后登录',
      not_set: '未设置',
      active: '正常',
      inactive: '停用'
    },
    
    // 基本信息部分
    basic_info: {
      title: '基本信息',
      login_account: '登录账号',
      login_account_readonly: '登录账号不可修改',
      name: '姓名',
      email: '邮箱地址',
      email_placeholder: '请输入邮箱地址',
      phone: '联系电话',
      phone_placeholder: '请输入联系电话',
      mobile: '手机号码',
      mobile_placeholder: '请输入手机号码',
      id_card: '身份证号',
      id_card_placeholder: '请输入身份证号',
      address: '联系地址',
      address_placeholder: '请输入联系地址',
      save: '保存基本信息',
      saving: '保存中...'
    },
    
    // 修改密码部分
    password_change: {
      title: '修改密码',
      current_password: '当前密码',
      current_password_placeholder: '请输入当前密码',
      new_password: '新密码',
      new_password_placeholder: '请输入新密码',
      confirm_password: '确认新密码',
      confirm_password_placeholder: '请再次输入新密码',
      password_min_length: '密码长度至少6位',
      change: '修改密码',
      changing: '修改中...',
      processing: '正在处理密码修改请求，请稍候...'
    },
    
    // 消息
    messages: {
      load_failed: '获取个人信息失败',
      update_success: '个人信息更新成功',
      update_failed: '更新个人信息失败',
      password_change_success: '密码修改成功',
      password_change_failed: '修改密码失败',
      current_password_incorrect: '当前密码不正确',
      new_password_mismatch: '新密码不匹配',
      password_match: '密码确认一致',
      validation_failed: '验证失败',
      password_validation_failed: '请检查密码输入是否正确',
      mock_password_change_success: '密码修改成功！\n\n⚠️ 重要提示：\n当前处于模拟登录模式，密码修改仅在本次会话中有效。\n\n正确的操作流程：\n1. 退出当前模拟会话\n2. 使用真实凭据登录：admin / 123456\n3. 在真实登录状态下重新修改密码\n\n请点击确定后退出登录，然后使用 admin/123456 重新登录。',
      password_change_success_redirect: '密码修改成功！系统将在2秒后自动跳转到登录页面，请使用新密码重新登录',
      authentication_failed: '身份验证失败，请重新登录',
      server_error: '服务器内部错误，请稍后重试',
      request_failed: '请求失败 (状态码: {status})',
      network_error: '网络连接失败，请检查网络连接后重试',
      request_send_failed: '请求发送失败',
      password_change_request_failed: '密码修改请求失败'
    },
    
    // 验证
    validation: {
      email_invalid: '邮箱格式不正确',
      phone_invalid: '电话号码格式不正确',
      mobile_invalid: '手机号码格式不正确',
      id_card_invalid: '身份证号码格式不正确',
      password_required: '密码不能为空',
      current_password_required: '当前密码不能为空',
      new_password_required: '新密码不能为空',
      confirm_password_required: '确认密码不能为空'
    }
  }
} 