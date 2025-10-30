# Generate Chinese overlay HTML for /mnt/data/1-01-fill.pdf while preserving original layout as background.
import fitz  # PyMuPDF

pdf_path = "/mnt/data/1-01-fill.pdf"
doc = fitz.open(pdf_path)

# Render each page to PNG at 2x for clarity
out_imgs = []
for i, page in enumerate(doc):
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_path = f"/mnt/data/1-01-fill-page{i+1}.png"
    pix.save(img_path)
    out_imgs.append(img_path)

# --- Overlay content (percent positioning) ---
# Page 1 main headings and sections
overlay_items_page1 = [
    # Header
    {"text":"现金交易报告（表格 反洗钱办 1-01）", "left":6, "top":3.4, "size":18, "bold":True},
    {"text":"机构：__________ 分支：__________ 佛历年：______ 报告顺序号（后两位）：__", "left":55, "top":4.6, "size":12},
    {"text":"（请在所选项目前打 ✔ ，并按要求逐项填写）", "left":6, "top":7.0, "size":12},
    {"text":"☑ 主报告    ☑ 更正/补充报告  第____次   填报日期：____/____/____", "left":6, "top":8.8, "size":12},
    {"text":"附件合计：________ 张", "left":78, "top":8.8, "size":12},
    # Section 1
    {"text":"部分 1. 交易人", "left":6, "top":13.2, "size":16, "bold":True},
    {"text":"1.1 姓名", "left":7, "top":17.7, "size":12},
    {"text":"☑ 本人办理（如有共同交易人，请在第2部分填写）", "left":48, "top":17.5, "size":12},
    {"text":"☑ 代他人办理（请在第2部分填写委托人/授权人信息）", "left":48, "top":19.2, "size":12},
    {"text":"（右侧：若为泰籍填身份证号；法人填纳税人识别号；外籍填护照/其他身份证明号）", "left":48, "top":21.0, "size":11},
    {"text":"1.2 地址 _________________________   电话 ________   传真 ________", "left":7, "top":24.2, "size":12},
    {"text":"1.3 职业 ____________ 单位 ____________ 电话 ____________", "left":7, "top":28.2, "size":12},
    {"text":"1.4 便捷联系地址 __________________  电话 ________  传真 ________", "left":7, "top":32.2, "size":12},
    {"text":"1.5 办理所用证件：身份证/公务员证/国企员工证｜护照｜外国人身份证明｜其他（请注明）", "left":7, "top":36.0, "size":12},
    {"text":"证件号 ________  签发机关 ________  签发日期 ________  到期日 ________", "left":7, "top":38.0, "size":12},
    # Section 2
    {"text":"部分 2. 共同交易人 / 委托人 / 授权人", "left":6, "top":43.2, "size":16, "bold":True},
    {"text":"2.1 姓名（请选择：共同交易人｜委托人｜授权人）", "left":7, "top":47.6, "size":12},
    {"text":"（个人：填身份证号；法人：填纳税人识别号；外籍：填护照或其他身份证明号）", "left":7, "top":49.4, "size":12},
    {"text":"2.2 地址/所在地 __________________  电话 ________  传真 ________", "left":7, "top":53.6, "size":12},
    {"text":"2.3 职业/经营类型 ________  单位 ________  电话 ________", "left":7, "top":58.0, "size":12},
    {"text":"2.4 便捷联系地址 __________________  电话 ________  传真 ________", "left":7, "top":62.2, "size":12},
    {"text":"2.5 办理所用证件：身份证/公务员证/国企员工证｜护照｜外国人身份证明｜登记证明（注册官≤1个月）｜其他（请注明）", "left":7, "top":66.2, "size":12},
    {"text":"证件号 ________  签发机关 ________  签发日期 ________  到期日 ________", "left":7, "top":68.3, "size":12},
    # Section 3
    {"text":"部分 3. 与交易有关的事实（右上角填写交易日期：____ 月 ____ 佛历年）", "left":6, "top":72.6, "size":14, "bold":True},
    {"text":"左侧（本机构“入账”/收现金）：", "left":7, "top":75.0, "size":12},
    {"text":"— 存入账户（账号：________；如多账户，请在“相关账户”注明）", "left":7, "top":76.6, "size":12},
    {"text":"— 以现金购买金融票据：支票｜汇票（DRAFT）｜其他（请注明）", "left":7, "top":78.3, "size":12},
    {"text":"— 购买外币（请注明币种）｜其他（请注明）", "left":7, "top":80.0, "size":12},
    {"text":"合计金额（泰铢）：________   金额大写：__________________", "left":7, "top":82.0, "size":12},
    {"text":"相关账户（如有）：__________________", "left":7, "top":83.6, "size":12},
    {"text":"右侧（本机构“出账”/付现金）：", "left":54, "top":75.0, "size":12},
    {"text":"— 从账户提取现金（账号：________；如多账户，请在“相关账户”注明）", "left":54, "top":76.6, "size":12},
    {"text":"— 以现金出售金融票据：支票｜汇票（DRAFT）｜其他（请注明）", "left":54, "top":78.3, "size":12},
    {"text":"— 出售外币（请注明币种）｜其他（请注明）", "left":54, "top":80.0, "size":12},
    {"text":"合计金额（泰铢）：________   金额大写：__________________", "left":54, "top":82.0, "size":12},
    {"text":"相关账户（如有）：__________________", "left":54, "top":83.6, "size":12},
    {"text":"3.2 交易受益人（如有）：__________________", "left":7, "top":86.6, "size":12},
    {"text":"3.3 交易目的：______________________________________________", "left":7, "top":88.4, "size":12},
    # Section 4 & sign
    {"text":"部分 4. 签署", "left":6, "top":91.8, "size":14, "bold":True},
    {"text":"☑ 金融机构为事实记录人（记录日期：____/____/____）   ☑ 客户未签名", "left":6, "top":93.6, "size":12},
    {"text":"交易人/事实记录人签名（签名）", "left":6, "top":96.0, "size":12},
    {"text":"报告人签名（签名）", "left":54, "top":96.0, "size":12},
]

# Page 2 explanatory translation
page2_text = (
"— 术语与定义 —\n"
"1) “现金交易”：指在金融机构办理、以现金进行的各类法律行为、合同或操作。\n"
"2) “现金”：指依法可用于清偿债务的法定纸币与硬币。\n"
"3) “交易人”：指与金融机构办理业务之人。\n"
"4) “委托人”：指委托他人代为办理交易之人，无论是否具书面委托。\n"
"5) “授权人”：指以书面授权委托他人代为办理交易之人；如为法人，授权书须由法定代表人签字并加盖公章。\n"
"6) “报告人”：指金融机构内负责接收并按规定提交报告的工作人员。\n\n"
"— 填表说明（现金交易报告） —\n"
"1) 当发生“自 200 万泰铢起”的现金交易时，应填写本表并勾选“主报告”；若为更正/补充，请勾选“更正/补充报告”，并注明次数与日期。\n"
"2) 若表格空白不足或需补充说明，可另附 A4 纸，并在首页“附件合计”处注明总张数。\n"
"3) 第1部分（交易人）：\n"
"   1.1 填写姓名并在右侧填写证件/编号（泰籍：身份证号；法人：纳税人识别号；外籍：护照或其他证件号）。\n"
"       - 本人办理：勾选“本人办理”。如有共同交易人，请在第2部分填写。\n"
"       - 代他人办理：勾选“代他人办理”，并在第2部分填写委托/授权信息。\n"
"   1.2 填写户籍或在泰地址与联系电话/传真。\n"
"   1.3 填写职业、工作单位与联系电话。\n"
"   1.4 如方便联系地址不同，请另填地址与联系电话/传真。\n"
"   1.5 勾选办理所用证件类型，并填写证件号、签发机关、签发与到期日期。\n"
"4) 第2部分（共同交易人/委托人/授权人）：按上述口径填写其身份、地址、职业/经营类型、便利联系地址与证件信息。\n"
"5) 第3部分（事实）：\n"
"   3.1 将“入账/本机构收现金”和“出账/本机构付现金”分别填写在左右两侧，包括：\n"
"       — 存取账户（列明账号，涉及多个账号时在“相关账户”注明）。\n"
"       — 现金买/卖金融票据：支票、汇票等。\n"
"       — 买/卖外币时注明币种。\n"
"       并分别填写“合计金额（泰铢）”与“金额大写”。\n"
"   3.2 如有受益人，请写明姓名/主体。\n"
"   3.3 写明交易目的，例如：存款取得利息、取现用于经营、购买支票支付货款等。\n"
"6) 第4部分（签署）：\n"
"   — 交易人签名；若由记录人代填，则记录人签名并正楷写姓名，并在右上角填“记录日期（年/月/日）”。\n"
"   — 报告人签名，并在右上角填“报告日期（年/月/日）”。\n\n"
"— 法律提示 —\n"
"1) 要求交易人作为事实记录人之规定，依据《反洗钱法》（B.E.2542）第13、14、17、21条。\n"
"2) 就本报告之诚实申报而致第三人受损者，报告人依法不承担责任（第19条）。\n"
"3) 虚假申报或隐瞒应报告事项者，处不超过2年监禁或罚款5万至50万泰铢，或两者并罚。\n"
)

def build_overlay_divs(items):
    nodes = []
    for it in items:
        style = f"left:{it['left']}%; top:{it['top']}%; font-size:{it.get('size',12)}px;"
        if it.get("bold"):
            style += " font-weight:700;"
        node = f'<div class="label" style="{style}">{it["text"]}</div>'
        nodes.append(node)
    return "\n".join(nodes)

# Compose HTML
html_template = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>1-01 中文叠加预览</title>
<style>
  body{{margin:0;background:#f6f7fb;font-family:"Noto Sans SC","Microsoft YaHei","PingFang SC",Arial,Helvetica,sans-serif;}}
  .wrap{{max-width:1100px;margin:24px auto;padding:12px;}}
  .tip{{background:#fff;border:1px solid #e6e8f0;border-radius:12px;padding:12px 16px;line-height:1.6;box-shadow:0 2px 6px rgba(0,0,0,.04);}}
  .page{{position:relative;margin:18px 0;box-shadow:0 4px 16px rgba(0,0,0,.08);}}
  .page img{{width:100%;display:block; vertical-align:middle;}}
  .overlay{{position:absolute; left:0; top:0; width:100%; height:100%; pointer-events:none;}}
  .label{{position:absolute; background:rgba(255,255,255,.84); padding:2px 6px; border-radius:6px; line-height:1.25; box-shadow:0 1px 3px rgba(0,0,0,.06);}}
  .page-title{{font-size:18px; margin:0 0 6px;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="tip">
    <p class="page-title">“中文叠加”预览：保持原始版式，将中文标签与说明按相对位置覆盖在原表之上。</p>
    <ul>
      <li>第1页：对齐“部分1/2/3/4”与主要字段（姓名、地址、证件、金额、账户、受益人、目的等）。</li>
      <li>第2页：提供对应的术语定义与填表说明（中文），便于对照原文理解。</li>
      <li>如需像素级微调，请在截图上标注目标位置，我会再精确对齐。</li>
    </ul>
  </div>

  <!-- Page 1 -->
  <div class="page">
    <img src="{page1_img}" alt="page 1">
    <div class="overlay">
      {overlay1}
    </div>
  </div>

  <!-- Page 2 -->
  <div class="page">
    <img src="{page2_img}" alt="page 2">
    <div class="overlay">
      <div class="label" style="left:6%; top:6%; width:88%; font-size:14px; background:rgba(255,255,255,.92); padding:12px; white-space:pre-wrap;">{page2_text}</div>
    </div>
  </div>
</div>
</body>
</html>
"""

overlay1 = build_overlay_divs(overlay_items_page1)
page1_img = out_imgs[0] if len(out_imgs) >= 1 else ""
page2_img = out_imgs[1] if len(out_imgs) >= 2 else out_imgs[0]

html = html_template.format(
    page1_img=page1_img,
    page2_img=page2_img,
    overlay1=overlay1,
    page2_text=page2_text
)

html_path = "/mnt/data/1-01-fill-zh-overlay.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

html_path
