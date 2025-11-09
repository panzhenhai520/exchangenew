# 初始化195个国家数据
from services.db_service import DatabaseService
from models.exchange_models import Country
import logging

logger = logging.getLogger(__name__)

class CountryDataInitializer:
    """国家数据初始化器 - 195个国家的完整数据"""

    # 195个国家的完整列表（ISO 3166-1 alpha-2代码）
    COUNTRIES_DATA = [
        # 亚洲国家
        {'code': 'CN', 'name_zh': '中国', 'name_en': 'China', 'name_th': 'จีน', 'phone': '+86', 'currency': 'CNY'},
        {'code': 'JP', 'name_zh': '日本', 'name_en': 'Japan', 'name_th': 'ญี่ปุ่น', 'phone': '+81', 'currency': 'JPY'},
        {'code': 'KR', 'name_zh': '韩国', 'name_en': 'South Korea', 'name_th': 'เกาหลีใต้', 'phone': '+82', 'currency': 'KRW'},
        {'code': 'TH', 'name_zh': '泰国', 'name_en': 'Thailand', 'name_th': 'ไทย', 'phone': '+66', 'currency': 'THB'},
        {'code': 'VN', 'name_zh': '越南', 'name_en': 'Vietnam', 'name_th': 'เวียดนาม', 'phone': '+84', 'currency': 'VND'},
        {'code': 'SG', 'name_zh': '新加坡', 'name_en': 'Singapore', 'name_th': 'สิงคโปร์', 'phone': '+65', 'currency': 'SGD'},
        {'code': 'MY', 'name_zh': '马来西亚', 'name_en': 'Malaysia', 'name_th': 'มาเลเซีย', 'phone': '+60', 'currency': 'MYR'},
        {'code': 'ID', 'name_zh': '印度尼西亚', 'name_en': 'Indonesia', 'name_th': 'อินโดนีเซีย', 'phone': '+62', 'currency': 'IDR'},
        {'code': 'PH', 'name_zh': '菲律宾', 'name_en': 'Philippines', 'name_th': 'ฟิลิปปินส์', 'phone': '+63', 'currency': 'PHP'},
        {'code': 'IN', 'name_zh': '印度', 'name_en': 'India', 'name_th': 'อินเดีย', 'phone': '+91', 'currency': 'INR'},
        {'code': 'PK', 'name_zh': '巴基斯坦', 'name_en': 'Pakistan', 'name_th': 'ปากีสถาน', 'phone': '+92', 'currency': 'PKR'},
        {'code': 'BD', 'name_zh': '孟加拉国', 'name_en': 'Bangladesh', 'name_th': 'บังกลาเทศ', 'phone': '+880', 'currency': 'BDT'},
        {'code': 'LA', 'name_zh': '老挝', 'name_en': 'Laos', 'name_th': 'ลาว', 'phone': '+856', 'currency': 'LAK'},
        {'code': 'KH', 'name_zh': '柬埔寨', 'name_en': 'Cambodia', 'name_th': 'กัมพูชา', 'phone': '+855', 'currency': 'KHR'},
        {'code': 'MM', 'name_zh': '缅甸', 'name_en': 'Myanmar', 'name_th': 'พม่า', 'phone': '+95', 'currency': 'MMK'},
        {'code': 'BN', 'name_zh': '文莱', 'name_en': 'Brunei', 'name_th': 'บรูไน', 'phone': '+673', 'currency': 'BND'},
        {'code': 'TL', 'name_zh': '东帝汶', 'name_en': 'Timor-Leste', 'name_th': 'ติมอร์-เลสเต', 'phone': '+670', 'currency': 'USD'},
        {'code': 'MN', 'name_zh': '蒙古', 'name_en': 'Mongolia', 'name_th': 'มองโกเลีย', 'phone': '+976', 'currency': 'MNT'},
        {'code': 'KZ', 'name_zh': '哈萨克斯坦', 'name_en': 'Kazakhstan', 'name_th': 'คาซัคสถาน', 'phone': '+7', 'currency': 'KZT'},
        {'code': 'UZ', 'name_zh': '乌兹别克斯坦', 'name_en': 'Uzbekistan', 'name_th': 'อุซเบกิสถาน', 'phone': '+998', 'currency': 'UZS'},

        # 欧洲国家
        {'code': 'GB', 'name_zh': '英国', 'name_en': 'United Kingdom', 'name_th': 'สหราชอาณาจักร', 'phone': '+44', 'currency': 'GBP'},
        {'code': 'FR', 'name_zh': '法国', 'name_en': 'France', 'name_th': 'ฝรั่งเศส', 'phone': '+33', 'currency': 'EUR'},
        {'code': 'DE', 'name_zh': '德国', 'name_en': 'Germany', 'name_th': 'เยอรมนี', 'phone': '+49', 'currency': 'EUR'},
        {'code': 'IT', 'name_zh': '意大利', 'name_en': 'Italy', 'name_th': 'อิตาลี', 'phone': '+39', 'currency': 'EUR'},
        {'code': 'ES', 'name_zh': '西班牙', 'name_en': 'Spain', 'name_th': 'สเปน', 'phone': '+34', 'currency': 'EUR'},
        {'code': 'RU', 'name_zh': '俄罗斯', 'name_en': 'Russia', 'name_th': 'รัสเซีย', 'phone': '+7', 'currency': 'RUB'},
        {'code': 'UA', 'name_zh': '乌克兰', 'name_en': 'Ukraine', 'name_th': 'ยูเครน', 'phone': '+380', 'currency': 'UAH'},
        {'code': 'PL', 'name_zh': '波兰', 'name_en': 'Poland', 'name_th': 'โปแลนด์', 'phone': '+48', 'currency': 'PLN'},
        {'code': 'NL', 'name_zh': '荷兰', 'name_en': 'Netherlands', 'name_th': 'เนเธอร์แลนด์', 'phone': '+31', 'currency': 'EUR'},
        {'code': 'BE', 'name_zh': '比利时', 'name_en': 'Belgium', 'name_th': 'เบลเยียม', 'phone': '+32', 'currency': 'EUR'},
        {'code': 'SE', 'name_zh': '瑞典', 'name_en': 'Sweden', 'name_th': 'สวีเดน', 'phone': '+46', 'currency': 'SEK'},
        {'code': 'NO', 'name_zh': '挪威', 'name_en': 'Norway', 'name_th': 'นอร์เวย์', 'phone': '+47', 'currency': 'NOK'},
        {'code': 'DK', 'name_zh': '丹麦', 'name_en': 'Denmark', 'name_th': 'เดนมาร์ก', 'phone': '+45', 'currency': 'DKK'},
        {'code': 'FI', 'name_zh': '芬兰', 'name_en': 'Finland', 'name_th': 'ฟินแลนด์', 'phone': '+358', 'currency': 'EUR'},
        {'code': 'CH', 'name_zh': '瑞士', 'name_en': 'Switzerland', 'name_th': 'สวิตเซอร์แลนด์', 'phone': '+41', 'currency': 'CHF'},
        {'code': 'AT', 'name_zh': '奥地利', 'name_en': 'Austria', 'name_th': 'ออสเตรีย', 'phone': '+43', 'currency': 'EUR'},
        {'code': 'PT', 'name_zh': '葡萄牙', 'name_en': 'Portugal', 'name_th': 'โปรตุเกส', 'phone': '+351', 'currency': 'EUR'},
        {'code': 'GR', 'name_zh': '希腊', 'name_en': 'Greece', 'name_th': 'กรีซ', 'phone': '+30', 'currency': 'EUR'},
        {'code': 'CZ', 'name_zh': '捷克', 'name_en': 'Czech Republic', 'name_th': 'สาธารณรัฐเช็ก', 'phone': '+420', 'currency': 'CZK'},
        {'code': 'RO', 'name_zh': '罗马尼亚', 'name_en': 'Romania', 'name_th': 'โรมาเนีย', 'phone': '+40', 'currency': 'RON'},

        # 美洲国家
        {'code': 'US', 'name_zh': '美国', 'name_en': 'United States', 'name_th': 'สหรัฐอเมริกา', 'phone': '+1', 'currency': 'USD'},
        {'code': 'CA', 'name_zh': '加拿大', 'name_en': 'Canada', 'name_th': 'แคนาดา', 'phone': '+1', 'currency': 'CAD'},
        {'code': 'BR', 'name_zh': '巴西', 'name_en': 'Brazil', 'name_th': 'บราซิล', 'phone': '+55', 'currency': 'BRL'},
        {'code': 'MX', 'name_zh': '墨西哥', 'name_en': 'Mexico', 'name_th': 'เม็กซิโก', 'phone': '+52', 'currency': 'MXN'},
        {'code': 'AR', 'name_zh': '阿根廷', 'name_en': 'Argentina', 'name_th': 'อาร์เจนตินา', 'phone': '+54', 'currency': 'ARS'},
        {'code': 'CL', 'name_zh': '智利', 'name_en': 'Chile', 'name_th': 'ชิลี', 'phone': '+56', 'currency': 'CLP'},
        {'code': 'CO', 'name_zh': '哥伦比亚', 'name_en': 'Colombia', 'name_th': 'โคลอมเบีย', 'phone': '+57', 'currency': 'COP'},
        {'code': 'PE', 'name_zh': '秘鲁', 'name_en': 'Peru', 'name_th': 'เปรู', 'phone': '+51', 'currency': 'PEN'},
        {'code': 'VE', 'name_zh': '委内瑞拉', 'name_en': 'Venezuela', 'name_th': 'เวเนซุเอลา', 'phone': '+58', 'currency': 'VES'},
        {'code': 'UY', 'name_zh': '乌拉圭', 'name_en': 'Uruguay', 'name_th': 'อุรุกวัย', 'phone': '+598', 'currency': 'UYU'},

        # 大洋洲国家
        {'code': 'AU', 'name_zh': '澳大利亚', 'name_en': 'Australia', 'name_th': 'ออสเตรเลีย', 'phone': '+61', 'currency': 'AUD'},
        {'code': 'NZ', 'name_zh': '新西兰', 'name_en': 'New Zealand', 'name_th': 'นิวซีแลนด์', 'phone': '+64', 'currency': 'NZD'},
        {'code': 'FJ', 'name_zh': '斐济', 'name_en': 'Fiji', 'name_th': 'ฟีจี', 'phone': '+679', 'currency': 'FJD'},
        {'code': 'PG', 'name_zh': '巴布亚新几内亚', 'name_en': 'Papua New Guinea', 'name_th': 'ปาปัวนิวกินี', 'phone': '+675', 'currency': 'PGK'},

        # 非洲国家
        {'code': 'ZA', 'name_zh': '南非', 'name_en': 'South Africa', 'name_th': 'แอฟริกาใต้', 'phone': '+27', 'currency': 'ZAR'},
        {'code': 'EG', 'name_zh': '埃及', 'name_en': 'Egypt', 'name_th': 'อียิปต์', 'phone': '+20', 'currency': 'EGP'},
        {'code': 'NG', 'name_zh': '尼日利亚', 'name_en': 'Nigeria', 'name_th': 'ไนจีเรีย', 'phone': '+234', 'currency': 'NGN'},
        {'code': 'KE', 'name_zh': '肯尼亚', 'name_en': 'Kenya', 'name_th': 'เคนยา', 'phone': '+254', 'currency': 'KES'},
        {'code': 'ET', 'name_zh': '埃塞俄比亚', 'name_en': 'Ethiopia', 'name_th': 'เอธิโอเปีย', 'phone': '+251', 'currency': 'ETB'},
        {'code': 'TZ', 'name_zh': '坦桑尼亚', 'name_en': 'Tanzania', 'name_th': 'แทนซาเนีย', 'phone': '+255', 'currency': 'TZS'},

        # 中东国家
        {'code': 'SA', 'name_zh': '沙特阿拉伯', 'name_en': 'Saudi Arabia', 'name_th': 'ซาอุดีอาระเบีย', 'phone': '+966', 'currency': 'SAR'},
        {'code': 'AE', 'name_zh': '阿联酋', 'name_en': 'United Arab Emirates', 'name_th': 'สหรัฐอาหรับเอมิเรตส์', 'phone': '+971', 'currency': 'AED'},
        {'code': 'IL', 'name_zh': '以色列', 'name_en': 'Israel', 'name_th': 'อิสราเอล', 'phone': '+972', 'currency': 'ILS'},
        {'code': 'TR', 'name_zh': '土耳其', 'name_en': 'Turkey', 'name_th': 'ตุรกี', 'phone': '+90', 'currency': 'TRY'},
        {'code': 'IR', 'name_zh': '伊朗', 'name_en': 'Iran', 'name_th': 'อิหร่าน', 'phone': '+98', 'currency': 'IRR'},
        {'code': 'IQ', 'name_zh': '伊拉克', 'name_en': 'Iraq', 'name_th': 'อิรัก', 'phone': '+964', 'currency': 'IQD'},

        # 其他亚洲国家
        {'code': 'AF', 'name_zh': '阿富汗', 'name_en': 'Afghanistan', 'name_th': 'อัฟกานิสถาน', 'phone': '+93', 'currency': 'AFN'},
        {'code': 'AM', 'name_zh': '亚美尼亚', 'name_en': 'Armenia', 'name_th': 'อาร์เมเนีย', 'phone': '+374', 'currency': 'AMD'},
        {'code': 'AZ', 'name_zh': '阿塞拜疆', 'name_en': 'Azerbaijan', 'name_th': 'อาเซอร์ไบจาน', 'phone': '+994', 'currency': 'AZN'},
        {'code': 'BH', 'name_zh': '巴林', 'name_en': 'Bahrain', 'name_th': 'บาห์เรน', 'phone': '+973', 'currency': 'BHD'},
        {'code': 'BT', 'name_zh': '不丹', 'name_en': 'Bhutan', 'name_th': 'ภูฏาน', 'phone': '+975', 'currency': 'BTN'},
        {'code': 'GE', 'name_zh': '格鲁吉亚', 'name_en': 'Georgia', 'name_th': 'จอร์เจีย', 'phone': '+995', 'currency': 'GEL'},
        {'code': 'JO', 'name_zh': '约旦', 'name_en': 'Jordan', 'name_th': 'จอร์แดน', 'phone': '+962', 'currency': 'JOD'},
        {'code': 'KW', 'name_zh': '科威特', 'name_en': 'Kuwait', 'name_th': 'คูเวต', 'phone': '+965', 'currency': 'KWD'},
        {'code': 'KG', 'name_zh': '吉尔吉斯斯坦', 'name_en': 'Kyrgyzstan', 'name_th': 'คีร์กีซสถาน', 'phone': '+996', 'currency': 'KGS'},
        {'code': 'LB', 'name_zh': '黎巴嫩', 'name_en': 'Lebanon', 'name_th': 'เลบานอน', 'phone': '+961', 'currency': 'LBP'},
        {'code': 'MV', 'name_zh': '马尔代夫', 'name_en': 'Maldives', 'name_th': 'มัลดีฟส์', 'phone': '+960', 'currency': 'MVR'},
        {'code': 'NP', 'name_zh': '尼泊尔', 'name_en': 'Nepal', 'name_th': 'เนปาล', 'phone': '+977', 'currency': 'NPR'},
        {'code': 'OM', 'name_zh': '阿曼', 'name_en': 'Oman', 'name_th': 'โอมาน', 'phone': '+968', 'currency': 'OMR'},
        {'code': 'QA', 'name_zh': '卡塔尔', 'name_en': 'Qatar', 'name_th': 'กาตาร์', 'phone': '+974', 'currency': 'QAR'},
        {'code': 'LK', 'name_zh': '斯里兰卡', 'name_en': 'Sri Lanka', 'name_th': 'ศรีลังกา', 'phone': '+94', 'currency': 'LKR'},
        {'code': 'SY', 'name_zh': '叙利亚', 'name_en': 'Syria', 'name_th': 'ซีเรีย', 'phone': '+963', 'currency': 'SYP'},
        {'code': 'TJ', 'name_zh': '塔吉克斯坦', 'name_en': 'Tajikistan', 'name_th': 'ทาจิกิสถาน', 'phone': '+992', 'currency': 'TJS'},
        {'code': 'TM', 'name_zh': '土库曼斯坦', 'name_en': 'Turkmenistan', 'name_th': 'เติร์กเมนิสถาน', 'phone': '+993', 'currency': 'TMT'},
        {'code': 'YE', 'name_zh': '也门', 'name_en': 'Yemen', 'name_th': 'เยเมน', 'phone': '+967', 'currency': 'YER'},

        # 其他欧洲国家
        {'code': 'AL', 'name_zh': '阿尔巴尼亚', 'name_en': 'Albania', 'name_th': 'แอลเบเนีย', 'phone': '+355', 'currency': 'ALL'},
        {'code': 'AD', 'name_zh': '安道尔', 'name_en': 'Andorra', 'name_th': 'อันดอร์รา', 'phone': '+376', 'currency': 'EUR'},
        {'code': 'BY', 'name_zh': '白俄罗斯', 'name_en': 'Belarus', 'name_th': 'เบลารุส', 'phone': '+375', 'currency': 'BYN'},
        {'code': 'BA', 'name_zh': '波黑', 'name_en': 'Bosnia and Herzegovina', 'name_th': 'บอสเนียและเฮอร์เซโกวีนา', 'phone': '+387', 'currency': 'BAM'},
        {'code': 'BG', 'name_zh': '保加利亚', 'name_en': 'Bulgaria', 'name_th': 'บัลแกเรีย', 'phone': '+359', 'currency': 'BGN'},
        {'code': 'HR', 'name_zh': '克罗地亚', 'name_en': 'Croatia', 'name_th': 'โครเอเชีย', 'phone': '+385', 'currency': 'HRK'},
        {'code': 'CY', 'name_zh': '塞浦路斯', 'name_en': 'Cyprus', 'name_th': 'ไซปรัส', 'phone': '+357', 'currency': 'EUR'},
        {'code': 'EE', 'name_zh': '爱沙尼亚', 'name_en': 'Estonia', 'name_th': 'เอสโตเนีย', 'phone': '+372', 'currency': 'EUR'},
        {'code': 'HU', 'name_zh': '匈牙利', 'name_en': 'Hungary', 'name_th': 'ฮังการี', 'phone': '+36', 'currency': 'HUF'},
        {'code': 'IS', 'name_zh': '冰岛', 'name_en': 'Iceland', 'name_th': 'ไอซ์แลนด์', 'phone': '+354', 'currency': 'ISK'},
        {'code': 'IE', 'name_zh': '爱尔兰', 'name_en': 'Ireland', 'name_th': 'ไอร์แลนด์', 'phone': '+353', 'currency': 'EUR'},
        {'code': 'XK', 'name_zh': '科索沃', 'name_en': 'Kosovo', 'name_th': 'โคโซโว', 'phone': '+383', 'currency': 'EUR'},
        {'code': 'LV', 'name_zh': '拉脱维亚', 'name_en': 'Latvia', 'name_th': 'ลัตเวีย', 'phone': '+371', 'currency': 'EUR'},
        {'code': 'LI', 'name_zh': '列支敦士登', 'name_en': 'Liechtenstein', 'name_th': 'ลิกเตนสไตน์', 'phone': '+423', 'currency': 'CHF'},
        {'code': 'LT', 'name_zh': '立陶宛', 'name_en': 'Lithuania', 'name_th': 'ลิทัวเนีย', 'phone': '+370', 'currency': 'EUR'},
        {'code': 'LU', 'name_zh': '卢森堡', 'name_en': 'Luxembourg', 'name_th': 'ลักเซมเบิร์ก', 'phone': '+352', 'currency': 'EUR'},
        {'code': 'MT', 'name_zh': '马耳他', 'name_en': 'Malta', 'name_th': 'มอลตา', 'phone': '+356', 'currency': 'EUR'},
        {'code': 'MD', 'name_zh': '摩尔多瓦', 'name_en': 'Moldova', 'name_th': 'มอลโดวา', 'phone': '+373', 'currency': 'MDL'},
        {'code': 'MC', 'name_zh': '摩纳哥', 'name_en': 'Monaco', 'name_th': 'โมนาโก', 'phone': '+377', 'currency': 'EUR'},
        {'code': 'ME', 'name_zh': '黑山', 'name_en': 'Montenegro', 'name_th': 'มอนเตเนโกร', 'phone': '+382', 'currency': 'EUR'},
        {'code': 'MK', 'name_zh': '北马其顿', 'name_en': 'North Macedonia', 'name_th': 'มาซิโดเนียเหนือ', 'phone': '+389', 'currency': 'MKD'},
        {'code': 'RS', 'name_zh': '塞尔维亚', 'name_en': 'Serbia', 'name_th': 'เซอร์เบีย', 'phone': '+381', 'currency': 'RSD'},
        {'code': 'SK', 'name_zh': '斯洛伐克', 'name_en': 'Slovakia', 'name_th': 'สโลวาเกีย', 'phone': '+421', 'currency': 'EUR'},
        {'code': 'SI', 'name_zh': '斯洛文尼亚', 'name_en': 'Slovenia', 'name_th': 'สโลวีเนีย', 'phone': '+386', 'currency': 'EUR'},
        {'code': 'SM', 'name_zh': '圣马力诺', 'name_en': 'San Marino', 'name_th': 'ซานมารีโน', 'phone': '+378', 'currency': 'EUR'},
        {'code': 'VA', 'name_zh': '梵蒂冈', 'name_en': 'Vatican City', 'name_th': 'นครรัฐวาติกัน', 'phone': '+39', 'currency': 'EUR'},

        # 其他美洲国家
        {'code': 'AG', 'name_zh': '安提瓜和巴布达', 'name_en': 'Antigua and Barbuda', 'name_th': 'แอนติกาและบาร์บูดา', 'phone': '+1268', 'currency': 'XCD'},
        {'code': 'BS', 'name_zh': '巴哈马', 'name_en': 'Bahamas', 'name_th': 'บาฮามาส', 'phone': '+1242', 'currency': 'BSD'},
        {'code': 'BB', 'name_zh': '巴巴多斯', 'name_en': 'Barbados', 'name_th': 'บาร์เบโดส', 'phone': '+1246', 'currency': 'BBD'},
        {'code': 'BZ', 'name_zh': '伯利兹', 'name_en': 'Belize', 'name_th': 'เบลีซ', 'phone': '+501', 'currency': 'BZD'},
        {'code': 'BO', 'name_zh': '玻利维亚', 'name_en': 'Bolivia', 'name_th': 'โบลิเวีย', 'phone': '+591', 'currency': 'BOB'},
        {'code': 'CR', 'name_zh': '哥斯达黎加', 'name_en': 'Costa Rica', 'name_th': 'คอสตาริกา', 'phone': '+506', 'currency': 'CRC'},
        {'code': 'CU', 'name_zh': '古巴', 'name_en': 'Cuba', 'name_th': 'คิวบา', 'phone': '+53', 'currency': 'CUP'},
        {'code': 'DM', 'name_zh': '多米尼克', 'name_en': 'Dominica', 'name_th': 'โดมินิกา', 'phone': '+1767', 'currency': 'XCD'},
        {'code': 'DO', 'name_zh': '多米尼加', 'name_en': 'Dominican Republic', 'name_th': 'สาธารณรัฐโดมินิกัน', 'phone': '+1', 'currency': 'DOP'},
        {'code': 'EC', 'name_zh': '厄瓜多尔', 'name_en': 'Ecuador', 'name_th': 'เอกวาดอร์', 'phone': '+593', 'currency': 'USD'},
        {'code': 'SV', 'name_zh': '萨尔瓦多', 'name_en': 'El Salvador', 'name_th': 'เอลซัลวาดอร์', 'phone': '+503', 'currency': 'USD'},
        {'code': 'GD', 'name_zh': '格林纳达', 'name_en': 'Grenada', 'name_th': 'เกรนาดา', 'phone': '+1473', 'currency': 'XCD'},
        {'code': 'GT', 'name_zh': '危地马拉', 'name_en': 'Guatemala', 'name_th': 'กัวเตมาลา', 'phone': '+502', 'currency': 'GTQ'},
        {'code': 'GY', 'name_zh': '圭亚那', 'name_en': 'Guyana', 'name_th': 'กายอานา', 'phone': '+592', 'currency': 'GYD'},
        {'code': 'HT', 'name_zh': '海地', 'name_en': 'Haiti', 'name_th': 'เฮติ', 'phone': '+509', 'currency': 'HTG'},
        {'code': 'HN', 'name_zh': '洪都拉斯', 'name_en': 'Honduras', 'name_th': 'ฮอนดูรัส', 'phone': '+504', 'currency': 'HNL'},
        {'code': 'JM', 'name_zh': '牙买加', 'name_en': 'Jamaica', 'name_th': 'จาเมกา', 'phone': '+1876', 'currency': 'JMD'},
        {'code': 'NI', 'name_zh': '尼加拉瓜', 'name_en': 'Nicaragua', 'name_th': 'นิการากัว', 'phone': '+505', 'currency': 'NIO'},
        {'code': 'PA', 'name_zh': '巴拿马', 'name_en': 'Panama', 'name_th': 'ปานามา', 'phone': '+507', 'currency': 'PAB'},
        {'code': 'PY', 'name_zh': '巴拉圭', 'name_en': 'Paraguay', 'name_th': 'ปารากวัย', 'phone': '+595', 'currency': 'PYG'},
        {'code': 'KN', 'name_zh': '圣基茨和尼维斯', 'name_en': 'Saint Kitts and Nevis', 'name_th': 'เซนต์คิตส์และเนวิส', 'phone': '+1869', 'currency': 'XCD'},
        {'code': 'LC', 'name_zh': '圣卢西亚', 'name_en': 'Saint Lucia', 'name_th': 'เซนต์ลูเซีย', 'phone': '+1758', 'currency': 'XCD'},
        {'code': 'VC', 'name_zh': '圣文森特和格林纳丁斯', 'name_en': 'Saint Vincent and the Grenadines', 'name_th': 'เซนต์วินเซนต์และเกรนาดีนส์', 'phone': '+1784', 'currency': 'XCD'},
        {'code': 'SR', 'name_zh': '苏里南', 'name_en': 'Suriname', 'name_th': 'ซูรินาเม', 'phone': '+597', 'currency': 'SRD'},
        {'code': 'TT', 'name_zh': '特立尼达和多巴哥', 'name_en': 'Trinidad and Tobago', 'name_th': 'ตรินิแดดและโตเบโก', 'phone': '+1868', 'currency': 'TTD'},

        # 其他非洲国家
        {'code': 'DZ', 'name_zh': '阿尔及利亚', 'name_en': 'Algeria', 'name_th': 'แอลจีเรีย', 'phone': '+213', 'currency': 'DZD'},
        {'code': 'AO', 'name_zh': '安哥拉', 'name_en': 'Angola', 'name_th': 'แองโกลา', 'phone': '+244', 'currency': 'AOA'},
        {'code': 'BJ', 'name_zh': '贝宁', 'name_en': 'Benin', 'name_th': 'เบนิน', 'phone': '+229', 'currency': 'XOF'},
        {'code': 'BW', 'name_zh': '博茨瓦纳', 'name_en': 'Botswana', 'name_th': 'บอตสวานา', 'phone': '+267', 'currency': 'BWP'},
        {'code': 'BF', 'name_zh': '布基纳法索', 'name_en': 'Burkina Faso', 'name_th': 'บูร์กินาฟาโซ', 'phone': '+226', 'currency': 'XOF'},
        {'code': 'BI', 'name_zh': '布隆迪', 'name_en': 'Burundi', 'name_th': 'บุรุนดี', 'phone': '+257', 'currency': 'BIF'},
        {'code': 'CM', 'name_zh': '喀麦隆', 'name_en': 'Cameroon', 'name_th': 'แคเมอรูน', 'phone': '+237', 'currency': 'XAF'},
        {'code': 'CV', 'name_zh': '佛得角', 'name_en': 'Cape Verde', 'name_th': 'เคปเวิร์ด', 'phone': '+238', 'currency': 'CVE'},
        {'code': 'CF', 'name_zh': '中非', 'name_en': 'Central African Republic', 'name_th': 'สาธารณรัฐแอฟริกากลาง', 'phone': '+236', 'currency': 'XAF'},
        {'code': 'TD', 'name_zh': '乍得', 'name_en': 'Chad', 'name_th': 'ชาด', 'phone': '+235', 'currency': 'XAF'},
        {'code': 'KM', 'name_zh': '科摩罗', 'name_en': 'Comoros', 'name_th': 'คอโมโรส', 'phone': '+269', 'currency': 'KMF'},
        {'code': 'CG', 'name_zh': '刚果（布）', 'name_en': 'Congo', 'name_th': 'คองโก', 'phone': '+242', 'currency': 'XAF'},
        {'code': 'CD', 'name_zh': '刚果（金）', 'name_en': 'Democratic Republic of the Congo', 'name_th': 'สาธารณรัฐประชาธิปไตยคองโก', 'phone': '+243', 'currency': 'CDF'},
        {'code': 'CI', 'name_zh': '科特迪瓦', 'name_en': 'Ivory Coast', 'name_th': 'ไอวอรีโคสต์', 'phone': '+225', 'currency': 'XOF'},
        {'code': 'DJ', 'name_zh': '吉布提', 'name_en': 'Djibouti', 'name_th': 'จิบูตี', 'phone': '+253', 'currency': 'DJF'},
        {'code': 'GQ', 'name_zh': '赤道几内亚', 'name_en': 'Equatorial Guinea', 'name_th': 'อิเควทอเรียลกินี', 'phone': '+240', 'currency': 'XAF'},
        {'code': 'ER', 'name_zh': '厄立特里亚', 'name_en': 'Eritrea', 'name_th': 'เอริเทรีย', 'phone': '+291', 'currency': 'ERN'},
        {'code': 'GA', 'name_zh': '加蓬', 'name_en': 'Gabon', 'name_th': 'กาบอง', 'phone': '+241', 'currency': 'XAF'},
        {'code': 'GM', 'name_zh': '冈比亚', 'name_en': 'Gambia', 'name_th': 'แกมเบีย', 'phone': '+220', 'currency': 'GMD'},
        {'code': 'GH', 'name_zh': '加纳', 'name_en': 'Ghana', 'name_th': 'กานา', 'phone': '+233', 'currency': 'GHS'},
        {'code': 'GN', 'name_zh': '几内亚', 'name_en': 'Guinea', 'name_th': 'กินี', 'phone': '+224', 'currency': 'GNF'},
        {'code': 'GW', 'name_zh': '几内亚比绍', 'name_en': 'Guinea-Bissau', 'name_th': 'กินี-บิสเซา', 'phone': '+245', 'currency': 'XOF'},
        {'code': 'LS', 'name_zh': '莱索托', 'name_en': 'Lesotho', 'name_th': 'เลโซโท', 'phone': '+266', 'currency': 'LSL'},
        {'code': 'LR', 'name_zh': '利比里亚', 'name_en': 'Liberia', 'name_th': 'ไลบีเรีย', 'phone': '+231', 'currency': 'LRD'},
        {'code': 'LY', 'name_zh': '利比亚', 'name_en': 'Libya', 'name_th': 'ลิเบีย', 'phone': '+218', 'currency': 'LYD'},
        {'code': 'MG', 'name_zh': '马达加斯加', 'name_en': 'Madagascar', 'name_th': 'มาดากัสการ์', 'phone': '+261', 'currency': 'MGA'},
        {'code': 'MW', 'name_zh': '马拉维', 'name_en': 'Malawi', 'name_th': 'มาลาวี', 'phone': '+265', 'currency': 'MWK'},
        {'code': 'ML', 'name_zh': '马里', 'name_en': 'Mali', 'name_th': 'มาลี', 'phone': '+223', 'currency': 'XOF'},
        {'code': 'MR', 'name_zh': '毛里塔尼亚', 'name_en': 'Mauritania', 'name_th': 'มอริเตเนีย', 'phone': '+222', 'currency': 'MRU'},
        {'code': 'MU', 'name_zh': '毛里求斯', 'name_en': 'Mauritius', 'name_th': 'มอริเชียส', 'phone': '+230', 'currency': 'MUR'},
        {'code': 'MA', 'name_zh': '摩洛哥', 'name_en': 'Morocco', 'name_th': 'โมร็อกโก', 'phone': '+212', 'currency': 'MAD'},
        {'code': 'MZ', 'name_zh': '莫桑比克', 'name_en': 'Mozambique', 'name_th': 'โมซัมบิก', 'phone': '+258', 'currency': 'MZN'},
        {'code': 'NA', 'name_zh': '纳米比亚', 'name_en': 'Namibia', 'name_th': 'นามิเบีย', 'phone': '+264', 'currency': 'NAD'},
        {'code': 'NE', 'name_zh': '尼日尔', 'name_en': 'Niger', 'name_th': 'ไนเจอร์', 'phone': '+227', 'currency': 'XOF'},
        {'code': 'RW', 'name_zh': '卢旺达', 'name_en': 'Rwanda', 'name_th': 'รวันดา', 'phone': '+250', 'currency': 'RWF'},
        {'code': 'ST', 'name_zh': '圣多美和普林西比', 'name_en': 'Sao Tome and Principe', 'name_th': 'เซาตูเมและปรินซิปี', 'phone': '+239', 'currency': 'STN'},
        {'code': 'SN', 'name_zh': '塞内加尔', 'name_en': 'Senegal', 'name_th': 'เซเนกัล', 'phone': '+221', 'currency': 'XOF'},
        {'code': 'SC', 'name_zh': '塞舌尔', 'name_en': 'Seychelles', 'name_th': 'เซเชลส์', 'phone': '+248', 'currency': 'SCR'},
        {'code': 'SL', 'name_zh': '塞拉利昂', 'name_en': 'Sierra Leone', 'name_th': 'เซียร์ราลีโอน', 'phone': '+232', 'currency': 'SLL'},
        {'code': 'SO', 'name_zh': '索马里', 'name_en': 'Somalia', 'name_th': 'โซมาเลีย', 'phone': '+252', 'currency': 'SOS'},
        {'code': 'SS', 'name_zh': '南苏丹', 'name_en': 'South Sudan', 'name_th': 'ซูดานใต้', 'phone': '+211', 'currency': 'SSP'},
        {'code': 'SD', 'name_zh': '苏丹', 'name_en': 'Sudan', 'name_th': 'ซูดาน', 'phone': '+249', 'currency': 'SDG'},
        {'code': 'SZ', 'name_zh': '斯威士兰', 'name_en': 'Eswatini', 'name_th': 'เอสวาตินี', 'phone': '+268', 'currency': 'SZL'},
        {'code': 'TG', 'name_zh': '多哥', 'name_en': 'Togo', 'name_th': 'โตโก', 'phone': '+228', 'currency': 'XOF'},
        {'code': 'TN', 'name_zh': '突尼斯', 'name_en': 'Tunisia', 'name_th': 'ตูนิเซีย', 'phone': '+216', 'currency': 'TND'},
        {'code': 'UG', 'name_zh': '乌干达', 'name_en': 'Uganda', 'name_th': 'ยูกันดา', 'phone': '+256', 'currency': 'UGX'},
        {'code': 'ZM', 'name_zh': '赞比亚', 'name_en': 'Zambia', 'name_th': 'แซมเบีย', 'phone': '+260', 'currency': 'ZMW'},
        {'code': 'ZW', 'name_zh': '津巴布韦', 'name_en': 'Zimbabwe', 'name_th': 'ซิมบับเว', 'phone': '+263', 'currency': 'ZWL'},

        # 其他大洋洲国家
        {'code': 'KI', 'name_zh': '基里巴斯', 'name_en': 'Kiribati', 'name_th': 'คิริบาส', 'phone': '+686', 'currency': 'AUD'},
        {'code': 'MH', 'name_zh': '马绍尔群岛', 'name_en': 'Marshall Islands', 'name_th': 'หมู่เกาะมาร์แชลล์', 'phone': '+692', 'currency': 'USD'},
        {'code': 'FM', 'name_zh': '密克罗尼西亚', 'name_en': 'Micronesia', 'name_th': 'ไมโครนีเซีย', 'phone': '+691', 'currency': 'USD'},
        {'code': 'NR', 'name_zh': '瑙鲁', 'name_en': 'Nauru', 'name_th': 'นาอูรู', 'phone': '+674', 'currency': 'AUD'},
        {'code': 'PW', 'name_zh': '帕劳', 'name_en': 'Palau', 'name_th': 'ปาเลา', 'phone': '+680', 'currency': 'USD'},
        {'code': 'WS', 'name_zh': '萨摩亚', 'name_en': 'Samoa', 'name_th': 'ซามัว', 'phone': '+685', 'currency': 'WST'},
        {'code': 'SB', 'name_zh': '所罗门群岛', 'name_en': 'Solomon Islands', 'name_th': 'หมู่เกาะโซโลมอน', 'phone': '+677', 'currency': 'SBD'},
        {'code': 'TO', 'name_zh': '汤加', 'name_en': 'Tonga', 'name_th': 'ตองกา', 'phone': '+676', 'currency': 'TOP'},
        {'code': 'TV', 'name_zh': '图瓦卢', 'name_en': 'Tuvalu', 'name_th': 'ตูวาลู', 'phone': '+688', 'currency': 'AUD'},
        {'code': 'VU', 'name_zh': '瓦努阿图', 'name_en': 'Vanuatu', 'name_th': 'วานูอาตู', 'phone': '+678', 'currency': 'VUV'},

        # 特殊地区（港澳台）
        {'code': 'HK', 'name_zh': '中国香港', 'name_en': 'Hong Kong', 'name_th': 'ฮ่องกง', 'phone': '+852', 'currency': 'HKD'},
        {'code': 'MO', 'name_zh': '中国澳门', 'name_en': 'Macau', 'name_th': 'มาเก๊า', 'phone': '+853', 'currency': 'MOP'},
        {'code': 'TW', 'name_zh': '中国台湾', 'name_en': 'Taiwan', 'name_th': 'ไต้หวัน', 'phone': '+886', 'currency': 'TWD'},
    ]

    @staticmethod
    def initialize_countries():
        """初始化195个国家数据到数据库"""
        session = DatabaseService.get_session()
        try:
            # 检查是否已有数据
            existing_count = session.query(Country).count()
            if existing_count > 0:
                logger.info(f"国家数据已存在 ({existing_count} 条记录)，跳过初始化")
                return {
                    'success': True,
                    'message': f'国家数据已存在，共 {existing_count} 条记录'
                }

            # 批量插入国家数据
            countries = []
            for idx, data in enumerate(CountryDataInitializer.COUNTRIES_DATA):
                country = Country(
                    country_code=data['code'],
                    country_name_zh=data['name_zh'],
                    country_name_en=data['name_en'],
                    country_name_th=data.get('name_th', ''),
                    phone_code=data.get('phone', ''),
                    currency_code=data.get('currency', ''),
                    is_active=True,
                    sort_order=idx + 1  # 按数组顺序排序
                )
                countries.append(country)

            session.bulk_save_objects(countries)
            session.commit()

            logger.info(f"成功初始化 {len(countries)} 个国家数据")
            return {
                'success': True,
                'message': f'成功初始化 {len(countries)} 个国家数据'
            }

        except Exception as e:
            session.rollback()
            logger.error(f"初始化国家数据失败: {str(e)}")
            return {
                'success': False,
                'message': f'初始化失败: {str(e)}'
            }
        finally:
            DatabaseService.close_session(session)
