<template>
  <div class="container">
    <h2 class="mb-4">交款功能</h2>
    
    <div class="row">
      <div class="col-md-8">
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">交款信息</h5>
          </div>
          <div class="card-body">
            <div v-if="!showConfirmation">
              <form @submit.prevent="handleSubmit">
                <div class="row mb-3">
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label for="currency-select" class="form-label">交款币种</label>
                      <div class="d-flex align-items-center">
                        <select 
                          id="currency-select"
                          class="form-select"
                          v-model="currency"
                        >
                          <option v-for="curr in currencies" :key="curr.code" :value="curr.code">
                            {{ curr.name }} ({{ curr.code }})
                          </option>
                        </select>
                        <CurrencyFlag 
                          v-if="currency"
                          :code="currency"
                          class="ms-2"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label for="current-balance" class="form-label">当前余额</label>
                      <input
                        type="text"
                        id="current-balance"
                        class="form-control"
                        :value="getCurrentBalance()"
                        readonly
                      />
                    </div>
                  </div>
                </div>
                
                <div class="row mb-3">
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label for="payment-amount" class="form-label">交款金额</label>
                      <div class="input-group">
                        <input
                          type="number"
                          id="payment-amount"
                          class="form-control"
                          placeholder="输入交款金额"
                          v-model="amount"
                          required
                        />
                        <span class="input-group-text">{{ currency }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label for="receiver" class="form-label">收款人</label>
                      <input
                        type="text"
                        id="receiver"
                        class="form-control"
                        placeholder="输入收款人姓名"
                        v-model="receiver"
                        required
                      />
                    </div>
                  </div>
                </div>
                
                <div class="mb-3">
                  <label for="remarks" class="form-label">备注</label>
                  <textarea
                    id="remarks"
                    class="form-control"
                    rows="3"
                    placeholder="输入备注信息（可选）"
                    v-model="remarks"
                  ></textarea>
                </div>
                
                <div class="d-flex justify-content-end mt-4">
                  <button type="submit" class="btn btn-primary">
                    <font-awesome-icon :icon="['fas', 'save']" class="me-2" />
                    确认交款
                  </button>
                </div>
              </form>
            </div>
            
            <div v-else>
              <h4 class="mb-4 text-center">交款确认</h4>
              
              <table class="table table-bordered">
                <tbody>
                  <tr>
                    <th style="width: 30%">交款币种</th>
                    <td>{{ getCurrencyFlag(currency) }} {{ currency }}</td>
                  </tr>
                  <tr>
                    <th>交款金额</th>
                    <td>{{ parseFloat(amount).toFixed(2) }} {{ currency }}</td>
                  </tr>
                  <tr>
                    <th>交款日期</th>
                    <td>{{ getCurrentDate() }}</td>
                  </tr>
                  <tr>
                    <th>交款人</th>
                    <td>admin</td>
                  </tr>
                  <tr>
                    <th>收款人</th>
                    <td>{{ receiver }}</td>
                  </tr>
                  <tr v-if="remarks">
                    <th>备注</th>
                    <td>{{ remarks }}</td>
                  </tr>
                </tbody>
              </table>
              
              <div class="d-flex justify-content-center mt-4">
                <button class="btn btn-secondary me-3" @click="handleCancel">
                  <font-awesome-icon :icon="['fas', 'times']" class="me-2" />
                  取消
                </button>
                <button class="btn btn-success me-3" @click="handleConfirm">
                  <font-awesome-icon :icon="['fas', 'save']" class="me-2" />
                  确认
                </button>
                <button class="btn btn-info" @click="handlePrint">
                  <font-awesome-icon :icon="['fas', 'print']" class="me-2" />
                  打印交款单
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-4">
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">交款说明</h5>
          </div>
          <div class="card-body">
            <p>交款功能用于网点将外币交至上级机构，完成交款后网点对应币种余额将减少。</p>
            <hr />
            <h6>操作步骤：</h6>
            <ol>
              <li>选择需要交款的币种</li>
              <li>输入交款金额</li>
              <li>填写收款人信息</li>
              <li>添加备注（可选）</li>
              <li>点击"确认交款"按钮</li>
              <li>确认交款信息无误后，点击"确认"</li>
              <li>可选择打印交款单</li>
            </ol>
            <hr />
            <p class="mb-0 text-danger">注意：交款操作不可撤销，请确认信息无误后再提交。</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue'

export default {
  name: 'CashHandoverView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      currency: 'USD',
      amount: '',
      receiver: '',
      remarks: '',
      showConfirmation: false,
      
      // 模拟币种数据
      currencies: [
        { code: 'USD', name: '美元', flag: '🇺🇸', balance: '50,000.00' },
        { code: 'EUR', name: '欧元', flag: '🇪🇺', balance: '30,000.00' },
        { code: 'GBP', name: '英镑', flag: '🇬🇧', balance: '20,000.00' },
        { code: 'JPY', name: '日元', flag: '🇯🇵', balance: '1,000,000.00' },
        { code: 'HKD', name: '港币', flag: '🇭🇰', balance: '5,000.00' },
        { code: 'THB', name: '泰铢', flag: '🇹🇭', balance: '100,000.00' },
      ]
    };
  },
  methods: {
    getCurrencyFlag(code) {
      const currency = this.currencies.find(c => c.code === code);
      return currency ? currency.flag : '';
    },
    getCurrentBalance() {
      const currency = this.currencies.find(c => c.code === this.currency);
      return currency ? currency.balance : '';
    },
    getCurrentDate() {
      return new Date().toLocaleDateString('zh-CN');
    },
    handleSubmit() {
      if (!this.amount || parseFloat(this.amount) <= 0 || !this.receiver) {
        alert('请填写完整的交款信息');
        return;
      }
      this.showConfirmation = true;
    },
    handleConfirm() {
      // 模拟交款确认
      alert('交款成功！');
      this.showConfirmation = false;
      this.amount = '';
      this.remarks = '';
    },
    handleCancel() {
      this.showConfirmation = false;
    },
    handlePrint() {
      alert('正在打印交款单...');
    }
  }
};
</script>

<style scoped>
.currency-flag {
  width: 24px;
  height: 16px;
  object-fit: cover;
  border-radius: 2px;
  border: 1px solid #ddd;
}
</style>
