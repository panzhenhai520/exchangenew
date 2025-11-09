<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
/* 全局样式 */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

/* 防止手机端横向滚动 */
html, body {
  overflow-x: hidden !important;
  max-width: 100% !important;
  width: 100% !important;
  position: relative !important;
  touch-action: pan-y !important;
  -webkit-overflow-scrolling: touch !important;
}

/* 全局防止横向滚动 */
* {
  max-width: 100% !important;
  box-sizing: border-box !important;
}

/* App角色专用样式 */
.app-mobile-layout {
  overflow-x: hidden !important;
  max-width: 100% !important;
  width: 100% !important;
  touch-action: pan-y !important;
}

.app-mobile-layout * {
  max-width: 100% !important;
  box-sizing: border-box !important;
}

/* 修复Bootstrap和FontAwesome的一些样式问题 */
.dropdown-item.active, .dropdown-item:active {
  background-color: #0d6efd;
}

/* 添加国旗样式 */
.currency-flag {
  width: 20px;
  height: 15px;
  display: inline-block;
  margin-right: 5px;
  vertical-align: middle;
}

/* 全局模态窗口响应式宽度控制 */
.modal-dialog {
  max-width: 600px !important;
  width: 90% !important;
}

@media (min-width: 576px) {
  .modal-dialog {
    max-width: 500px !important;
    width: auto !important;
  }
}

@media (min-width: 768px) {
  .modal-dialog {
    max-width: 550px !important;
    width: auto !important;
  }
}

@media (min-width: 992px) {
  .modal-dialog {
    max-width: 600px !important;
    width: auto !important;
  }
}

/* modal-lg 类的响应式控制 */
.modal-dialog.modal-lg {
  max-width: 600px !important;
  width: 90% !important;
}

@media (min-width: 576px) {
  .modal-dialog.modal-lg {
    max-width: 500px !important;
    width: auto !important;
  }
}

@media (min-width: 768px) {
  .modal-dialog.modal-lg {
    max-width: 550px !important;
    width: auto !important;
  }
}

@media (min-width: 992px) {
  .modal-dialog.modal-lg {
    max-width: 600px !important;
    width: auto !important;
  }
}

/* modal-xl 类的响应式控制 */
.modal-dialog.modal-xl {
  max-width: 700px !important;
  width: 90% !important;
}

@media (min-width: 576px) {
  .modal-dialog.modal-xl {
    max-width: 600px !important;
    width: auto !important;
  }
}

@media (min-width: 768px) {
  .modal-dialog.modal-xl {
    max-width: 650px !important;
    width: auto !important;
  }
}

@media (min-width: 992px) {
  .modal-dialog.modal-xl {
    max-width: 700px !important;
    width: auto !important;
  }
}
</style>
