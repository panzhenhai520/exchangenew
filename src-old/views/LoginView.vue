<template>
  <div class="login-page">
    <!-- 登录容器 -->
    <div class="login-container">
      <div class="login-card">
        <!-- 兑换动画Logo -->
        <div class="logo-section">
          <div class="exchange-logo">
            <div class="coins-stack">
              <!-- 四个硬币叠在一起 -->
              <div class="coin coin-1" :class="{ 'separating': isSeparating, 'combining': isCombining }">
                <span class="coin-letter">{{ currentLeft }}</span>
              </div>
              <div class="coin coin-2" :class="{ 'separating': isSeparating, 'combining': isCombining }">
                <span class="coin-letter">{{ currentRight }}</span>
              </div>
              <div class="coin coin-3" :class="{ 'separating': isSeparating, 'combining': isCombining }">
                <span class="coin-letter">{{ nextLeft }}</span>
              </div>
              <div class="coin coin-4" :class="{ 'separating': isSeparating, 'combining': isCombining }">
                <span class="coin-letter">{{ nextRight }}</span>
              </div>
            </div>
          </div>
          <!-- 系统名称标题 -->
          <div class="system-title">
            <h1 class="title-main">ExchangeOK</h1>
          </div>
        </div>
        
        <!-- 登录表单 -->
        <form @submit.prevent="handleSubmit" class="login-form">
          <!-- 用户名输入 -->
          <div class="input-group">
            <div class="input-icon">
              <font-awesome-icon :icon="['fas', 'user']" />
            </div>
            <input
              type="text"
              class="form-input"
              v-model="username"
              placeholder=""
              title="用户名"
              required
              :disabled="loading"
            />
          </div>
          
          <!-- 密码输入 -->
          <div class="input-group">
            <div class="input-icon">
              <font-awesome-icon :icon="['fas', 'lock']" />
            </div>
            <input
              type="password"
              class="form-input"
              v-model="password"
              placeholder=""
              title="密码"
              required
              :disabled="loading"
            />
          </div>
          
          <!-- 网点选择 -->
          <div class="input-group">
            <div class="input-icon">
              <font-awesome-icon :icon="['fas', 'building']" />
            </div>
            <select
              class="form-select"
              v-model="branch"
              title="选择网点"
              required
              :disabled="loading"
            >
              <option value="">{{ loading ? '正在加载网点...' : (branches.length > 0 ? '请选择网点' : '暂无可用网点') }}</option>
              <option v-for="b in branches" :key="b.id" :value="b.id">
                {{ b.branch_code }} - {{ b.branch_name }}
              </option>
            </select>
          </div>
          
          <!-- 错误提示 -->
          <div v-if="showError" class="error-message">
            <font-awesome-icon :icon="['fas', 'exclamation-triangle']" />
            <span>{{ errorMessage }}</span>
            <button @click="fetchBranches" class="retry-btn" type="button">
              重试
            </button>
          </div>

          <!-- 登录按钮 -->
          <button type="submit" class="login-btn" :disabled="loading">
            <font-awesome-icon :icon="['fas', 'arrow-right']" />
            <span>OK</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginView',
  data() {
    return {
      username: '',
      password: '',
      branch: '',
      showError: false,
      errorMessage: '',
      language: 'zh',
      branches: [],
      loading: false,
      currentLeft: 'R',
      currentRight: 'H',
      nextLeft: 'F',
      nextRight: 'X',
      isSeparating: false,
      isCombining: false,
      exchangeStep: 0
    };
  },
  mounted() {
    this.startExchangeAnimation();
  },
  methods: {
    startExchangeAnimation() {
      const exchangeSequence = [
        { left: 'R', right: 'H', nextLeft: 'F', nextRight: 'X' },
        { left: 'F', right: 'X', nextLeft: 'R', nextRight: 'H' },
        { left: 'R', right: 'H', nextLeft: 'F', nextRight: 'X' }
      ];
      
      setInterval(() => {
        this.performExchangeAnimation(exchangeSequence);
      }, 3000); // 每3秒执行一次完整动画
    },
    
    performExchangeAnimation(sequence) {
      // 第一步：分离动画
      this.isSeparating = true;
      
      setTimeout(() => {
        // 分离完成后，更新字母
        this.exchangeStep = (this.exchangeStep + 1) % sequence.length;
        const next = sequence[this.exchangeStep];
        this.currentLeft = next.left;
        this.currentRight = next.right;
        this.nextLeft = next.nextLeft;
        this.nextRight = next.nextRight;
        
        // 停止分离动画
        this.isSeparating = false;
        
        // 第二步：合并动画
        setTimeout(() => {
          this.isCombining = true;
          
          setTimeout(() => {
            this.isCombining = false;
          }, 800);
        }, 300);
        
      }, 800);
    },
    
    async fetchBranches() {
      try {
        console.log('🔄 开始获取网点列表...');

        // 检查API是否可用
        if (!this.$api) {
          console.error('❌ $api 实例不存在');
          throw new Error('API服务不可用');
        }

        const response = await this.$api.get('/auth/branches');
        console.log('✅ 获取网点列表响应:', response);

        if (response && response.data) {
          console.log('📊 响应数据结构:', {
            hasData: !!response.data,
            hasSuccess: 'success' in response.data,
            success: response.data.success,
            hasBranches: 'branches' in response.data,
            branchesType: typeof response.data.branches,
            branchesLength: Array.isArray(response.data.branches) ? response.data.branches.length : 'not array'
          });

          if (response.data.success) {
            this.branches = response.data.branches || [];
            console.log('✅ 成功获取网点列表:', this.branches);

            // 如果只有一个网点，自动选择
            if (this.branches.length === 1) {
              this.branch = this.branches[0].id;
              console.log('🎯 自动选择唯一网点:', this.branches[0]);
            }

            // 验证网点数据格式
            if (this.branches.length > 0) {
              const sampleBranch = this.branches[0];
              console.log('📋 网点数据示例:', sampleBranch);
              if (!sampleBranch.id || !sampleBranch.branch_name) {
                console.warn('⚠️ 网点数据格式可能不正确');
              }
            }
          } else {
            console.error('❌ API返回失败:', response.data.message);
            throw new Error(response.data?.message || '获取网点列表失败');
          }
        } else {
          console.error('❌ 无效的响应格式:', response);
          throw new Error('服务器响应格式错误');
        }
      } catch (error) {
        console.error('❌ 获取网点列表出错:', error);
        console.error('错误详情:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          stack: error.stack
        });

        let errorMsg = '获取网点列表失败';
        if (error.response) {
          if (error.response.status === 500) {
            errorMsg = '服务器内部错误，请稍后重试';
          } else if (error.response.status === 404) {
            errorMsg = '网点服务不可用';
          } else {
            errorMsg = error.response.data?.message || `服务器错误 (${error.response.status})`;
          }
        } else if (error.request) {
          errorMsg = '网络连接失败，请检查网络连接';
        } else {
          errorMsg = error.message || '未知错误';
        }

        this.errorMessage = errorMsg;
        this.showError = true;

        // 在错误情况下，不设置备用数据，让用户看到真实的错误信息
        console.log('❌ 网点加载失败，请检查后端服务是否正常运行');
        console.log('💡 提示：可点击重试按钮重新加载网点列表');
      }
    },

    toggleLanguage() {
      this.language = this.language === 'zh' ? 'en' : 'zh';
    },
    async handleSubmit() {
      this.loading = true;
      this.showError = false;
      this.errorMessage = '';
      
      try {
        console.log('=== 开始登录流程 ===');
        console.log('用户名:', this.username);
        console.log('网点ID:', this.branch);
        console.log('当前页面URL:', window.location.href);
        
        const loginData = {
          login_code: this.username,
          password: this.password,
          branch: this.branch
        };
        
        console.log('登录数据:', loginData);
        
        const response = await this.$api.post('/auth/login', loginData);
        
        console.log('=== 登录响应 ===');
        console.log('响应状态:', response.status);
        console.log('响应数据:', response.data);
        
        if (response.data.success) {
          const token = response.data.token;
          if (token) {
            console.log('=== 开始保存数据到localStorage ===');
            
            try {
              // 清除旧数据
              localStorage.clear();
              console.log('✅ 旧数据已清除');
              
              // 保存新数据
              localStorage.setItem('token', token);
              console.log('✅ token已保存');
              
              // 保存用户信息
              const userInfo = {
                ...response.data.user,
                role: response.data.user?.role_name || (this.username.toLowerCase() === 'admin' ? 'admin' : 'operator')
              };
              localStorage.setItem('user', JSON.stringify(userInfo));
              console.log('✅ 用户信息已保存:', userInfo);
              
              // 保存权限信息
              if (response.data.permissions) {
                localStorage.setItem('userPermissions', JSON.stringify(response.data.permissions));
                console.log('✅ 权限信息已保存');
              } else {
                localStorage.setItem('userPermissions', JSON.stringify([]));
                console.log('⚠️ 保存空权限信息');
              }
              
              // 验证保存结果
              const savedToken = localStorage.getItem('token');
              const savedUser = localStorage.getItem('user');
              const savedPermissions = localStorage.getItem('userPermissions');
              
              console.log('=== 验证保存结果 ===');
              console.log('保存的token:', savedToken ? '存在' : '不存在');
              console.log('保存的user:', savedUser ? '存在' : '不存在');
              console.log('保存的permissions:', savedPermissions ? '存在' : '不存在');
              
              if (!savedToken || !savedUser) {
                throw new Error('localStorage保存验证失败');
              }
              
              console.log('✅ 所有数据保存成功，准备跳转');
              
              // 根据用户角色跳转到不同页面
              const currentUser = JSON.parse(localStorage.getItem('user'));
              if (currentUser.role_name === 'App' || currentUser.role_name === 'APP') {
                console.log('📱 App角色用户，跳转到手机端首页');
                this.$router.push('/app');
              } else {
                console.log('💻 普通用户，跳转到桌面端首页');
              this.$router.push('/dashboard');
              }
              
            } catch (storageError) {
              console.error('❌ localStorage操作失败:', storageError);
              throw new Error(`localStorage操作失败: ${storageError.message}`);
            }
          } else {
            throw new Error('登录成功但未收到token');
          }
        } else {
          throw new Error(response.data.message || '登录失败');
        }
      } catch (error) {
        console.error('❌ 登录出错:', error);
        console.error('错误详情:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        });
        
        let errorMsg = '登录失败，请重试';
        if (error.response) {
          if (error.response.status === 401) {
            errorMsg = '用户名或密码错误';
          } else if (error.response.status === 400) {
            errorMsg = error.response.data?.message || '请求参数错误';
          } else if (error.response.status === 500) {
            errorMsg = '服务器内部错误，请稍后重试';
          } else {
            errorMsg = error.response.data?.message || `服务器错误 (${error.response.status})`;
          }
        } else if (error.request) {
          errorMsg = '网络连接失败，请检查网络连接';
        } else {
          errorMsg = error.message || '未知错误';
        }
        
        this.errorMessage = errorMsg;
        this.showError = true;
      } finally {
        this.loading = false;
      }
    }
  },
  created() {
    // 清除旧的认证信息
    localStorage.clear();
    sessionStorage.clear();
    
    // 移除API默认请求头
    delete this.$api.defaults.headers.common['Authorization'];
    
    // 清除所有可能的认证相关存储
    const keysToRemove = ['token', 'user', 'refresh_token', 'access_token'];
    keysToRemove.forEach(key => {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
    
    console.log('✅ 登录页面：已清除所有认证信息');
    
    // 获取网点列表
    this.fetchBranches();
  }
};
</script>

<style scoped>
/* 登录页面容器 */
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 30%, #dee2e6 100%);
  overflow: hidden;
}

/* 登录容器 */
.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 380px;
  padding: 0 20px;
}

/* 登录卡片 */
.login-card {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 35px 25px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 123, 255, 0.1), 
              0 2px 8px rgba(0, 0, 0, 0.05);
  animation: fadeInUp 0.6s ease-out;
}

/* Logo区域 */
.logo-section {
  text-align: center;
  margin-bottom: 30px;
  position: relative;
  height: 120px;
}

/* 兑换动画Logo */
.exchange-logo {
  position: relative;
  display: inline-block;
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
}

/* 系统标题样式 */
.system-title {
  text-align: center;
  margin-top: 10px;
}

.title-main {
  font-size: 26px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 5px 0;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.title-subtitle {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.5px;
}

/* 硬币堆叠容器 */
.coins-stack {
  position: relative;
  width: 155px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 硬币基础样式 */
.coin {
  position: absolute;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  border: 3px solid #daa520;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 四个硬币的初始位置（水平叠放，错开显示） */
.coin-1 {
  z-index: 4;
  transform: translate(0, 0);
}

.coin-2 {
  z-index: 3;
  transform: translate(35px, 0);
}

.coin-3 {
  z-index: 2;
  transform: translate(70px, 0);
}

.coin-4 {
  z-index: 1;
  transform: translate(105px, 0);
}

/* 分离动画 - 向四个角落分离 */
.coin.separating {
  animation: separateToCorners 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.coin-1.separating {
  animation-delay: 0s;
  animation-name: separateToTopLeft;
}

.coin-2.separating {
  animation-delay: 0.1s;
  animation-name: separateToTopRight;
}

.coin-3.separating {
  animation-delay: 0.2s;
  animation-name: separateToBottomLeft;
}

.coin-4.separating {
  animation-delay: 0.3s;
  animation-name: separateToBottomRight;
}

@keyframes separateToTopLeft {
  0% {
    transform: translate(0, 0);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  50% {
    transform: translate(-150px, -120px) scale(1.1);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  100% {
    transform: translate(-200px, -160px) scale(1);
    background: linear-gradient(135deg, #c0c0c0, #e5e5e5);
  }
}

@keyframes separateToTopRight {
  0% {
    transform: translate(35px, 0);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  50% {
    transform: translate(150px, -120px) scale(1.1);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  100% {
    transform: translate(200px, -160px) scale(1);
    background: linear-gradient(135deg, #b8860b, #daa520);
  }
}

@keyframes separateToBottomLeft {
  0% {
    transform: translate(70px, 0);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  50% {
    transform: translate(-150px, 120px) scale(1.1);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  100% {
    transform: translate(-200px, 160px) scale(1);
    background: linear-gradient(135deg, #cd7f32, #b87333);
  }
}

@keyframes separateToBottomRight {
  0% {
    transform: translate(105px, 0);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  50% {
    transform: translate(150px, 120px) scale(1.1);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  100% {
    transform: translate(200px, 160px) scale(1);
    background: linear-gradient(135deg, #8b4513, #a0522d);
  }
}

/* 合并动画 - 从四个角落回到中央 */
.coin.combining {
  animation: combineFromCorners 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.coin-1.combining {
  animation-delay: 0.3s;
  animation-name: combineFromTopLeft;
}

.coin-2.combining {
  animation-delay: 0.2s;
  animation-name: combineFromTopRight;
}

.coin-3.combining {
  animation-delay: 0.1s;
  animation-name: combineFromBottomLeft;
}

.coin-4.combining {
  animation-delay: 0s;
  animation-name: combineFromBottomRight;
}

@keyframes combineFromTopLeft {
  0% {
    transform: translate(-200px, -160px) scale(1);
    background: linear-gradient(135deg, #c0c0c0, #e5e5e5);
  }
  50% {
    transform: translate(-80px, -80px) scale(1.1);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  100% {
    transform: translate(0, 0);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
}

@keyframes combineFromTopRight {
  0% {
    transform: translate(200px, -160px) scale(1);
    background: linear-gradient(135deg, #b8860b, #daa520);
  }
  50% {
    transform: translate(80px, -80px) scale(1.1);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  100% {
    transform: translate(35px, 0);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
}

@keyframes combineFromBottomLeft {
  0% {
    transform: translate(-200px, 160px) scale(1);
    background: linear-gradient(135deg, #cd7f32, #b87333);
  }
  50% {
    transform: translate(-80px, 80px) scale(1.1);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  100% {
    transform: translate(70px, 0);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
}

@keyframes combineFromBottomRight {
  0% {
    transform: translate(200px, 160px) scale(1);
    background: linear-gradient(135deg, #8b4513, #a0522d);
  }
  50% {
    transform: translate(80px, 80px) scale(1.1);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
  100% {
    transform: translate(105px, 0);
    background: linear-gradient(135deg, #ffd700, #ffed4e);
  }
}

/* 硬币字母 */
.coin-letter {
  font-size: 20px;
  font-weight: bold;
  color: #8b4513;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
  font-family: 'Times New Roman', serif;
  transition: opacity 0.3s ease;
}

/* 登录表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* 输入组 */
.login-card .input-group {
  position: relative;
  display: flex;
  align-items: center;
  background: white;
  border-radius: 14px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
  width: 100% !important;
  max-width: 280px !important;
  margin: 0 auto !important;
}

.input-group:focus-within {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
  transform: translateY(-1px);
}

/* 输入图标 */
.input-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  color: #6c757d;
  font-size: 17px;
  transition: color 0.3s ease;
}

.input-group:focus-within .input-icon {
  color: #007bff;
}

/* 输入框 */
.form-input,
.form-select {
  flex: 1;
  height: 48px;
  background: transparent;
  border: none;
  outline: none;
  color: #495057;
  font-size: 15px;
  padding: 0 18px 0 0;
  font-weight: 500;
}

.form-input::placeholder {
  color: #adb5bd;
}

.form-select {
  cursor: pointer;
  /* 强制显示下拉箭头和滚动条 */
  appearance: auto;
  -webkit-appearance: menulist;
  -moz-appearance: menulist;
  /* 确保有足够的高度来显示下拉选项 */
  min-height: 48px;
}

/* 下拉选项样式 */
.form-select option {
  background: white;
  color: #495057;
  padding: 8px 12px;
  font-size: 14px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.form-select option:hover {
  background: #f8f9fa;
}

.form-select option:checked {
  background: #007bff;
  color: white;
}

/* 登录按钮 */
.login-card .login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 50px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  width: 100% !important;
  max-width: 280px !important;
  margin: 0 auto !important;
  border: none;
  border-radius: 16px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 10px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #0056b3, #004085);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.login-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(0, 123, 255, 0.2);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.login-btn.loading {
  position: relative;
  color: transparent;
}

.login-btn.loading::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (min-width: 1200px) {
  .login-container {
    max-width: 420px;
  }
  
  .login-card .input-group,
  .login-card .login-btn {
    max-width: 320px;
  }
}

@media (max-width: 768px) {
  .login-container {
    max-width: 320px;
    padding: 0 15px;
  }
  
  .login-card .input-group,
  .login-card .login-btn {
    max-width: 260px;
  }
  
  .title-main {
    font-size: 22px;
  }
  
  .login-card {
    padding: 28px 18px;
    border-radius: 18px;
  }
  
  .logo-section {
    height: auto;
    min-height: 90px;
  }
  
  .coins-stack {
    width: 45px;
    height: 45px;
  }
  
  .coin {
    width: 40px;
    height: 40px;
  }
  
  .coin-letter {
    font-size: 16px;
  }
  
  .input-group {
    border-radius: 12px;
  }
  
  .input-icon {
    width: 44px;
    height: 44px;
    font-size: 15px;
  }
  
  .form-input,
  .form-select,
  .login-btn {
    height: 44px;
    font-size: 14px;
  }
  
  .login-btn {
    border-radius: 14px;
  }
}

@media (max-width: 480px) {
  .login-container {
    max-width: 280px;
    padding: 0 10px;
  }
  
  .title-main {
    font-size: 18px;
  }
  
  .login-card {
    padding: 24px 16px;
    border-radius: 16px;
  }
  
  .logo-section {
    height: auto;
    min-height: 80px;
  }
  
  .coins-stack {
    width: 35px;
    height: 35px;
  }
  
  .coin {
    width: 30px;
    height: 30px;
  }
  
  .coin-letter {
    font-size: 12px;
  }
  
  .input-icon {
    width: 40px;
    height: 40px;
    font-size: 14px;
  }
  
  .form-input,
  .form-select,
  .login-btn {
    height: 40px;
    font-size: 14px;
  }
  
  .login-btn {
    border-radius: 12px;
  }
}

@media (max-width: 360px) {
  .login-container {
    max-width: 260px;
    padding: 0 8px;
  }
  
  .login-card {
    padding: 20px 15px;
  }
  
  .title-main {
    font-size: 16px;
  }
  
  .login-card .input-group,
  .login-card .login-btn {
    width: 95%;
  }
}

/* 加载状态 */
.input-group.loading {
  opacity: 0.7;
}

/* 错误状态 */
.input-group.error {
  border-color: #dc3545;
  background: rgba(220, 53, 69, 0.02);
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 12px;
  color: #dc3545;
  font-size: 14px;
  font-weight: 500;
  max-width: 280px;
  margin: 0 auto;
  text-align: left;
  animation: slideIn 0.3s ease-out;
  flex-direction: column;
}

.error-message svg {
  flex-shrink: 0;
  font-size: 16px;
}

.retry-btn {
  margin-top: 8px;
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.retry-btn:hover {
  background: #0056b3;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

