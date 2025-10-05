export default {
  profile: {
    title: 'การจัดการข้อมูลส่วนตัว',
    subtitle: 'จัดการข้อมูลบัญชีและการตั้งค่าความปลอดภัย',
    
    // ส่วนข้อมูลบัญชี
    account_info: {
      title: 'ข้อมูลบัญชี',
      branch: 'สาขาที่สังกัด',
      role: 'บทบาทผู้ใช้',
      status: 'สถานะบัญชี',
      last_login: 'เข้าสู่ระบบล่าสุด',
      not_set: 'ไม่ได้ตั้งค่า',
      active: 'เปิดใช้งาน',
      inactive: 'ปิดใช้งาน'
    },
    
    // ส่วนข้อมูลพื้นฐาน
    basic_info: {
      title: 'ข้อมูลพื้นฐาน',
      login_account: 'บัญชีเข้าสู่ระบบ',
      login_account_readonly: 'บัญชีเข้าสู่ระบบไม่สามารถแก้ไขได้',
      name: 'ชื่อ',
      email: 'อีเมล',
      email_placeholder: 'กรุณาใส่อีเมล',
      phone: 'หมายเลขโทรศัพท์',
      phone_placeholder: 'กรุณาใส่หมายเลขโทรศัพท์',
      mobile: 'หมายเลขมือถือ',
      mobile_placeholder: 'กรุณาใส่หมายเลขมือถือ',
      id_card: 'เลขบัตรประชาชน',
      id_card_placeholder: 'กรุณาใส่เลขบัตรประชาชน',
      address: 'ที่อยู่',
      address_placeholder: 'กรุณาใส่ที่อยู่',
      save: 'บันทึกข้อมูลพื้นฐาน',
      saving: 'กำลังบันทึก...'
    },
    
    // ส่วนเปลี่ยนรหัสผ่าน
    password_change: {
      title: 'เปลี่ยนรหัสผ่าน',
      current_password: 'รหัสผ่านปัจจุบัน',
      current_password_placeholder: 'กรุณาใส่รหัสผ่านปัจจุบัน',
      new_password: 'รหัสผ่านใหม่',
      new_password_placeholder: 'กรุณาใส่รหัสผ่านใหม่',
      confirm_password: 'ยืนยันรหัสผ่านใหม่',
      confirm_password_placeholder: 'กรุณาใส่รหัสผ่านใหม่อีกครั้ง',
      password_min_length: 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร',
      change: 'เปลี่ยนรหัสผ่าน',
      changing: 'กำลังเปลี่ยน...',
      processing: 'กำลังประมวลผลคำขอเปลี่ยนรหัสผ่าน กรุณารอสักครู่...'
    },
    
    // ข้อความ
    messages: {
      load_failed: 'ไม่สามารถโหลดข้อมูลส่วนตัวได้',
      update_success: 'อัปเดตข้อมูลส่วนตัวสำเร็จ',
      update_failed: 'อัปเดตข้อมูลส่วนตัวล้มเหลว',
      password_change_success: 'เปลี่ยนรหัสผ่านสำเร็จ',
      password_change_failed: 'เปลี่ยนรหัสผ่านล้มเหลว',
      current_password_incorrect: 'รหัสผ่านปัจจุบันไม่ถูกต้อง',
      new_password_mismatch: 'รหัสผ่านใหม่ไม่ตรงกัน',
      password_match: 'รหัสผ่านตรงกัน',
      validation_failed: 'การตรวจสอบล้มเหลว',
      password_validation_failed: 'กรุณาตรวจสอบการป้อนรหัสผ่านว่าถูกต้องหรือไม่',
      mock_password_change_success: 'เปลี่ยนรหัสผ่านสำเร็จ!\n\n⚠️ หมายเหตุสำคัญ:\nคุณกำลังอยู่ในโหมดจำลองการเข้าสู่ระบบ การเปลี่ยนรหัสผ่านมีผลเฉพาะในเซสชันนี้เท่านั้น\n\nขั้นตอนการทำงานที่ถูกต้อง:\n1. ออกจากเซสชันจำลองปัจจุบัน\n2. เข้าสู่ระบบด้วยข้อมูลจริง: admin / 123456\n3. เปลี่ยนรหัสผ่านอีกครั้งในสถานะการเข้าสู่ระบบจริง\n\nกรุณาคลิกตกลงเพื่อออกจากระบบ แล้วเข้าสู่ระบบอีกครั้งด้วย admin/123456',
      password_change_success_redirect: 'เปลี่ยนรหัสผ่านสำเร็จ! ระบบจะเปลี่ยนเส้นทางไปยังหน้าล็อกอินโดยอัตโนมัติใน 2 วินาที กรุณาเข้าสู่ระบบด้วยรหัสผ่านใหม่',
      authentication_failed: 'การยืนยันตัวตนล้มเหลว กรุณาเข้าสู่ระบบอีกครั้ง',
      server_error: 'ข้อผิดพลาดภายในเซิร์ฟเวอร์ กรุณาลองใหม่อีกครั้ง',
      request_failed: 'คำขอล้มเหลว (สถานะ: {status})',
      network_error: 'การเชื่อมต่อเครือข่ายล้มเหลว กรุณาตรวจสอบการเชื่อมต่อเครือข่ายและลองใหม่อีกครั้ง',
      request_send_failed: 'การส่งคำขอล้มเหลว',
      password_change_request_failed: 'คำขอเปลี่ยนรหัสผ่านล้มเหลว'
    },
    
    // การตรวจสอบ
    validation: {
      email_invalid: 'รูปแบบอีเมลไม่ถูกต้อง',
      phone_invalid: 'รูปแบบหมายเลขโทรศัพท์ไม่ถูกต้อง',
      mobile_invalid: 'รูปแบบหมายเลขมือถือไม่ถูกต้อง',
      id_card_invalid: 'รูปแบบเลขบัตรประชาชนไม่ถูกต้อง',
      password_required: 'รหัสผ่านจำเป็น',
      current_password_required: 'รหัสผ่านปัจจุบันจำเป็น',
      new_password_required: 'รหัสผ่านใหม่จำเป็น',
      confirm_password_required: 'การยืนยันรหัสผ่านจำเป็น'
    }
  }
} 