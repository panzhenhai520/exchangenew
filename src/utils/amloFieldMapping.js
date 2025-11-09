/**
 * AMLO字段映射：数据库字段名 → PDF表单字段名
 *
 * 基于backend的amlo_data_mapper.py实现
 * 用于PDF和编辑面板的双向同步
 *
 * PDF字段命名规则:
 * - fill_1 ~ fill_56: 文本字段
 * - comb_1 ~ comb_6: 身份证号等组合字段（comb fields）
 * - Check Box2 ~ Check Box33: 复选框
 * - left_amount, right_amount: 泰文金额
 * - sig_transactor, sig_reporter: 签名字段
 * - transactor_date, reporter_date: 签名日期
 */

/**
 * AMLO-1-01 (CTR - 现金交易报告) 字段映射
 */
export const AMLO_101_FIELD_MAP = {
  // ===== 报告基本信息 =====
  'report_number': 'fill_52',           // 报告编号
  'report_no': 'fill_52',               // 报告编号（别名）
  'is_amendment_report': 'Check Box3',  // 是否修订报告 (true=修订, false=Check Box2原报告)
  'is_first_report': 'Check Box2',      // 是否首次报告
  'amendment_count': 'fill_3',          // 修订次数
  'amendment_date': 'fill_1',           // 修订日期
  'total_pages': 'fill_2',              // 总页数

  // ===== 第1部分：交易办理人信息 (Maker/Transaction Handler) =====
  'maker_id_number': 'comb_1',          // 身份证号码（13位组合框）
  'maker_full_name': 'fill_4',          // 姓名全称
  'maker_name': 'fill_4',               // 姓名（别名）
  'maker_transaction_by_self': 'Check Box4',    // 本人办理
  'maker_transaction_on_behalf': 'Check Box5',  // 代理办理
  'maker_is_proxy': 'Check Box5',       // 是否代理（别名）
  'maker_address': 'fill_5',            // 地址（第1行）
  'maker_address_line1': 'fill_5',      // 地址第1行（别名）
  'maker_address_line2': 'fill_5_2',    // 地址（第2行）
  'maker_phone': 'fill_7',              // 电话
  'maker_fax': 'fill_8',                // 传真
  'maker_occupation': 'fill_9',         // 职业
  'maker_occupation_employer': 'fill_10', // 工作单位
  'maker_work_phone': 'fill_11',        // 工作单位电话
  'maker_contact_address': 'fill_12',   // 联系地址
  'maker_contact_phone': 'fill_14',     // 联系电话
  'maker_contact_fax': 'fill_15',       // 联系传真

  // 证件类型复选框
  'maker_id_type_id_card': 'Check Box6',      // 身份证
  'maker_id_type_passport': 'Check Box7',     // 护照
  'maker_id_type_alien_cert': 'Check Box8',   // 外国人证
  'maker_id_type_other': 'Check Box9',        // 其他
  'maker_id_type_other_text': 'fill_6',       // 其他类型说明
  'maker_id_issued_by': 'fill_17',            // 签发机构
  'maker_id_issued_date': 'fill_18',          // 签发日期
  'maker_id_expiry_date': 'fill_19',          // 过期日期
  // Note: maker_id_number也映射到fill_16作为证件号码显示

  // ===== 第2部分：共同交易人/代理人信息 (Joint Party) =====
  'has_joint_party': null,              // 仅控制逻辑，无直接PDF字段
  'joint_party_type_joint': 'Check Box10',    // 共同交易人
  'joint_party_type_delegator': 'Check Box11', // 委托人
  'joint_party_type_agent': 'Check Box12',     // 代理人
  'joint_party_id_number': 'comb_2',          // 身份证号码
  'joint_party_name': 'fill_20',              // 姓名
  'joint_party_address': 'fill_21',           // 地址（第1行）
  'joint_party_address_line2': 'fill_22',     // 地址（第2行）
  'joint_party_phone': 'fill_23',             // 电话
  'joint_party_fax': 'fill_24',               // 传真
  'joint_party_occupation': 'fill_25',        // 职业
  'joint_party_employer': 'fill_26',          // 工作单位
  'joint_party_work_phone': 'fill_27',        // 工作单位电话
  'joint_party_business_type': 'fill_28',     // 企业类型（如果是法人）
  'joint_party_contact_address': 'fill_29',   // 联系地址
  'joint_party_contact_phone': 'fill_31',     // 联系电话
  'joint_party_contact_fax': 'fill_32',       // 联系传真

  // 证件类型
  'joint_party_id_type_id_card': 'Check Box13',     // 身份证
  'joint_party_id_type_passport': 'Check Box14',    // 护照
  'joint_party_id_type_alien_cert': 'Check Box15',  // 外国人证
  'joint_party_id_type_registry': 'Check Box16',    // 登记证明
  'joint_party_id_type_other': 'Check Box17',       // 其他
  'joint_party_id_type_other_text': 'fill_56',      // 其他类型说明
  'joint_party_id_issued_by': 'fill_34',            // 签发机构
  'joint_party_id_issued_date': 'fill_35',          // 签发日期
  'joint_party_id_expiry_date': 'fill_36',          // 过期日期
  // Note: joint_party_id_number也映射到fill_33

  // ===== 第3部分：交易信息 (Transaction Information) =====
  'transaction_date_day': 'fill_37',    // 交易日期-日
  'transaction_date_month': 'fill_38',  // 交易日期-月
  'transaction_date_year': 'fill_39',   // 交易日期-年

  // 左栏（机构买入外币/存款）
  'deposit_account': 'comb_3',          // 账号
  'deposit_related_account': 'comb_5',  // 关联账号
  'deposit_thb_amount': 'fill_48',      // 账号行金额（通常为空）
  'deposit_cash': 'Check Box19',        // 现金存款复选框
  'deposit_check': 'Check Box20',       // 支票
  'deposit_draft': 'Check Box21',       // 汇票
  'deposit_other_instrument': 'Check Box22',  // 其他票据
  'deposit_other_text': 'fill_40',      // 其他票据说明
  'deposit_currency_amount': 'fill_48_5', // 买入外币金额
  'deposit_total': 'fill_50',           // 左栏合计
  'left_amount': 'left_amount',         // 泰文金额
  'foreign_currency_buy': 'fill_42',    // 外币代码和金额

  // 右栏（机构卖出外币/取款）
  'withdrawal_account': 'comb_4',       // 账号
  'withdrawal_related_account': 'comb_6', // 关联账号
  'withdrawal_thb_amount': 'fill_49',   // 账号行金额（通常为空）
  'withdrawal_cash': 'Check Box25',     // 现金取款
  'withdrawal_transfer': 'Check Box26', // 转账
  'withdrawal_check': 'Check Box27',    // 支票
  'withdrawal_draft': 'Check Box28',    // 汇票
  'withdrawal_other': 'Check Box29',    // 其他
  'withdrawal_other_text': 'fill_41',   // 其他说明
  'withdrawal_currency_amount': 'fill_49_5', // 卖出外币金额
  'withdrawal_total': 'fill_51',        // 右栏合计
  'right_amount': 'right_amount',       // 泰文金额
  'foreign_currency_sell': 'fill_43',   // 外币代码和金额

  // 交易类型（左栏/右栏各有一组复选框）
  'exchange_buy_currency': 'Check Box23',  // 买外币 (左栏)
  'exchange_sell_currency': 'Check Box30', // 卖外币 (右栏)
  'exchange_other_transaction': 'Check Box31', // 其他交易
  'exchange_other_description': 'fill43_2',    // 其他交易说明

  // 受益人和目的
  'beneficiary_name': 'fill_46',        // 受益人姓名
  'transaction_purpose': 'fill_47',     // 交易目的
  'exchange_purpose': 'fill_47',        // 兑换目的（别名）

  // ===== 第4部分：签名区域 =====
  'institution_records_fact': 'Check Box32',    // 机构记录事实
  'customer_no_signature': 'Check Box33',       // 客户未签名

  // 签名和日期
  'transactor_signature': 'sig_transactor',  // 交易人签名
  'transactor_date': 'transactor_date',      // 交易人签名日期
  'reporter_signature': 'sig_reporter',      // 报告人签名
  'reporter_date': 'reporter_date'           // 报告人签名日期
}

/**
 * 反向映射：PDF字段名 → 数据库字段名
 * 用于从PDF读取值同步到数据库字段
 */
export const PDF_TO_DB_FIELD_MAP = Object.entries(AMLO_101_FIELD_MAP)
  // eslint-disable-next-line no-unused-vars
  .filter(([dbFieldIgnored, pdfField]) => pdfField !== null)
  .reduce((acc, [dbField, pdfField]) => {
    // 如果多个DB字段映射到同一个PDF字段，保留第一个（主要的）
    if (!acc[pdfField]) {
      acc[pdfField] = dbField
    }
    return acc
  }, {})

/**
 * 将数据库字段名转换为PDF字段名
 * @param {string} dbFieldName - 数据库字段名
 * @returns {string|null} PDF字段名，如果没有映射则返回null
 */
export function dbFieldToPdfField(dbFieldName) {
  return AMLO_101_FIELD_MAP[dbFieldName] || null
}

/**
 * 将PDF字段名转换为数据库字段名
 * @param {string} pdfFieldName - PDF字段名
 * @returns {string|null} 数据库字段名，如果没有映射则返回null
 */
export function pdfFieldToDbField(pdfFieldName) {
  return PDF_TO_DB_FIELD_MAP[pdfFieldName] || null
}

/**
 * 批量转换：数据库数据 → PDF数据
 * @param {Object} dbData - 数据库form_data对象
 * @returns {Object} PDF字段值对象
 */
export function dbDataToPdfData(dbData) {
  const pdfData = {}

  for (const [dbField, value] of Object.entries(dbData)) {
    const pdfField = dbFieldToPdfField(dbField)
    if (pdfField) {
      pdfData[pdfField] = value
    } else {
      // 字段没有映射，可能是PDF直接使用的字段名（如fill_1, fill_52等）
      // 保留原字段名
      pdfData[dbField] = value
    }
  }

  return pdfData
}

/**
 * 批量转换：PDF数据 → 数据库数据
 * @param {Object} pdfData - PDF字段值对象
 * @returns {Object} 数据库form_data对象
 */
export function pdfDataToDbData(pdfData) {
  const dbData = {}

  for (const [pdfField, value] of Object.entries(pdfData)) {
    const dbField = pdfFieldToDbField(pdfField)
    if (dbField) {
      dbData[dbField] = value
    } else {
      // 可能是直接使用PDF字段名的字段（如fill_1等）
      // 保留原字段名
      dbData[pdfField] = value
    }
  }

  return dbData
}

/**
 * 获取所有映射的数据库字段名
 * @returns {string[]} 数据库字段名数组
 */
export function getMappedDbFields() {
  return Object.keys(AMLO_101_FIELD_MAP).filter(field => AMLO_101_FIELD_MAP[field] !== null)
}

/**
 * 获取所有映射的PDF字段名
 * @returns {string[]} PDF字段名数组
 */
export function getMappedPdfFields() {
  return Object.values(AMLO_101_FIELD_MAP).filter(field => field !== null)
}

export default {
  AMLO_101_FIELD_MAP,
  PDF_TO_DB_FIELD_MAP,
  dbFieldToPdfField,
  pdfFieldToDbField,
  dbDataToPdfData,
  pdfDataToDbData,
  getMappedDbFields,
  getMappedPdfFields
}
