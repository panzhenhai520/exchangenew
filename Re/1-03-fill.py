# Render the uploaded PDF (/mnt/data/1-03-fill.pdf) to page images
# and create an HTML overlay that places Chinese translations at the same relative positions.
import fitz  # PyMuPDF
import os

pdf_path = "/mnt/data/1-03-fill.pdf"
doc = fitz.open(pdf_path)

out_imgs = []
for i, page in enumerate(doc):
    # 2x scale for clarity
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_path = f"/mnt/data/1-03-fill-page{i+1}.png"
    pix.save(img_path)
    out_imgs.append(img_path)

# Overlay items for page 1 (positions in percentages)
overlay_items_page1 = [
    # Header & meta
    {"text":"可疑交易报告（表格 反洗钱办 1-03）", "left":6, "top":3.5, "size":18, "bold":True},
    {"text":"机构：__________ 分支：__________ 佛历年：______ 报告顺序号（后两位）：__", "left":55, "top":4.5, "size":12},
    {"text":"（请在所选项目前打 ✔ 并按要求逐项填写）", "left":6, "top":7.0, "size":12},
    {"text":"☑ 主报告    ☑ 更正/补充报告  第____次   填报日期：____/____/____", "left":6, "top":9.0, "size":12},
    {"text":"附件合计：________ 张", "left":78, "top":9.0, "size":12},
    # Section 1
    {"text":"部分 1. 交易人", "left":6, "top":13.8, "size":16, "bold":True},
    {"text":"1.1 姓名", "left":7, "top":18.5, "size":12},
    {"text":"☑ 本人办理（如有共同交易人，请在第2部分填写）", "left":7, "top":21.0, "size":12},
    {"text":"☑ 代他人办理（请在第2部分填写委托人/授权人信息）", "left":7, "top":22.8, "size":12},
    {"text":"1.2 地址 _________________________   电话 ________   传真 ________", "left":7, "top":26.4, "size":12},
    {"text":"1.3 职业 ____________ 单位 ____________ 电话 ____________", "left":7, "top":30.4, "size":12},
    {"text":"1.4 便捷联系地址 __________________  电话 ________  传真 ________", "left":7, "top":34.4, "size":12},
    {"text":"1.5 办理所用证件：身份证/公务员证/国企员工证｜护照｜外国人身份证明｜其他（请注明）", "left":7, "top":38.2, "size":12},
    {"text":"证件号 ________  签发机关 ________  签发日期 ________  到期日 ________", "left":7, "top":40.2, "size":12},
    # Section 2
    {"text":"部分 2. 共同交易人 / 委托人 / 授权人", "left":6, "top":45.8, "size":16, "bold":True},
    {"text":"2.1 姓名（请选择：共同交易人｜委托人｜授权人）", "left":7, "top":50.6, "size":12},
    {"text":"（个人：填写身份证号；法人：填写纳税人识别号；外籍：填写护照或其他身份证明号）", "left":7, "top":52.4, "size":12},
    {"text":"2.2 地址/所在地 __________________  电话 ________  传真 ________", "left":7, "top":56.5, "size":12},
    {"text":"2.3 职业/经营类型 ________  单位 ________  电话 ________", "left":7, "top":60.9, "size":12},
    {"text":"2.4 便捷联系地址 __________________  电话 ________  传真 ________", "left":7, "top":65.1, "size":12},
    {"text":"2.5 办理所用证件：身份证/公务员证/国企员工证｜护照｜外国人身份证明｜登记证明（注册官≤1个月）｜其他（请注明）", "left":7, "top":69.2, "size":12},
    {"text":"证件号 ________  签发机关 ________  签发日期 ________  到期日 ________", "left":7, "top":71.2, "size":12},
    # Section 3
    {"text":"部分 3. 与交易有关的事实", "left":6, "top":76.0, "size":16, "bold":True},
    {"text":"交易日期：____ 月 ____ 佛历年", "left":65, "top":76.0, "size":12},
    {"text":"3.1 涉嫌交易金额：________ 泰铢（金额大写：________________）", "left":7, "top":79.6, "size":12},
    {"text":"（如为外币，请注明数量与币种）", "left":7, "top":81.2, "size":12},
    {"text":"3.2 交易类别：☑ 现金类（请具体说明）  ☑ 与财产相关（请具体说明）", "left":7, "top":83.0, "size":12},
    {"text":"3.3 涉及账户（本机构）：账号 ________  账户名 ________  账户所有人 ________", "left":7, "top":86.0, "size":12},
    {"text":"3.4 其他关联账户（如有）：账号 ________  账户名 ________  账户所有人 ________  关联方式 ________", "left":7, "top":88.5, "size":12},
    {"text":"3.5 交易受益人（如有） ____________________", "left":7, "top":90.4, "size":12},
    {"text":"3.6 交易目的 ____________________________________________", "left":7, "top":92.2, "size":12},
    # Section 4
    {"text":"部分 4. 事实记录人签名（记录日期：____/____/____）", "left":6, "top":95.3, "size":12, "bold":True},
    {"text":"（如该交易已按“现金交易/与财产相关交易”报送主报告，则本表仅填写第5部分“可疑原因”，第一页第1-4部分可免填）", "left":6, "top":97.2, "size":11},
]

# Page 2 main areas
overlay_items_page2 = [
    {"text":"— 第 5 部分：可疑原因（请详述具体事由） —", "left":6, "top":6.0, "size":16, "bold":True},
    {"text":"— 第 6 部分：报告人签名（报告日期：____/____/____） —", "left":6, "top":26.0, "size":16, "bold":True},
]

# Page 2 explanatory text (definitions & instructions)
page2_text = (
"【定义】\n"
"1) “可疑交易”：与常态明显不符、经济上缺乏合理性、疑为规避反洗钱法或与重大犯罪相关的交易；可为一次或多次。\n"
"2) “交易人”：与金融机构办理业务之人。\n"
"3) “委托人”：委托他人代为办理交易之人，无论是否具书面委托。\n"
"4) “授权人”：以书面授权委托他人办理交易之人；如为法人，需法定代表人签字并加盖公章。\n"
"5) “报告人”：在金融机构内负责受理并按规定填报本表之工作人员。\n"
"6) 如有共同交易人/委托人/授权人，应在第2部分填写其详细信息。\n\n"
"【填表要点（第3部分）】\n"
"3.1 金额：填写可疑交易金额，并在右侧以中文大写金额注明（如适用）。\n"
"3.2 类型：指明属于“现金类”或“与财产相关”并具体说明类别。\n"
"3.3 账户：填写本机构涉及的交易账户（如从未在本机构开户，则可不填）。\n"
"3.4 关联账户：填写与本次可疑交易关联的其他账户，并说明关联关系（如无可不填）。\n"
"3.5 受益人：如有，请写明最终受益人姓名/主体。\n"
"3.6 目的：说明交易目的（例：支付货款、存入账户等）。\n\n"
"【签署说明】\n"
"4) 事实记录人需手写签名并正楷填写姓名，右上角注明记录日期（年/月/日）。\n"
"6) 报告人（负责上报）手写签名并正楷填写姓名，右上角注明报告日期（年/月/日）。\n\n"
"【附件与已报情形】\n"
"9) 若该交易此前已以“现金交易/与财产相关交易”主报告报送，请在本表首页右上角填写该主报告编号，本表仅需填写第5部分。\n"
"12) 如表内空白不足或需补充说明，请另附 A4 纸，并在“附件合计”处注明总张数。\n\n"
"【法律提示】\n"
"1) 交易人被要求作为事实记录人，依据《反洗钱法》（B.E.2542）第13、14、17、21条。\n"
"2) 就此类报告之诚实申报而导致第三方受损者，报告人依法不承担责任（第19条）。\n"
"3) 对于虚假申报或隐瞒应报告事项者，处不超过2年监禁或罚款5万至50万泰铢，或两者并罚。\n"
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

html_template = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>1-03 中文叠加预览</title>
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
    <p class="page-title">“中文叠加”预览：保持原始版式，将中文提示与字段说明按相对位置覆盖在原表之上。</p>
    <ul>
      <li>第1页：对齐“部分1/2/3/4”与主要字段（姓名、地址、证件、金额、账户、受益人、目的等）。</li>
      <li>第2页：标出“第5部分（可疑原因）”“第6部分（报告人签名）”，并附中文定义/填表说明。</li>
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
      {overlay2}
      <div class="label" style="left:6%; top:34%; width:88%; font-size:14px; background:rgba(255,255,255,.92); padding:12px; white-space:pre-wrap;">{page2_text}</div>
    </div>
  </div>
</div>
</body>
</html>
"""

# Build HTML
overlay1 = build_overlay_divs(overlay_items_page1)
overlay2 = build_overlay_divs(overlay_items_page2)

# Ensure we have two pages; if not, duplicate page 1 image as page 2 fallback to avoid error
page1_img = out_imgs[0] if len(out_imgs) >= 1 else ""
page2_img = out_imgs[1] if len(out_imgs) >= 2 else out_imgs[0]

html = html_template.format(
    page1_img=page1_img,
    page2_img=page2_img,
    overlay1=overlay1,
    overlay2=overlay2,
    page2_text=page2_text
)

html_path = "/mnt/data/1-03-fill-zh-overlay.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

html_path
