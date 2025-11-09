export default {
  profile: {
    title: 'Personal Information Management',
    subtitle: 'Manage your account information and security settings',
    
    // Account Information Section
    account_info: {
      title: 'Account Information',
      branch: 'Affiliated Branch',
      role: 'User Role',
      status: 'Account Status',
      last_login: 'Last Login',
      not_set: 'Not Set',
      active: 'Active',
      inactive: 'Inactive'
    },
    
    // Basic Information Section
    basic_info: {
      title: 'Basic Information',
      login_account: 'Login Account',
      login_account_readonly: 'Login account cannot be modified',
      name: 'Name',
      email: 'Email Address',
      email_placeholder: 'Please enter email address',
      phone: 'Contact Phone',
      phone_placeholder: 'Please enter contact phone',
      mobile: 'Mobile Number',
      mobile_placeholder: 'Please enter mobile number',
      id_card: 'ID Number',
      id_card_placeholder: 'Please enter ID number',
      address: 'Contact Address',
      address_placeholder: 'Please enter contact address',
      save: 'Save Basic Information',
      saving: 'Saving...'
    },
    
    // Password Change Section
    password_change: {
      title: 'Change Password',
      current_password: 'Current Password',
      current_password_placeholder: 'Please enter current password',
      new_password: 'New Password',
      new_password_placeholder: 'Please enter new password',
      confirm_password: 'Confirm New Password',
      confirm_password_placeholder: 'Please re-enter new password',
      password_min_length: 'Password length at least 6 digits',
      change: 'Change Password',
      changing: 'Changing...',
      processing: 'Processing password change request, please wait...'
    },
    
    // Messages
    messages: {
      load_failed: 'Failed to load profile information',
      update_success: 'Personal information updated successfully',
      update_failed: 'Failed to update personal information',
      password_change_success: 'Password changed successfully',
      password_change_failed: 'Failed to change password',
      current_password_incorrect: 'Current password is incorrect',
      new_password_mismatch: 'New passwords do not match',
      password_match: 'Passwords match',
      validation_failed: 'Validation failed',
      password_validation_failed: 'Please check if password input is correct',
      mock_password_change_success: 'Password changed successfully!\n\n⚠️ Important Notice:\nYou are currently in mock login mode. Password changes are only valid for this session.\n\nCorrect operation process:\n1. Exit current mock session\n2. Login with real credentials: admin / 123456\n3. Change password again in real login state\n\nPlease click OK to logout, then login again with admin/123456.',
      password_change_success_redirect: 'Password changed successfully! The system will automatically redirect to login page in 2 seconds, please login with new password.',
      authentication_failed: 'Authentication failed, please login again',
      server_error: 'Server internal error, please try again later',
      request_failed: 'Request failed (Status: {status})',
      network_error: 'Network connection failed, please check network connection and try again',
      request_send_failed: 'Request send failed',
      password_change_request_failed: 'Password change request failed'
    },
    
    // Validation
    validation: {
      email_invalid: 'Invalid email format',
      phone_invalid: 'Invalid phone number format',
      mobile_invalid: 'Invalid mobile number format',
      id_card_invalid: 'Invalid ID number format',
      password_required: 'Password is required',
      current_password_required: 'Current password is required',
      new_password_required: 'New password is required',
      confirm_password_required: 'Password confirmation is required'
    }
  }
} 