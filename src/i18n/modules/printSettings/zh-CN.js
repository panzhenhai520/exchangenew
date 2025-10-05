// printSettings模块 - zh-CN翻译
export default {
  "printSettings": {
    "title": "打印设置管理",
    "subtitle": "配置不同单据类型的打印格式和布局",
    "documentType": "选择单据类型：",
    "layoutSelect": "布局选择",
    "layoutManager": "布局管理",
    "save": "保存设置",
    "saving": "保存中...",
    "documentTypes": {
      "exchange": "兑换业务凭据",
      "reversal": "冲正业务凭据",
      "balance_adjustment": "余额调节凭据",
      "initial_balance": "余额初始化凭据",
      "eod_report": "日结凭据"
    },
    "documentTypesEn": {
      "exchange": "FOREIGN EXCHANGE TRANSACTION RECEIPT",
      "reversal": "TRANSACTION REVERSAL RECEIPT",
      "balance_adjustment": "BALANCE ADJUSTMENT RECEIPT",
      "initial_balance": "BALANCE INITIALIZATION RECEIPT",
      "eod_report": "END OF DAY REPORT"
    },
    "layouts": {
      "table": "表格格式",
      "simple": "简洁格式",
      "compact": "紧凑格式",
      "default": "默认"
    },
    "reset": "初始化单据格式，恢复到出厂状态",
    "panels": {
      "preview": "实时预览",
      "editor": "布局编辑器",
      "settings": "设置面板"
    },
    "elements": {
      "logo": "Logo",
      "title": "标题",
      "subtitle": "副标题",
      "branch": "网点信息",
      "content": "交易内容",
      "signature": "签名区域",
      "watermark": "水印"
    },
    "properties": {
      "xPosition": "X位置 (mm)",
      "yPosition": "Y位置 (mm)",
      "width": "宽度 (mm)",
      "visible": "显示此元素",
      "properties": "属性"
    },
    "sections": {
      "paper": "纸张设置",
      "font": "字体设置",
      "logo": "Logo设置",
      "layout": "布局设置",
      "signature": "签名设置",
      "advanced": "高级设置"
    },
    "paper": {
      "type": "纸张类型",
      "orientation": "纸张方向",
      "portrait": "纵向 (Portrait)",
      "landscape": "横向 (Landscape)",
      "width": "宽度 (mm)",
      "height": "高度 (mm)",
      "margins": "页边距设置 (mm)",
      "top": "上",
      "right": "右",
      "bottom": "下",
      "left": "左"
    },
    "font": {
      "family": "字体族",
      "size": "字体大小",
      "color": "字体颜色"
    },
    "logo": {
      "show": "显示Logo",
      "upload": "点击或拖拽上传Logo",
      "formats": "支持 PNG, JPG, GIF, SVG 格式，最大2MB",
      "change": "更换",
      "delete": "删除",
      "width": "宽度 (px)",
      "height": "高度 (px)"
    },
    "layout": {
      "lineSpacing": "行间距",
      "contentStyle": "内容样式",
      "tableFormat": "表格格式",
      "simpleFormat": "简洁格式",
      "titleAlign": "标题对齐",
      "contentAlign": "内容对齐",
      "left": "左对齐",
      "center": "居中",
      "right": "右对齐",
      "fieldLabelWidth": "字段标签宽度 (%)",
      "showFieldLabels": "显示字段标签",
      "showTableBorder": "显示表格边框"
    },
    "signature": {
      "style": "签名样式",
      "none": "不显示签名区域",
      "single": "单签名框",
      "double": "双签名框",
      "showDateLine": "显示日期线"
    },
    "advanced": {
      "enableWatermark": "启用水印",
      "watermarkText": "水印文字",
      "opacity": "透明度"
    },
    "sample": {
      "transactionNo": "交易编号/No:",
      "transactionDate": "交易日期/Date:",
      "amount": "交易金额/Amount:",
      "exchange": "兑换金额/Exchange:",
      "rate": "交易汇率/Rate:",
      "customerName": "客户姓名/Name:",
      "idNumber": "证件号码/ID:",
      "purpose": "交易用途/Purpose:",
      "remarks": "备注/Remarks:",
      "branchInfo": "示例网点 (001)",
      "signature": "签名/Signature",
      "customer": "客户签名/Customer"
    },
    "tips": {
      "editorTip": "点击选择元素，拖拽调整位置，在右侧面板调整详细属性",
      "paperInfo": "纸张信息：",
      "actualSize": "实际尺寸：",
      "displaySize": "显示尺寸：",
      "scale": "缩放比例：",
      "ratio": "比例："
    },
    "messages": {
      "saveSuccess": "布局设置保存成功",
      "loadSuccess": "设置加载成功",
      "resetSuccess": "打印设置已重置为默认值",
      "logoUploadSuccess": "Logo上传成功",
      "logoDeleteSuccess": "Logo删除成功",
      "saveFailed": "保存打印设置失败",
      "loadFailed": "加载打印设置失败",
      "resetFailed": "重置打印设置失败",
      "invalidFileType": "不支持的文件类型，请上传 PNG, JPG, GIF, BMP 或 SVG 格式的图片",
      "fileTooLarge": "文件大小不能超过2MB",
      "logoUploadFailed": "Logo上传失败",
      "layoutApplied": "布局已应用到主窗口，请在主窗口中保存设置"
    },
    "confirmations": {
      "resetLayout": "确定要重置当前布局的打印设置为默认值吗？",
      "deleteLogo": "确定要删除当前Logo吗？"
    }
  }
}