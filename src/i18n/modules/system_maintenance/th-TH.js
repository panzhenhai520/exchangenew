export default {
  system_maintenance: {
    title: 'ระบบบำรุงรักษา',
    subtitle: 'จัดการการตั้งค่าระบบและข้อมูลพื้นฐาน',
    
    // การจัดการผู้ใช้
    user_management: {
      title: 'การจัดการผู้ใช้',
      subtitle: 'จัดการผู้ใช้ บทบาท และสิทธิ์ของระบบ',
      user_list: 'รายการผู้ใช้',
      add_user: 'เพิ่มผู้ใช้',
      edit_user: 'แก้ไขผู้ใช้',
      user_info: 'ข้อมูลผู้ใช้',
      login_code: 'รหัสเข้าสู่ระบบ',
      name: 'ชื่อ',
      role: 'บทบาท',
      role_names: {
        '系统管理员': 'ผู้ดูแลระบบ',
        '网点管理员': 'ผู้จัดการสาขา',
        '分行管理员': 'ผู้ดูแลสาขา',
        '窗口操作员': 'ผู้ปฏิบัติงานหน้าต่าง',
        'TEST Role': 'บทบาททดสอบ',
        'unassigned': 'ไม่ได้กำหนด'
      },
      branch: 'สาขา',
      status: 'สถานะ',
      password: 'รหัสผ่าน',
      id_card_number: 'เลขบัตรประชาชน',
      phone_number: 'หมายเลขโทรศัพท์',
      mobile_number: 'หมายเลขมือถือ',
      address: 'ที่อยู่',
      email: 'อีเมล',
      status_options: {
        active: 'เปิดใช้งาน',
        inactive: 'ปิดใช้งาน',
        locked: 'ล็อค',
        suspended: 'ระงับ'
      },
      actions: {
        edit: 'แก้ไข',
        reset_password: 'รีเซ็ตรหัสผ่าน',
        disable: 'ปิดใช้งาน',
        enable: 'เปิดใช้งาน',
        delete: 'ลบผู้ใช้',
        view_permissions: 'ดูสิทธิ์',
        hide_permissions: 'ซ่อนสิทธิ์'
      },
      permission_restrictions: {
        app_role_no_edit: 'ผู้ใช้บทบาท App ไม่สามารถแก้ไขได้',
        app_role_no_reset_password: 'ผู้ใช้บทบาท App ไม่สามารถรีเซ็ตรหัสผ่านได้',
        app_role_no_status_change: 'ผู้ใช้บทบาท App ไม่สามารถเปลี่ยนสถานะได้',
        app_role_no_delete: 'ผู้ใช้บทบาท App ไม่สามารถลบได้'
      },
      form: {
        login_code_required: 'กรุณาใส่ชื่อผู้ใช้',
        name_required: 'กรุณาใส่ชื่อ',
        role_required: 'กรุณาเลือกบทบาทผู้ใช้',
        branch_required: 'กรุณาเลือกสาขา',
        password_required: 'กรุณาตั้งรหัสผ่านเริ่มต้น',
        password_min_length: 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร',
        email_invalid: 'รูปแบบอีเมลไม่ถูกต้อง',
        phone_invalid: 'รูปแบบหมายเลขโทรศัพท์ไม่ถูกต้อง',
        mobile_invalid: 'รูปแบบหมายเลขมือถือไม่ถูกต้อง',
        id_card_invalid: 'รูปแบบเลขบัตรประชาชนไม่ถูกต้อง'
      },
      messages: {
        create_success: 'สร้างผู้ใช้สำเร็จ',
        update_success: 'อัปเดตผู้ใช้สำเร็จ',
        delete_success: 'ลบผู้ใช้สำเร็จ',
        reset_password_success: 'รีเซ็ตรหัสผ่านสำเร็จ',
        operation_failed: 'การดำเนินการล้มเหลว',
        business_check_failed: 'ตรวจสอบธุรกรรมผู้ใช้ล้มเหลว'
      },
      no_permissions: 'ผู้ใช้นี้ไม่มีสิทธิ์',
      personal_info: 'ข้อมูลส่วนตัว',
      no_personal_info: 'ไม่มีข้อมูลส่วนตัว',
      never_login: 'ไม่เคยเข้าสู่ระบบ',
      no_users_found: 'ไม่พบผู้ใช้',
      permissions: 'สิทธิ์',
      account_status: 'สถานะบัญชี',
      initial_password: 'รหัสผ่านเริ่มต้น',
      optional: 'ไม่บังคับ',
      current_branch: 'สาขาปัจจุบัน',
      can_only_create_for_current_branch: 'คุณสามารถสร้างผู้ใช้สำหรับสาขาปัจจุบันเท่านั้น',
      confirm_delete: 'ยืนยันการลบ',
      confirm_delete_message: 'คุณแน่ใจหรือไม่ที่จะลบผู้ใช้ {user}? การดำเนินการนี้ไม่สามารถยกเลิกได้',
      delete_check_title: 'ตรวจสอบก่อนลบ',
      delete_check_description: 'ระบบจะตรวจสอบว่าผู้ใช้นี้มีธุรกรรมแลกเปลี่ยน ธุรกรรมยกเลิก การปรับยอดคงเหลือ หรือการตั้งยอดคงเหลือเริ่มต้นหรือไม่ หากมีธุรกรรมใดๆ การลบจะไม่ได้รับอนุญาต และแนะนำให้ปิดการใช้งานผู้ใช้แทน',
      reset_password: 'รีเซ็ตรหัสผ่าน',
      confirm_reset_password: 'ยืนยันการรีเซ็ตรหัสผ่าน',
      reset_password_for_user: 'คุณกำลังรีเซ็ตรหัสผ่านสำหรับผู้ใช้ {name} ({code})',
      password_will_be_reset_to: 'รหัสผ่านจะถูกรีเซ็ตเป็น',
      recommend_change_password: 'แนะนำให้ผู้ใช้เปลี่ยนรหัสผ่านทันทีหลังเข้าสู่ระบบครั้งแรก',
      confirm_reset: 'ยืนยันการรีเซ็ต',
      status_update_success: 'อัปเดตสถานะผู้ใช้สำเร็จ',
      status_update_failed: 'อัปเดตสถานะล้มเหลว',
      password_reset_success: 'รหัสผ่านสำหรับผู้ใช้ {name} ได้ถูกรีเซ็ตเป็น 123456',
      placeholder: {
        login_code: 'กรุณาใส่ชื่อผู้ใช้',
        name: 'กรุณาใส่ชื่อจริง',
        select_role: 'กรุณาเลือกบทบาท',
        select_branch: 'กรุณาเลือกสาขา',
        set_initial_password: 'กรุณาตั้งรหัสผ่านเริ่มต้น',
        id_card_number: 'กรุณาใส่เลขบัตรประชาชน',
        email: 'กรุณาใส่อีเมล',
        phone_number: 'กรุณาใส่หมายเลขโทรศัพท์',
        mobile_number: 'กรุณาใส่หมายเลขมือถือ',
        address: 'กรุณาใส่ที่อยู่'
      },
      validation: {
        fill_username_and_name: 'กรุณาใส่ชื่อผู้ใช้และชื่อ',
        select_role: 'กรุณาเลือกบทบาทผู้ใช้',
        select_branch: 'กรุณาเลือกสาขา',
        branch_info_error: 'ข้อมูลสาขาผิดพลาด กรุณารีเฟรชหน้าและลองใหม่',
        set_initial_password: 'กรุณาตั้งรหัสผ่านเริ่มต้น',
        password_min_length: 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'
      }
    },
    
    // การจัดการสาขา
    branch_management: {
      title: 'การจัดการสาขา',
      subtitle: 'จัดการสาขาและบริษัทในเครือของระบบ',
      branch_list: 'รายการสาขา',
      branch_info: 'การจัดการข้อมูลสาขา',
      current_branch: 'สาขาปัจจุบัน',
      add_branch: 'เพิ่มสาขา',
      edit_branch: 'แก้ไขสาขา',
      branch_code: 'รหัสสาขา',
      branch_name: 'ชื่อสาขา',
      address: 'ที่อยู่',
      manager_name: 'ผู้จัดการ',
      phone_number: 'หมายเลขโทรศัพท์',
      base_currency: 'สกุลเงินหลัก',
      is_active: 'สถานะการใช้งาน',
      status: {
        active: 'ใช้งาน',
        inactive: 'ไม่ใช้งาน'
      },
      actions: {
        edit: 'แก้ไข',
        delete: 'ลบ',
        view: 'ดู'
      },
      form: {
        branch_code_required: 'กรุณาใส่รหัสสาขา',
        branch_name_required: 'กรุณาใส่ชื่อสาขา',
        address_required: 'กรุณาใส่ที่อยู่',
        manager_required: 'กรุณาใส่ชื่อผู้จัดการ',
        phone_required: 'กรุณาใส่หมายเลขโทรศัพท์',
        base_currency_required: 'กรุณาเลือกสกุลเงินหลัก'
      },
      messages: {
        save_success: 'บันทึกสาขาสำเร็จ',
        save_failed: 'บันทึกสาขาล้มเหลว',
        delete_success: 'ลบสาขาสำเร็จ',
        delete_failed: 'ลบสาขาล้มเหลว',
        code_exists: 'รหัสสาขามีอยู่แล้ว',
        invalid_code: 'รูปแบบรหัสสาขาไม่ถูกต้อง'
      }
    },
    
    // การจัดการบทบาท
    role_management: {
      title: 'การจัดการบทบาทและสิทธิ์',
      subtitle: 'จัดการบทบาทและสิทธิ์ของระบบ',
      role_list: 'รายการบทบาท',
      add_role: 'เพิ่มบทบาท',
      edit_role: 'แก้ไขบทบาท',
      role_name: 'ชื่อบทบาท',
      description: 'คำอธิบาย',
      permissions: 'สิทธิ์',
      permission_count: 'จำนวนสิทธิ์',
      permission_preview: 'ตัวอย่างสิทธิ์',
      protected_role: 'ป้องกัน',
      system_admin: 'ผู้ดูแลระบบ',
      system_admin_description: 'มีสิทธิ์ทั้งหมดของระบบ',
      total_roles: 'รวม {count} บทบาท',
      branch_admin: 'ผู้จัดการสาขา',
      branch_admin_description: 'จัดการธุรกิจสาขาและผู้ปฏิบัติงาน',
      window_operator: 'ผู้ปฏิบัติงานหน้าต่าง',
      no_description: 'ไม่มีคำอธิบาย',
      actions: {
        edit: 'แก้ไข',
        delete: 'ลบ',
        view: 'ดู',
        create: 'สร้าง'
      },
      form: {
        role_name_required: 'กรุณาใส่ชื่อบทบาท',
        role_name_max_length: 'ชื่อบทบาทไม่สามารถเกิน 50 ตัวอักษร',
        no_permissions_warning: 'ไม่ได้เลือกสิทธิ์ใดๆ คุณแน่ใจหรือไม่ที่จะสร้างบทบาทนี้?',
        protected_role_name: 'ชื่อบทบาทผู้ดูแลระบบไม่สามารถแก้ไขได้',
        select_all: 'เลือกทั้งหมด',
        clear_all: 'ล้างทั้งหมด',
        selected_count: 'เลือกสิทธิ์ {count} รายการ'
      },
      messages: {
        create_success: 'สร้างบทบาทสำเร็จ',
        update_success: 'อัปเดตบทบาทสำเร็จ',
        delete_success: 'ลบบทบาทสำเร็จ',
        delete_failed: 'ลบล้มเหลว',
        protected_role_delete: 'บทบาทผู้ดูแลระบบได้รับการป้องกันและไม่สามารถลบได้',
        confirm_delete: 'คุณแน่ใจหรือไม่ที่จะลบบทบาท "{name}"?',
        load_data_failed: 'ไม่สามารถโหลดข้อมูลได้',
        load_roles_failed: 'ไม่สามารถโหลดบทบาทได้',
        load_permissions_failed: 'ไม่สามารถโหลดสิทธิ์ได้',
        save_role_failed: 'ไม่สามารถบันทึกบทบาทได้',
        delete_role_failed: 'ไม่สามารถลบบทบาทได้',
        network_error: 'การเชื่อมต่อเครือข่ายล้มเหลว กรุณาตรวจสอบการเชื่อมต่อเครือข่าย',
        server_error: 'ข้อผิดพลาดภายในเซิร์ฟเวอร์ กรุณาลองใหม่อีกครั้ง',
        permission_denied: 'คุณไม่มีสิทธิ์เพียงพอในการดำเนินการนี้',
        login_expired: 'การเข้าสู่ระบบหมดอายุ กรุณาเข้าสู่ระบบอีกครั้ง',
        request_error: 'ข้อผิดพลาดพารามิเตอร์คำขอ',
        unknown_error: 'ข้อผิดพลาดที่ไม่ทราบสาเหตุ'
      }
    },
    
    // ตารางที่เกี่ยวข้อง
    table: {
      serial_number: 'ลำดับ',
      actions: 'การดำเนินการ',
      loading: 'กำลังโหลด...',
      no_data: 'ไม่มีข้อมูล',
      cannot_load: 'ไม่สามารถโหลดข้อมูลได้',
      cannot_get_branch: 'ไม่สามารถรับข้อมูลสาขาปัจจุบันได้',
      edit_only: 'แก้ไขเท่านั้น',
      has_business_data: 'สาขานี้มีข้อมูลธุรกิจและไม่สามารถลบได้',
      delete_branch: 'ลบสาขา'
    },
    
    // ฟอร์มที่เกี่ยวข้อง
    form: {
      required: 'จำเป็น',
      select_currency: 'กรุณาเลือกสกุลเงินหลัก',
      enable_status: 'สถานะการเปิดใช้งาน',
      cancel: 'ยกเลิก',
      save: 'บันทึก',
      saving: 'กำลังบันทึก...',
      understand: 'เข้าใจแล้ว'
    },
    
    // ความช่วยเหลือรหัสสาขา
    branch_code_help: {
      title: 'คำแนะนำรหัสสาขา',
      existing_codes: 'รหัสสาขาที่มีอยู่:',
      code_rules: 'กฎรหัส:',
      head_office: 'สำนักงานใหญ่ใช้ HO นำหน้า เช่น: HO001',
      branch_office: 'สำนักงานสาขาใช้ตัวอักษรแรกของเมือง เช่น:',
      sub_branch: 'สาขาย่อยเพิ่มหมายเลขลำดับให้กับรหัสสาขา เช่น:',
      examples: {
        beijing: 'สาขาปักกิ่ง: BJ001',
        shanghai: 'สาขาเซี่ยงไฮ้: SH001',
        guangzhou: 'สาขากว่างโจว: GZ001',
        beijing_sub1: 'สาขาย่อยที่ 1 ของปักกิ่ง: BJ101',
        beijing_sub2: 'สาขาย่อยที่ 2 ของปักกิ่ง: BJ102'
      },
      code_format: 'รูปแบบที่แนะนำ: รหัสภูมิภาค + ตัวเลข 3 หลัก เช่น: BJ001'
    },
    
    // สิทธิ์
    permissions: {
      no_branch_manage: 'คุณไม่มีสิทธิ์ในการเข้าถึงการจัดการสาขา ต้องการสิทธิ์ branch_manage หรือ system_manage',
      no_branch_info: 'ไม่สามารถรับข้อมูลสาขาปัจจุบันได้ กรุณาติดต่อผู้ดูแลระบบเพื่อตรวจสอบการตั้งค่าผู้ใช้'
    },
    
    // ข้อความการดำเนินการ
    messages: {
      branch_update_success: 'อัปเดตสาขาสำเร็จ',
      branch_add_success: 'เพิ่มสาขาสำเร็จ',
      branch_delete_success: 'ลบสาขาสำเร็จ',
      fetch_branches_failed: 'ไม่สามารถดึงรายการสาขาได้',
      fetch_currencies_failed: 'ไม่สามารถดึงรายการสกุลเงินได้',
      save_failed: 'บันทึกล้มเหลว',
      delete_failed: 'ลบล้มเหลว',
      check_branch_data_failed: 'ไม่สามารถตรวจสอบข้อมูลสาขาได้',
      cannot_delete_branch: 'ไม่สามารถลบสาขานี้ได้ เหตุผล:',
      confirm_delete: 'คุณแน่ใจหรือไม่ที่จะลบสาขา "{name}"?\n\nหมายเหตุ: การดำเนินการนี้ไม่สามารถยกเลิกได้ กรุณาดำเนินการด้วยความระมัดระวัง!'
    }
  },

  // การบำรุงรักษาสกุลเงิน
  currency_maintenance: {
    title: 'การบำรุงรักษาสกุลเงิน',
    subtitle: 'จัดการประเภทสกุลเงินที่ระบบรองรับ',
    currency_list: 'รายการสกุลเงิน',
    add_template: 'เพิ่มเทมเพลต',
    init_templates: 'เริ่มต้นเทมเพลต',
    currency_code: 'รหัสสกุลเงิน',
    currency_name: 'ชื่อสกุลเงิน',
    country: 'ประเทศ',
    symbol: 'สัญลักษณ์',
    is_active: 'เปิดใช้งาน',
    actions: {
      edit: 'แก้ไข',
      delete: 'ลบ',
      view: 'ดู'
    },
    messages: {
      init_success: 'เริ่มต้นเทมเพลตสกุลเงินสำเร็จ',
      save_success: 'บันทึกสกุลเงินสำเร็จ',
      delete_success: 'ลบสกุลเงินสำเร็จ',
      operation_failed: 'การดำเนินการล้มเหลว'
    }
  },

  // การจัดการข้อกำหนด
  specification_management: {
    title: 'การจัดการข้อกำหนด',
    subtitle: 'จัดการข้อกำหนดทางธุรกิจและการตั้งค่าของระบบ',
    tabs: {
      print_settings: 'การตั้งค่าการพิมพ์',
      receipt_files: 'ไฟล์ใบเสร็จที่พิมพ์แล้ว',
      other_settings: 'การตั้งค่าอื่นๆ'
    },
    print_settings: {
      title: 'การตั้งค่าการพิมพ์',
      printer_name: 'ชื่อเครื่องพิมพ์',
      paper_size: 'ขนาดกระดาษ',
      orientation: 'ทิศทาง',
      margin: 'ขอบ',
      font_size: 'ขนาดตัวอักษร'
    },
    receipt_files: {
      title: 'ไฟล์ใบเสร็จที่พิมพ์แล้ว',
      year: 'ปี',
      month: 'เดือน',
      day: 'วัน',
      file_name: 'ชื่อไฟล์',
      file_size: 'ขนาดไฟล์',
      created_at: 'สร้างเมื่อ',
      actions: 'การดำเนินการ'
    },
    other_settings: {
      title: 'การตั้งค่าอื่นๆ',
      system_name: 'ชื่อระบบ',
      company_name: 'ชื่อบริษัท',
      contact_info: 'ข้อมูลการติดต่อ',
      backup_settings: 'การตั้งค่าการสำรองข้อมูล'
    }
  },

  // การล้างข้อมูล
  data_clear: {
    title: 'ล้างข้อมูลธุรกิจ',
    subtitle: 'พื้นที่การดำเนินการอันตราย - ต้องการสิทธิ์การจัดการระบบ',
    permission_denied: 'สิทธิ์ไม่เพียงพอ: คุณไม่มีสิทธิ์การจัดการระบบในการดำเนินการนี้',
    clear_success: 'ล้างสำเร็จ! ข้อมูลธุรกิจได้รับการล้างสำเร็จแล้ว คุณสามารถตั้งค่าเริ่มต้นใหม่ได้',
    clear_time: 'เวลาล้าง',
    current_branch: 'สาขาปัจจุบัน',
    branch_status: 'สถานะสาขา',
    clear_reason: 'เหตุผลการล้าง',
    security_password: 'รหัสผ่านความปลอดภัย',
    final_confirm: 'ฉันยืนยันว่าฉันเข้าใจความเสี่ยงของการดำเนินการนี้และยินยอมล้างข้อมูลธุรกิจทั้งหมด',
    confirm_clear: 'ยืนยันการล้าง',
    important_notes: 'หมายเหตุสำคัญ',
    danger_warning: '⚠️ คำเตือนการดำเนินการอันตราย',
    danger_description: 'การดำเนินการนี้จะลบข้อมูลต่อไปนี้อย่างถาวร:',
    data_to_clear: [
      'บันทึกธุรกรรมทั้งหมด',
      'บันทึกการปรับยอดเงินทั้งหมด',
      'ข้อมูลประวัติการปิดวันทั้งหมด',
      'ข้อมูลธุรกิจที่เกี่ยวข้องทั้งหมด'
    ],
    operation_irreversible: 'การดำเนินการนี้ไม่สามารถยกเลิกได้ กรุณาพิจารณาอย่างรอบคอบ!',
    usage_scenarios: 'สถานการณ์การใช้งาน',
    scenarios: [
      'การเริ่มต้นระบบ',
      'การทำความสะอาดข้อมูลทดสอบ',
      'การซ่อมแซมข้อผิดพลาดร้ายแรง',
      'การเปิดสาขาใหม่'
    ],
    operation_consequences: 'ผลลัพธ์การดำเนินการ',
    consequences: [
      'สถานะสาขารีเซ็ตเป็นสถานะเริ่มต้น',
      'สามารถตั้งค่าเริ่มต้นใหม่ได้',
      'ข้อมูลธุรกิจทั้งหมดเป็นศูนย์',
      'บันทึกการดำเนินการเก็บไว้ในบันทึกระบบ'
    ],
    warning_message: 'คุณกำลังจะล้างข้อมูลธุรกิจทั้งหมดสำหรับสาขา {branch}!',
    clear_history: 'ประวัติการล้าง',
    form: {
      reason_required: 'กรุณาใส่เหตุผลการล้าง (อย่างน้อย 10 ตัวอักษร)',
      reason_placeholder: 'กรุณาอธิบายเหตุผลในการล้างข้อมูลธุรกิจอย่างละเอียด (อย่างน้อย 10 ตัวอักษร)',
      password_required: 'กรุณาใส่รหัสผ่านความปลอดภัย',
      password_placeholder: 'กรุณาใส่รหัสผ่านความปลอดภัย',
      password_help: 'กรุณาใส่รหัสผ่านความปลอดภัยที่ถูกต้องเพื่อดำเนินการต่อ',
      confirm_required: 'กรุณายืนยันการดำเนินการล้าง'
    },
    messages: {
      clear_success: 'ล้างข้อมูลธุรกิจสาขาปัจจุบันสำเร็จ!',
      clear_failed: 'ล้างข้อมูลธุรกิจล้มเหลว',
      invalid_password: 'รหัสผ่านความปลอดภัยไม่ถูกต้อง',
      reason_too_short: 'คำอธิบายเหตุผลต้องการอย่างน้อย 10 ตัวอักษร'
    },
    data_clear_operation: 'การดำเนินการล้างข้อมูล',
    current_branch_info: 'ข้อมูลสาขาปัจจุบัน',
    clear_status: 'สถานะการล้าง',
    can_clear: 'สามารถล้างได้',
    cannot_clear: 'ไม่สามารถล้างได้',
    blocking_reason: 'เหตุผลการบล็อก',
    data_stats: 'สถิติข้อมูล',
    transactions: 'ธุรกรรม',
    adjustments: 'การปรับ',
    eod_reports: 'รายงานปิดวัน',
    clearing: 'กำลังล้าง...',
    clear_current_branch: 'ล้างสาขาปัจจุบัน'
  },

  // การจัดการบันทึก
  log_management: {
    title: 'การจัดการบันทึก',
    subtitle: 'ดูและจัดการบันทึกระบบ',
    log_types: {
      all: 'ทั้งหมด',
      error: 'ข้อผิดพลาด',
      warning: 'คำเตือน',
      info: 'ข้อมูล',
      debug: 'ดีบัก'
    },
    table: {
      timestamp: 'เวลา',
      level: 'ระดับ',
      message: 'ข้อความ',
      source: 'แหล่งที่มา',
      user: 'ผู้ใช้'
    },
    actions: {
      export: 'ส่งออก',
      clear: 'ล้าง',
      refresh: 'รีเฟรช'
    }
  }
} 