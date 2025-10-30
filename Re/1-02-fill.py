# Retry: fix f-string issue by building HTML with format() instead of nested f-string containing backslashes.

import fitz  # PyMuPDF
import os

pdf_path = "/mnt/data/1-02-fill.pdf"
doc = fitz.open(pdf_path)

out_imgs = []
for i, page in enumerate(doc):
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_path = f"/mnt/data/1-02-fill-page{i+1}.png"
    pix.save(img_path)
    out_imgs.append(img_path)

overlay_items_page1 = [
    {"text":"与财产相关的交易报告表（表格 反洗钱办 1-02）", "left":6, "top":3.5, "size":18, "bold":True},
    {"text":"机构：__________ 分支：__________ 佛历年：______ 报告顺序号（后两位）：__", "left":55, "top":4.5, "size":12},
    {"text":"部分 1. 交易人", "left":6, "top":15.0, "size":16, "bold":True},
    {"text":"1.1 姓名", "left":7, "top":20.8, "size":12},
    {"text":"☑ 本人办理（如有共同交易人，请在第2部分填写）", "left":45, "top":20.6, "size":12},
    {"text":"☑ 代他人办理（请在第2部分填写委托人/授权人信息）", "left":45, "top":22.4, "size":12},
    {"text":"1.2 地址 _______________________   电话 ________   传真 ________", "left":7, "top":28.8, "size":12},
    {"text":"1.3 职业 ____________ 单位 ____________ 电话 ____________", "left":7, "top":33.8, "size":12},
    {"text":"1.4 便捷联系地址 __________________  电话 ________  传真 ________", "left":7, "top":38.5, "size":12},
    {"text":"1.5 交易所用证件：身份证/公务员证/国企员工证｜护照｜外国人身份证明｜其他（请注明）", "left":7, "top":43.0, "size":12},
    {"text":"证件号 ________  签发机关 ________  签发日期 ________  到期日 ________", "left":7, "top":45.0, "size":12},
    {"text":"部分 2. 共同交易人 / 委托人 / 授权人", "left":6, "top":51.7, "size":16, "bold":True},
    {"text":"2.1 姓名（请选择：共同交易人｜委托人｜授权人）", "left":7, "top":56.7, "size":12},
    {"text":"（个人：填写身份证号；法人：填写纳税人识别号；外籍：填写护照或其他身份证明号）", "left":7, "top":58.4, "size":12},
    {"text":"2.2 地址/所在地 __________________  电话 ________  传真 ________", "left":7, "top":62.7, "size":12},
    {"text":"2.3 职业/经营类型 ________  单位 ________  电话 ________", "left":7, "top":67.1, "size":12},
    {"text":"2.4 便捷联系地址 __________________  电话 ________  传真 ________", "left":7, "top":71.5, "size":12},
    {"text":"2.5 交易所用证件：身份证/公务员证/国企员工证｜护照｜外国人身份证明｜登记证明（注册官≤1个月）｜其他（请注明）", "left":7, "top":75.6, "size":12},
    {"text":"证件号 ________  签发机关 ________  签发日期 ________  到期日 ________", "left":7, "top":77.6, "size":12},
    {"text":"部分 3. 与交易有关的事实", "left":6, "top":82.0, "size":16, "bold":True},
    {"text":"交易日期：____ 月 ____ 佛历年", "left":65, "top":82.0, "size":12},
    {"text":"3.1 交易类型：抵押｜典当｜汇款｜其他（请注明）", "left":7, "top":85.5, "size":12},
    {"text":"3.2 资产类型：土地｜土地及建筑物｜建筑物｜其他（请注明）", "left":7, "top":87.5, "size":12},
    {"text":"（请填写资产详细信息）", "left":7, "top":89.1, "size":12},
    {"text":"3.3 交易资产总价值：________ 泰铢（金额大写：________________）", "left":7, "top":91.3, "size":12},
    {"text":"（如为外币，请注明数量与币种）", "left":7, "top":92.8, "size":12},
    {"text":"3.4 交易账户：账号 ________  账户名 ________  账户所有人 ________", "left":7, "top":94.7, "size":12},
    {"text":"3.5 关联账户（如有）：账号 ________  账户名 ________  账户所有人 ________  关系 ________", "left":7, "top":96.3, "size":12},
    {"text":"3.6 交易受益人（如有） ____________________", "left":7, "top":97.8, "size":12},
    {"text":"部分 4.", "left":6, "top":99.0, "size":16, "bold":True},
]

page2_text = (
"— 术语说明 —\n"
"1) “与财产相关的交易”系指在金融机构办理的、以财产为基础的各类法律行为、合同或操作。\n"
"2) “财产”包括动产与不动产（依泰国《民商法典》）。\n"
"3) “交易人”指到金融机构实际办理交易的个人/主体。\n"
"4) “委托人”指委托他人代为办理交易的个人/主体，无论是否具有书面委托书。\n"
"5) “授权人”指以书面授权书委托他人代为办理交易的个人/主体。若为法人，授权书须有法定代表人签字并加盖公章。\n"
"6) “报告人”指在金融机构内负责受理并按规定提交报告的工作人员。\n\n"
"— 填表指引 —\n"
"1) 凡与财产相关之交易，金额“自 500 万泰铢起”，须填写本报告。首次填报勾选“主报告”；若需更正/补充，请勾选“更正/补充报告”，并注明第几次及报告日期。\n"
"2) 若表内空白不足或需补充说明，可另附 A4 纸，并在首页“附件共____页”处注明总页数。\n"
"3) 第1部分（交易人）：\n"
"   1.1 填写姓名。若为泰籍自然人，请在右侧填写身份证号；外籍人员请填写护照或其他身份证明号。\n"
"       - 本人办理：勾选“本人办理”。若有共同交易人，请在第2部分填写其信息。\n"
"       - 代他人办理：勾选“代他人办理”，并在第2部分填写委托人/授权人信息。\n"
"   1.2 填写户籍地址或在泰居住地址及联系电话/传真。\n"
"   1.3 填写职业、工作单位及联系电话。\n"
"   1.4 如方便联系地址不同，请另填联系地址及联系电话/传真。\n"
"   1.5 勾选用于办理的证件类型，并填写证件号、签发机关、签发日期及到期日。\n"
"4) 第2部分（共同交易人/委托人/授权人）：\n"
"   2.1 填写姓名，并在其后勾选身份（共同交易人/委托人/授权人）。\n"
"       自然人填写身份证号；法人填写纳税人识别号；外籍填写护照或其他身份证明号。\n"
"   2.2 填写地址（法人填注册地址）及联系电话/传真。\n"
"   2.3 自然人填职业、单位及电话；法人仅填经营类型（如：建材销售、会计审计公司等）。\n"
"   2.4 如方便联系地址不同，请另填联系地址及联系电话/传真。\n"
"   2.5 勾选证件类型并填写证件详情（登记证明须为注册官签发且不超过1个月）。\n"
"5) 第3部分（与交易有关的事实）：\n"
"   3.1 勾选交易类型；如不在列，请在“其他”栏注明。\n"
"   3.2 勾选资产类型；如不在列，请在“其他”栏注明，并填写资产详情。\n"
"   3.3 填写交易资产金额；如为外币，请注明金额与币种，并在右侧以大写填写金额。\n"
"   3.4 如涉及该金融机构账户，请填写交易所用账户号码。\n"
"   3.5 如涉及其他关联账户，请填写其账号等信息及与本交易之关系。\n"
"   3.6 如有受益人，请填其姓名（例如：抵押财产之受益人、汇款之收款受益人等）。\n"
"   3.7 写明交易目的（例：以土地作抵押申请贷款等）。\n"
"6) 第4部分（签署）：\n"
"   ① 交易人签名；若由记录人代填，则记录人签名并正楷注明姓名，同时在右上角填写记录日期（年/月/日）。\n"
"   ② 金融机构报告责任人签名，并正楷注明姓名，同时在右上角填写报告日期（年/月/日）。\n\n"
"— 备注 —\n"
"1) 要求交易人作为事实记录人的条款，依据《反洗钱法》（B.E. 2542）第13、14、17、21条。\n"
"2) 就本报告之诚实申报而致第三人受损者，报告人依法不承担责任（依据第19条）。\n"
"3) 虚假申报或隐瞒应告知事项者，处不超过2年监禁或罚款5万至50万泰铢，或两者并罚。\n"
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
<title>1-02 中文叠加预览</title>
<style>
  body{{margin:0;background:#f6f7fb;font-family:"Noto Sans SC","Microsoft YaHei","PingFang SC",Arial,Helvetica,sans-serif;}}
  .wrap{{max-width:1100px;margin:24px auto;padding:12px;}}
  .tip{{background:#fff;border:1px solid #e6e8f0;border-radius:12px;padding:12px 16px;line-height:1.6;box-shadow:0 2px 6px rgba(0,0,0,.04);}}
  .page{{position:relative;margin:18px 0;box-shadow:0 4px 16px rgba(0,0,0,.08);}}
  .page img{{width:100%;display:block; vertical-align:middle;}}
  .overlay{{position:absolute; left:0; top:0; width:100%; height:100%; pointer-events:none;}}
  .label{{position:absolute; background:rgba(255,255,255,.84); padding:2px 6px; border-radius:6px; line-height:1.25; box-shadow:0 1px 3px rgba(0,0,0,.06);}}
  .h{{font-weight:700;}}
  .page-title{{font-size:18px; margin:0 0 6px;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="tip">
    <p class="page-title">已生成“中文叠加”预览：保持原版版式不变，以原表作为背景，在相同位置覆盖中文标签。</p>
    <ul>
      <li>第1页：表单区中文标签已对齐主要栏目与字段（如“部分1/2/3”等）。</li>
      <li>第2页：将说明文字整体译为中文并放入整页文本区。</li>
      <li>如需微调，请在页面截图上标注希望的位置，我可继续精确对齐。</li>
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
      <div class="label" style="left:5%; top:6%; width:88%; font-size:14px; background:rgba(255,255,255,.92); padding:12px; white-space:pre-wrap;">{page2_text}</div>
    </div>
  </div>
</div>
</body>
</html>
"""

html = html_template.format(
    page1_img=out_imgs[0],
    page2_img=out_imgs[1],
    overlay1=build_overlay_divs(overlay_items_page1),
    page2_text=page2_text
)

html_path = "/mnt/data/1-02-fill-zh-overlay.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

html_path
