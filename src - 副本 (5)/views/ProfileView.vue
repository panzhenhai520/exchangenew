<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2>
            <font-awesome-icon :icon="['fas', 'user-edit']" class="me-2" />
            {{ $t('profile.title') }}
          </h2>
        </div>

        <!-- 账户信息 - 横向显示 -->
        <div class="mb-4">
          <h6 class="mb-3">
            <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
            {{ $t('profile.account_info.title') }}
          </h6>
          <div class="row account-info-section">
            <div class="col-md-3 account-info-item">
              <span class="text-muted">{{ $t('profile.account_info.branch') }}：</span>
              <span class="fw-bold">{{ profile.branch_name || $t('profile.account_info.not_set') }}</span>
            </div>
            <div class="col-md-3 account-info-item">
              <span class="text-muted">{{ $t('profile.account_info.role') }}：</span>
              <span class="badge bg-primary">{{ profile.role_name || $t('profile.account_info.not_set') }}</span>
            </div>
            <div class="col-md-3 account-info-item">
              <span class="text-muted">{{ $t('profile.account_info.status') }}：</span>
              <span :class="profile.status === 'active' ? 'badge bg-success' : 'badge bg-secondary'">
                {{ profile.status === 'active' ? $t('profile.account_info.active') : $t('profile.account_info.inactive') }}
              </span>
            </div>
            <div class="col-md-3 account-info-item">
              <span class="text-muted">{{ $t('profile.account_info.last_login') }}：</span>
              <span class="fw-bold">{{ formatDateTime(profile.last_login) }}</span>
            </div>
          </div>
        </div>

        <div class="row">
          <!-- 基本信息卡片 -->
          <div class="col-lg-9">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'user']" class="me-2" />
                  {{ $t('profile.basic_info.title') }}
                </h5>
              </div>
              <div class="card-body">
                <form @submit.prevent="updateProfile">
                  <div class="row">
                    <div class="col-md-6">
                      <div class="mb-3">
                        <label for="loginCode" class="form-label">{{ $t('profile.basic_info.login_account') }}</label>
                        <input
                          type="text"
                          class="form-control"
                          id="loginCode"
                          v-model="profile.login_code"
                          readonly
                          disabled
                        />
                        <div class="form-text">{{ $t('profile.basic_info.login_account_readonly') }}</div>
                      </div>
                    </div>
                    <div class="col-md-6">
                      <div class="mb-3">
                        <label for="name" class="form-label">{{ $t('profile.basic_info.name') }}</label>
                        <input
                          type="text"
                          class="form-control"
                          id="name"
                          v-model="profile.name"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div class="row">
                    <div class="col-md-6">
                      <div class="mb-3">
                        <label for="email" class="form-label">{{ $t('profile.basic_info.email') }}</label>
                        <input
                          type="email"
                          class="form-control"
                          id="email"
                          v-model="profile.email"
                          :placeholder="$t('profile.basic_info.email_placeholder')"
                        />
                      </div>
                    </div>
                    <div class="col-md-6">
                      <div class="mb-3">
                        <label for="mobileNumber" class="form-label">{{ $t('profile.basic_info.mobile') }}</label>
                        <input
                          type="tel"
                          class="form-control"
                          id="mobileNumber"
                          v-model="profile.mobile_number"
                          :placeholder="$t('profile.basic_info.mobile_placeholder')"
                          pattern="^[+]?[0-9\-\s()]{7,20}$"
                        />
                      </div>
                    </div>
                  </div>

                  <div class="row">
                    <div class="col-md-6">
                      <div class="mb-3">
                        <label for="phoneNumber" class="form-label">{{ $t('profile.basic_info.phone') }}</label>
                        <input
                          type="tel"
                          class="form-control"
                          id="phoneNumber"
                          v-model="profile.phone_number"
                          :placeholder="$t('profile.basic_info.phone_placeholder')"
                          pattern="^[+]?[0-9\-\s()]{7,20}$"
                        />
                      </div>
                    </div>
                    <div class="col-md-6">
                      <div class="mb-3">
                        <label for="idCardNumber" class="form-label">{{ $t('profile.basic_info.id_card') }}</label>
                        <input
                          type="text"
                          class="form-control"
                          id="idCardNumber"
                          v-model="profile.id_card_number"
                          :placeholder="$t('profile.basic_info.id_card_placeholder')"
                        />
                      </div>
                    </div>
                  </div>

                  <div class="mb-3">
                    <label for="address" class="form-label">{{ $t('profile.basic_info.address') }}</label>
                    <textarea
                      class="form-control"
                      id="address"
                      rows="3"
                      v-model="profile.address"
                      :placeholder="$t('profile.basic_info.address_placeholder')"
                    ></textarea>
                  </div>

                  <div class="d-flex justify-content-end">
                    <button type="submit" class="btn btn-primary" :disabled="updating">
                      <span v-if="updating">
                        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                        {{ $t('profile.basic_info.saving') }}
                      </span>
                      <span v-else>
                        <font-awesome-icon :icon="['fas', 'save']" class="me-1" />
                        {{ $t('profile.basic_info.save') }}
                      </span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>

          <!-- 密码修改卡片 -->
          <div class="col-lg-3">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'key']" class="me-2" />
                  {{ $t('profile.password_change.title') }}
                </h5>
              </div>
              <div class="card-body">
                <div class="alert alert-info mb-3" v-if="changingPassword">
                  <small>
                    <font-awesome-icon :icon="['fas', 'info-circle']" class="me-1" />
                    {{ $t('profile.password_change.processing') }}
                  </small>
                </div>
                
                <form @submit.prevent="changePassword">
                  <div class="mb-3">
                    <label for="currentPassword" class="form-label">{{ $t('profile.password_change.current_password') }}</label>
                    <input
                      type="password"
                      class="form-control"
                      id="currentPassword"
                      v-model="passwordForm.currentPassword"
                      required
                      :placeholder="$t('profile.password_change.current_password_placeholder')"
                    />
                  </div>

                  <div class="mb-3">
                    <label for="newPassword" class="form-label">{{ $t('profile.password_change.new_password') }}</label>
                    <input
                      type="password"
                      class="form-control"
                      id="newPassword"
                      v-model="passwordForm.newPassword"
                      required
                      minlength="6"
                      :placeholder="$t('profile.password_change.new_password_placeholder')"
                      :class="{
                        'is-invalid': passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword
                      }"
                    />
                    <div class="form-text">{{ $t('profile.password_change.password_min_length') }}</div>
                  </div>

                  <div class="mb-3">
                    <label for="confirmPassword" class="form-label">{{ $t('profile.password_change.confirm_password') }}</label>
                    <input
                      type="password"
                      class="form-control"
                      id="confirmPassword"
                      v-model="passwordForm.confirmPassword"
                      required
                      :placeholder="$t('profile.password_change.confirm_password_placeholder')"
                      :class="{
                        'is-valid': passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword === passwordForm.confirmPassword,
                        'is-invalid': passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword
                      }"
                    />
                    <div v-if="passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword" class="invalid-feedback">
                      {{ $t('profile.messages.new_password_mismatch') }}
                    </div>
                    <div v-if="passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword === passwordForm.confirmPassword" class="valid-feedback">
                      {{ $t('profile.messages.password_match') }}
                    </div>
                  </div>

                  <div class="d-grid">
                    <button 
                      type="submit" 
                      class="btn btn-warning" 
                      :disabled="changingPassword || !isPasswordValid"
                    >
                      <span v-if="changingPassword">
                        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        {{ $t('profile.password_change.changing') }}
                      </span>
                      <span v-else>
                        <font-awesome-icon :icon="['fas', 'key']" class="me-1" />
                        {{ $t('profile.password_change.change') }}
                      </span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatDateTime } from '@/utils/formatters'

export default {
  name: 'ProfileView',
  data() {
    return {
      profile: {
        login_code: '',
        name: '',
        email: '',
        mobile_number: '',
        phone_number: '',
        id_card_number: '',
        address: '',
        branch_name: '',
        role_name: '',
        status: '',
        last_login: null
      },
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      updating: false,
      changingPassword: false
    };
  },
  computed: {
    isPasswordValid() {
      return this.passwordForm.currentPassword &&
             this.passwordForm.newPassword &&
             this.passwordForm.confirmPassword &&
             this.passwordForm.newPassword === this.passwordForm.confirmPassword &&
             this.passwordForm.newPassword.length >= 6;
    }
  },
  methods: {
    async loadProfile() {
      try {
        const response = await this.$api.get('user/profile');
        if (response.data.success) {
          this.profile = { ...this.profile, ...response.data.user };
        } else {
          alert(response.data.message || this.$t('profile.messages.load_failed'));
        }
      } catch (error) {
        console.error('获取个人信息失败:', error);
        alert(error.response?.data?.message || this.$t('profile.messages.load_failed'));
      }
    },

    async updateProfile() {
      try {
        this.updating = true;
        
        const updateData = {
          name: this.profile.name,
          email: this.profile.email,
          mobile_number: this.profile.mobile_number,
          phone_number: this.profile.phone_number,
          id_card_number: this.profile.id_card_number,
          address: this.profile.address
        };

        const response = await this.$api.put('user/profile', updateData);
        
        if (response.data.success) {
          alert(this.$t('profile.messages.update_success'));
          
          // 更新localStorage中的用户信息
          const userStr = localStorage.getItem('user');
          if (userStr) {
            const user = JSON.parse(userStr);
            Object.assign(user, updateData);
            localStorage.setItem('user', JSON.stringify(user));
          }
        } else {
          alert(response.data.message || this.$t('profile.messages.update_failed'));
        }
      } catch (error) {
        console.error('更新个人信息失败:', error);
        alert(error.response?.data?.message || '更新个人信息失败');
      } finally {
        this.updating = false;
      }
    },

    async changePassword() {
      if (!this.isPasswordValid) {
        alert(this.$t('profile.messages.password_validation_failed'));
        return;
      }

      this.changingPassword = true;
      
      try {
        // 检查是否使用模拟token
        const token = localStorage.getItem('token');
        const isMockToken = token && token.includes('mock-signature');
        
        if (isMockToken) {
          // 模拟模式下的密码修改
          console.log('=== 模拟模式密码修改 ===');
          
          // 模拟成功响应
          alert(this.$t('profile.messages.mock_password_change_success'));
          
          // 清空密码表单
          this.passwordForm = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          };
          
          // 更新localStorage中的密码信息（仅用于演示）
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          user.lastPasswordChange = new Date().toISOString();
          localStorage.setItem('user', JSON.stringify(user));
          
          return;
        }
        
        // 真实API调用
        const response = await this.$api.put('user/change-password', {
          current_password: this.passwordForm.currentPassword,
          new_password: this.passwordForm.newPassword
        });
        
        if (response.data && response.data.success) {
          alert(this.$t('profile.messages.password_change_success_redirect'));
          
          // 清空密码表单
          this.passwordForm = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          };
          
          // 延迟跳转到登录页
          setTimeout(() => {
            localStorage.clear();
            this.$router.push('/login');
          }, 2000);
        } else {
          const errorMsg = response.data?.message || this.$t('profile.messages.password_change_failed');
          alert(this.$t('profile.messages.password_change_failed') + ': ' + errorMsg);
        }
      } catch (error) {
        console.error(this.$t('profile.messages.password_change_request_failed'), error);
        
        let errorMessage = this.$t('profile.messages.password_change_failed');
        
        if (error.response) {
          if (error.response.status === 400) {
            errorMessage = error.response.data?.message || this.$t('profile.messages.current_password_incorrect');
          } else if (error.response.status === 401) {
            errorMessage = this.$t('profile.messages.authentication_failed');
          } else if (error.response.status === 500) {
            errorMessage = this.$t('profile.messages.server_error');
          } else {
            errorMessage = error.response.data?.message || this.$t('profile.messages.request_failed', { status: error.response.status });
          }
        } else if (error.request) {
          errorMessage = this.$t('profile.messages.network_error');
        } else {
          errorMessage = this.$t('profile.messages.request_send_failed') + ': ' + error.message;
        }
        
        alert(errorMessage);
      } finally {
        this.changingPassword = false;
      }
    },

    formatDateTime
  },
  created() {
    // 从localStorage获取基本用户信息
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      this.profile = { ...this.profile, ...user };
    }
    
    // 从服务器获取完整的个人信息
    this.loadProfile();
  }
};
</script>

<style scoped>
.card {
  border: 1px solid #e3e6f0;
  box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
}

.card-header {
  background-color: #f8f9fc;
  border-bottom: 1px solid #e3e6f0;
}

.form-control:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.btn-primary {
  background-color: #4e73df;
  border-color: #4e73df;
}

.btn-primary:hover {
  background-color: #2e59d9;
  border-color: #2e59d9;
}

.btn-warning {
  background-color: #f6c23e;
  border-color: #f6c23e;
  color: #3a3b45;
}

.btn-warning:hover {
  background-color: #f4b619;
  border-color: #f4b619;
  color: #3a3b45;
}

.badge {
  font-size: 0.75rem;
}

.form-text {
  font-size: 0.875rem;
}

.invalid-feedback,
.valid-feedback {
  font-size: 0.875rem;
}

/* 账户信息横向显示样式 */
.account-info-section {
  background-color: #f8f9fc;
  border-radius: 0.375rem;
  padding: 0.75rem 1rem;
  border: 1px solid #e3e6f0;
}

.account-info-item {
  text-align: left;
  line-height: 1.5;
}

.account-info-item .text-muted {
  font-size: 0.875rem;
  margin-right: 0.5rem;
}

.account-info-item .fw-bold {
  font-size: 0.875rem;
}

.account-info-item .badge {
  font-size: 0.75rem;
  vertical-align: middle;
}
</style> 