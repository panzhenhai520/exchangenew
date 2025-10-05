#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Initialize 195 countries data with multi-language support (zh-CN, en-US, th-TH)
Based on ISO 3166-1 alpha-2 country codes
"""

import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Country

# 195 countries data (ISO 3166-1 alpha-2)
COUNTRIES_DATA = [
    ('AF', 'Afghanistan', '阿富汗', 'อัฟกานิสถาน', '+93', 'AFN', 1, 10),
    ('AL', 'Albania', '阿尔巴尼亚', 'แอลเบเนีย', '+355', 'ALL', 1, 20),
    ('DZ', 'Algeria', '阿尔及利亚', 'แอลจีเรีย', '+213', 'DZD', 1, 30),
    ('AD', 'Andorra', '安道尔', 'อันดอร์รา', '+376', 'EUR', 1, 40),
    ('AO', 'Angola', '安哥拉', 'แองโกลา', '+244', 'AOA', 1, 50),
    ('AG', 'Antigua and Barbuda', '安提瓜和巴布达', 'แอนติกาและบาร์บูดา', '+1-268', 'XCD', 1, 60),
    ('AR', 'Argentina', '阿根廷', 'อาร์เจนตินา', '+54', 'ARS', 1, 70),
    ('AM', 'Armenia', '亚美尼亚', 'อาร์เมเนีย', '+374', 'AMD', 1, 80),
    ('AU', 'Australia', '澳大利亚', 'ออสเตรเลีย', '+61', 'AUD', 1, 90),
    ('AT', 'Austria', '奥地利', 'ออสเตรีย', '+43', 'EUR', 1, 100),
    ('AZ', 'Azerbaijan', '阿塞拜疆', 'อาเซอร์ไบจาน', '+994', 'AZN', 1, 110),
    ('BS', 'Bahamas', '巴哈马', 'บาฮามาส', '+1-242', 'BSD', 1, 120),
    ('BH', 'Bahrain', '巴林', 'บาห์เรน', '+973', 'BHD', 1, 130),
    ('BD', 'Bangladesh', '孟加拉国', 'บังกลาเทศ', '+880', 'BDT', 1, 140),
    ('BB', 'Barbados', '巴巴多斯', 'บาร์เบโดส', '+1-246', 'BBD', 1, 150),
    ('BY', 'Belarus', '白俄罗斯', 'เบลารุส', '+375', 'BYN', 1, 160),
    ('BE', 'Belgium', '比利时', 'เบลเยียม', '+32', 'EUR', 1, 170),
    ('BZ', 'Belize', '伯利兹', 'เบลีซ', '+501', 'BZD', 1, 180),
    ('BJ', 'Benin', '贝宁', 'เบนิน', '+229', 'XOF', 1, 190),
    ('BT', 'Bhutan', '不丹', 'ภูฏาน', '+975', 'BTN', 1, 200),
    ('BO', 'Bolivia', '玻利维亚', 'โบลิเวีย', '+591', 'BOB', 1, 210),
    ('BA', 'Bosnia and Herzegovina', '波斯尼亚和黑塞哥维那', 'บอสเนียและเฮอร์เซโกวีนา', '+387', 'BAM', 1, 220),
    ('BW', 'Botswana', '博茨瓦纳', 'บอตสวานา', '+267', 'BWP', 1, 230),
    ('BR', 'Brazil', '巴西', 'บราซิล', '+55', 'BRL', 1, 240),
    ('BN', 'Brunei', '文莱', 'บรูไน', '+673', 'BND', 1, 250),
    ('BG', 'Bulgaria', '保加利亚', 'บัลแกเรีย', '+359', 'BGN', 1, 260),
    ('BF', 'Burkina Faso', '布基纳法索', 'บูร์กินาฟาโซ', '+226', 'XOF', 1, 270),
    ('BI', 'Burundi', '布隆迪', 'บุรุนดี', '+257', 'BIF', 1, 280),
    ('KH', 'Cambodia', '柬埔寨', 'กัมพูชา', '+855', 'KHR', 1, 290),
    ('CM', 'Cameroon', '喀麦隆', 'แคเมอรูน', '+237', 'XAF', 1, 300),
    ('CA', 'Canada', '加拿大', 'แคนาดา', '+1', 'CAD', 1, 310),
    ('CV', 'Cape Verde', '佛得角', 'เคปเวิร์ด', '+238', 'CVE', 1, 320),
    ('CF', 'Central African Republic', '中非共和国', 'สาธารณรัฐแอฟริกากลาง', '+236', 'XAF', 1, 330),
    ('TD', 'Chad', '乍得', 'ชาด', '+235', 'XAF', 1, 340),
    ('CL', 'Chile', '智利', 'ชิลี', '+56', 'CLP', 1, 350),
    ('CN', 'China', '中国', 'จีน', '+86', 'CNY', 1, 1),
    ('CO', 'Colombia', '哥伦比亚', 'โคลอมเบีย', '+57', 'COP', 1, 360),
    ('KM', 'Comoros', '科摩罗', 'คอโมโรส', '+269', 'KMF', 1, 370),
    ('CG', 'Congo', '刚果（布）', 'คองโก', '+242', 'XAF', 1, 380),
    ('CD', 'Congo (DRC)', '刚果（金）', 'คองโก (สาธารณรัฐประชาธิปไตย)', '+243', 'CDF', 1, 390),
    ('CR', 'Costa Rica', '哥斯达黎加', 'คอสตาริกา', '+506', 'CRC', 1, 400),
    ('CI', 'Ivory Coast', '科特迪瓦', 'ไอวอรีโคสต์', '+225', 'XOF', 1, 410),
    ('HR', 'Croatia', '克罗地亚', 'โครเอเชีย', '+385', 'HRK', 1, 420),
    ('CU', 'Cuba', '古巴', 'คิวบา', '+53', 'CUP', 1, 430),
    ('CY', 'Cyprus', '塞浦路斯', 'ไซปรัส', '+357', 'EUR', 1, 440),
    ('CZ', 'Czech Republic', '捷克', 'สาธารณรัฐเช็ก', '+420', 'CZK', 1, 450),
    ('DK', 'Denmark', '丹麦', 'เดนมาร์ก', '+45', 'DKK', 1, 460),
    ('DJ', 'Djibouti', '吉布提', 'จิบูตี', '+253', 'DJF', 1, 470),
    ('DM', 'Dominica', '多米尼克', 'โดมินิกา', '+1-767', 'XCD', 1, 480),
    ('DO', 'Dominican Republic', '多米尼加共和国', 'สาธารณรัฐโดมินิกัน', '+1-809', 'DOP', 1, 490),
    ('EC', 'Ecuador', '厄瓜多尔', 'เอกวาดอร์', '+593', 'USD', 1, 500),
    ('EG', 'Egypt', '埃及', 'อียิปต์', '+20', 'EGP', 1, 510),
    ('SV', 'El Salvador', '萨尔瓦多', 'เอลซัลวาดอร์', '+503', 'USD', 1, 520),
    ('GQ', 'Equatorial Guinea', '赤道几内亚', 'อิเควทอเรียลกินี', '+240', 'XAF', 1, 530),
    ('ER', 'Eritrea', '厄立特里亚', 'เอริเทรีย', '+291', 'ERN', 1, 540),
    ('EE', 'Estonia', '爱沙尼亚', 'เอสโตเนีย', '+372', 'EUR', 1, 550),
    ('ET', 'Ethiopia', '埃塞俄比亚', 'เอธิโอเปีย', '+251', 'ETB', 1, 560),
    ('FJ', 'Fiji', '斐济', 'ฟิจิ', '+679', 'FJD', 1, 570),
    ('FI', 'Finland', '芬兰', 'ฟินแลนด์', '+358', 'EUR', 1, 580),
    ('FR', 'France', '法国', 'ฝรั่งเศส', '+33', 'EUR', 1, 590),
    ('GA', 'Gabon', '加蓬', 'กาบอง', '+241', 'XAF', 1, 600),
    ('GM', 'Gambia', '冈比亚', 'แกมเบีย', '+220', 'GMD', 1, 610),
    ('GE', 'Georgia', '格鲁吉亚', 'จอร์เจีย', '+995', 'GEL', 1, 620),
    ('DE', 'Germany', '德国', 'เยอรมนี', '+49', 'EUR', 1, 630),
    ('GH', 'Ghana', '加纳', 'กานา', '+233', 'GHS', 1, 640),
    ('GR', 'Greece', '希腊', 'กรีซ', '+30', 'EUR', 1, 650),
    ('GD', 'Grenada', '格林纳达', 'เกรเนดา', '+1-473', 'XCD', 1, 660),
    ('GT', 'Guatemala', '危地马拉', 'กัวเตมาลา', '+502', 'GTQ', 1, 670),
    ('GN', 'Guinea', '几内亚', 'กินี', '+224', 'GNF', 1, 680),
    ('GW', 'Guinea-Bissau', '几内亚比绍', 'กินี-บิสเซา', '+245', 'XOF', 1, 690),
    ('GY', 'Guyana', '圭亚那', 'กายอานา', '+592', 'GYD', 1, 700),
    ('HT', 'Haiti', '海地', 'เฮติ', '+509', 'HTG', 1, 710),
    ('HN', 'Honduras', '洪都拉斯', 'ฮอนดูรัส', '+504', 'HNL', 1, 720),
    ('HU', 'Hungary', '匈牙利', 'ฮังการี', '+36', 'HUF', 1, 730),
    ('IS', 'Iceland', '冰岛', 'ไอซ์แลนด์', '+354', 'ISK', 1, 740),
    ('IN', 'India', '印度', 'อินเดีย', '+91', 'INR', 1, 750),
    ('ID', 'Indonesia', '印度尼西亚', 'อินโดนีเซีย', '+62', 'IDR', 1, 760),
    ('IR', 'Iran', '伊朗', 'อิหร่าน', '+98', 'IRR', 1, 770),
    ('IQ', 'Iraq', '伊拉克', 'อิรัก', '+964', 'IQD', 1, 780),
    ('IE', 'Ireland', '爱尔兰', 'ไอร์แลนด์', '+353', 'EUR', 1, 790),
    ('IL', 'Israel', '以色列', 'อิสราเอล', '+972', 'ILS', 1, 800),
    ('IT', 'Italy', '意大利', 'อิตาลี', '+39', 'EUR', 1, 810),
    ('JM', 'Jamaica', '牙买加', 'จาเมกา', '+1-876', 'JMD', 1, 820),
    ('JP', 'Japan', '日本', 'ญี่ปุ่น', '+81', 'JPY', 1, 830),
    ('JO', 'Jordan', '约旦', 'จอร์แดน', '+962', 'JOD', 1, 840),
    ('KZ', 'Kazakhstan', '哈萨克斯坦', 'คาซัคสถาน', '+7', 'KZT', 1, 850),
    ('KE', 'Kenya', '肯尼亚', 'เคนยา', '+254', 'KES', 1, 860),
    ('KI', 'Kiribati', '基里巴斯', 'คิริบาส', '+686', 'AUD', 1, 870),
    ('KP', 'North Korea', '朝鲜', 'เกาหลีเหนือ', '+850', 'KPW', 1, 880),
    ('KR', 'South Korea', '韩国', 'เกาหลีใต้', '+82', 'KRW', 1, 890),
    ('KW', 'Kuwait', '科威特', 'คูเวต', '+965', 'KWD', 1, 900),
    ('KG', 'Kyrgyzstan', '吉尔吉斯斯坦', 'คีร์กีซสถาน', '+996', 'KGS', 1, 910),
    ('LA', 'Laos', '老挝', 'ลาว', '+856', 'LAK', 1, 920),
    ('LV', 'Latvia', '拉脱维亚', 'ลัตเวีย', '+371', 'EUR', 1, 930),
    ('LB', 'Lebanon', '黎巴嫩', 'เลบานอน', '+961', 'LBP', 1, 940),
    ('LS', 'Lesotho', '莱索托', 'เลโซโท', '+266', 'LSL', 1, 950),
    ('LR', 'Liberia', '利比里亚', 'ไลบีเรีย', '+231', 'LRD', 1, 960),
    ('LY', 'Libya', '利比亚', 'ลิเบีย', '+218', 'LYD', 1, 970),
    ('LI', 'Liechtenstein', '列支敦士登', 'ลิกเตนสไตน์', '+423', 'CHF', 1, 980),
    ('LT', 'Lithuania', '立陶宛', 'ลิทัวเนีย', '+370', 'EUR', 1, 990),
    ('LU', 'Luxembourg', '卢森堡', 'ลักเซมเบิร์ก', '+352', 'EUR', 1, 1000),
    ('MK', 'North Macedonia', '北马其顿', 'มาซิโดเนียเหนือ', '+389', 'MKD', 1, 1010),
    ('MG', 'Madagascar', '马达加斯加', 'มาดากัสการ์', '+261', 'MGA', 1, 1020),
    ('MW', 'Malawi', '马拉维', 'มาลาวี', '+265', 'MWK', 1, 1030),
    ('MY', 'Malaysia', '马来西亚', 'มาเลเซีย', '+60', 'MYR', 1, 1040),
    ('MV', 'Maldives', '马尔代夫', 'มัลดีฟส์', '+960', 'MVR', 1, 1050),
    ('ML', 'Mali', '马里', 'มาลี', '+223', 'XOF', 1, 1060),
    ('MT', 'Malta', '马耳他', 'มอลตา', '+356', 'EUR', 1, 1070),
    ('MH', 'Marshall Islands', '马绍尔群岛', 'หมู่เกาะมาร์แชลล์', '+692', 'USD', 1, 1080),
    ('MR', 'Mauritania', '毛里塔尼亚', 'มอริเตเนีย', '+222', 'MRU', 1, 1090),
    ('MU', 'Mauritius', '毛里求斯', 'มอริเชียส', '+230', 'MUR', 1, 1100),
    ('MX', 'Mexico', '墨西哥', 'เม็กซิโก', '+52', 'MXN', 1, 1110),
    ('FM', 'Micronesia', '密克罗尼西亚', 'ไมโครนีเซีย', '+691', 'USD', 1, 1120),
    ('MD', 'Moldova', '摩尔多瓦', 'มอลโดวา', '+373', 'MDL', 1, 1130),
    ('MC', 'Monaco', '摩纳哥', 'โมนาโก', '+377', 'EUR', 1, 1140),
    ('MN', 'Mongolia', '蒙古', 'มองโกเลีย', '+976', 'MNT', 1, 1150),
    ('ME', 'Montenegro', '黑山', 'มอนเตเนโกร', '+382', 'EUR', 1, 1160),
    ('MA', 'Morocco', '摩洛哥', 'โมร็อกโก', '+212', 'MAD', 1, 1170),
    ('MZ', 'Mozambique', '莫桑比克', 'โมซัมบิก', '+258', 'MZN', 1, 1180),
    ('MM', 'Myanmar', '缅甸', 'พม่า', '+95', 'MMK', 1, 1190),
    ('NA', 'Namibia', '纳米比亚', 'นามิเบีย', '+264', 'NAD', 1, 1200),
    ('NR', 'Nauru', '瑙鲁', 'นาอูรู', '+674', 'AUD', 1, 1210),
    ('NP', 'Nepal', '尼泊尔', 'เนปาล', '+977', 'NPR', 1, 1220),
    ('NL', 'Netherlands', '荷兰', 'เนเธอร์แลนด์', '+31', 'EUR', 1, 1230),
    ('NZ', 'New Zealand', '新西兰', 'นิวซีแลนด์', '+64', 'NZD', 1, 1240),
    ('NI', 'Nicaragua', '尼加拉瓜', 'นิการากัว', '+505', 'NIO', 1, 1250),
    ('NE', 'Niger', '尼日尔', 'ไนเจอร์', '+227', 'XOF', 1, 1260),
    ('NG', 'Nigeria', '尼日利亚', 'ไนจีเรีย', '+234', 'NGN', 1, 1270),
    ('NO', 'Norway', '挪威', 'นอร์เวย์', '+47', 'NOK', 1, 1280),
    ('OM', 'Oman', '阿曼', 'โอมาน', '+968', 'OMR', 1, 1290),
    ('PK', 'Pakistan', '巴基斯坦', 'ปากีสถาน', '+92', 'PKR', 1, 1300),
    ('PW', 'Palau', '帕劳', 'ปาเลา', '+680', 'USD', 1, 1310),
    ('PA', 'Panama', '巴拿马', 'ปานามา', '+507', 'PAB', 1, 1320),
    ('PG', 'Papua New Guinea', '巴布亚新几内亚', 'ปาปัวนิวกินี', '+675', 'PGK', 1, 1330),
    ('PY', 'Paraguay', '巴拉圭', 'ปารากวัย', '+595', 'PYG', 1, 1340),
    ('PE', 'Peru', '秘鲁', 'เปรู', '+51', 'PEN', 1, 1350),
    ('PH', 'Philippines', '菲律宾', 'ฟิลิปปินส์', '+63', 'PHP', 1, 1360),
    ('PL', 'Poland', '波兰', 'โปแลนด์', '+48', 'PLN', 1, 1370),
    ('PT', 'Portugal', '葡萄牙', 'โปรตุเกส', '+351', 'EUR', 1, 1380),
    ('QA', 'Qatar', '卡塔尔', 'กาตาร์', '+974', 'QAR', 1, 1390),
    ('RO', 'Romania', '罗马尼亚', 'โรมาเนีย', '+40', 'RON', 1, 1400),
    ('RU', 'Russia', '俄罗斯', 'รัสเซีย', '+7', 'RUB', 1, 1410),
    ('RW', 'Rwanda', '卢旺达', 'รวันดา', '+250', 'RWF', 1, 1420),
    ('KN', 'Saint Kitts and Nevis', '圣基茨和尼维斯', 'เซนต์คิตส์และเนวิส', '+1-869', 'XCD', 1, 1430),
    ('LC', 'Saint Lucia', '圣卢西亚', 'เซนต์ลูเซีย', '+1-758', 'XCD', 1, 1440),
    ('VC', 'Saint Vincent and the Grenadines', '圣文森特和格林纳丁斯', 'เซนต์วินเซนต์และเกรนาดีนส์', '+1-784', 'XCD', 1, 1450),
    ('WS', 'Samoa', '萨摩亚', 'ซามัว', '+685', 'WST', 1, 1460),
    ('SM', 'San Marino', '圣马力诺', 'ซานมารีโน', '+378', 'EUR', 1, 1470),
    ('ST', 'Sao Tome and Principe', '圣多美和普林西比', 'เซาตูเมและปรินซิปี', '+239', 'STN', 1, 1480),
    ('SA', 'Saudi Arabia', '沙特阿拉伯', 'ซาอุดีอาระเบีย', '+966', 'SAR', 1, 1490),
    ('SN', 'Senegal', '塞内加尔', 'เซเนกัล', '+221', 'XOF', 1, 1500),
    ('RS', 'Serbia', '塞尔维亚', 'เซอร์เบีย', '+381', 'RSD', 1, 1510),
    ('SC', 'Seychelles', '塞舌尔', 'เซเชลส์', '+248', 'SCR', 1, 1520),
    ('SL', 'Sierra Leone', '塞拉利昂', 'เซียร์ราลีโอน', '+232', 'SLL', 1, 1530),
    ('SG', 'Singapore', '新加坡', 'สิงคโปร์', '+65', 'SGD', 1, 1540),
    ('SK', 'Slovakia', '斯洛伐克', 'สโลวาเกีย', '+421', 'EUR', 1, 1550),
    ('SI', 'Slovenia', '斯洛文尼亚', 'สโลวีเนีย', '+386', 'EUR', 1, 1560),
    ('SB', 'Solomon Islands', '所罗门群岛', 'หมู่เกาะโซโลมอน', '+677', 'SBD', 1, 1570),
    ('SO', 'Somalia', '索马里', 'โซมาเลีย', '+252', 'SOS', 1, 1580),
    ('ZA', 'South Africa', '南非', 'แอฟริกาใต้', '+27', 'ZAR', 1, 1590),
    ('SS', 'South Sudan', '南苏丹', 'ซูดานใต้', '+211', 'SSP', 1, 1600),
    ('ES', 'Spain', '西班牙', 'สเปน', '+34', 'EUR', 1, 1610),
    ('LK', 'Sri Lanka', '斯里兰卡', 'ศรีลังกา', '+94', 'LKR', 1, 1620),
    ('SD', 'Sudan', '苏丹', 'ซูดาน', '+249', 'SDG', 1, 1630),
    ('SR', 'Suriname', '苏里南', 'ซูรินาม', '+597', 'SRD', 1, 1640),
    ('SZ', 'Eswatini', '斯威士兰', 'เอสวาตินี', '+268', 'SZL', 1, 1650),
    ('SE', 'Sweden', '瑞典', 'สวีเดน', '+46', 'SEK', 1, 1660),
    ('CH', 'Switzerland', '瑞士', 'สวิตเซอร์แลนด์', '+41', 'CHF', 1, 1670),
    ('SY', 'Syria', '叙利亚', 'ซีเรีย', '+963', 'SYP', 1, 1680),
    ('TJ', 'Tajikistan', '塔吉克斯坦', 'ทาจิกิสถาน', '+992', 'TJS', 1, 1690),
    ('TZ', 'Tanzania', '坦桑尼亚', 'แทนซาเนีย', '+255', 'TZS', 1, 1700),
    ('TH', 'Thailand', '泰国', 'ไทย', '+66', 'THB', 1, 2),
    ('TL', 'Timor-Leste', '东帝汶', 'ติมอร์-เลสเต', '+670', 'USD', 1, 1710),
    ('TG', 'Togo', '多哥', 'โตโก', '+228', 'XOF', 1, 1720),
    ('TO', 'Tonga', '汤加', 'ตองกา', '+676', 'TOP', 1, 1730),
    ('TT', 'Trinidad and Tobago', '特立尼达和多巴哥', 'ตรินิแดดและโตเบโก', '+1-868', 'TTD', 1, 1740),
    ('TN', 'Tunisia', '突尼斯', 'ตูนิเซีย', '+216', 'TND', 1, 1750),
    ('TR', 'Turkey', '土耳其', 'ตุรกี', '+90', 'TRY', 1, 1760),
    ('TM', 'Turkmenistan', '土库曼斯坦', 'เติร์กเมนิสถาน', '+993', 'TMT', 1, 1770),
    ('TV', 'Tuvalu', '图瓦卢', 'ตูวาลู', '+688', 'AUD', 1, 1780),
    ('UG', 'Uganda', '乌干达', 'ยูกันดา', '+256', 'UGX', 1, 1790),
    ('UA', 'Ukraine', '乌克兰', 'ยูเครน', '+380', 'UAH', 1, 1800),
    ('AE', 'United Arab Emirates', '阿联酋', 'สหรัฐอาหรับเอมิเรตส์', '+971', 'AED', 1, 1810),
    ('GB', 'United Kingdom', '英国', 'สหราชอาณาจักร', '+44', 'GBP', 1, 1820),
    ('US', 'United States', '美国', 'สหรัฐอเมริกา', '+1', 'USD', 1, 3),
    ('UY', 'Uruguay', '乌拉圭', 'อุรุกวัย', '+598', 'UYU', 1, 1830),
    ('UZ', 'Uzbekistan', '乌兹别克斯坦', 'อุซเบกิสถาน', '+998', 'UZS', 1, 1840),
    ('VU', 'Vanuatu', '瓦努阿图', 'วานูอาตู', '+678', 'VUV', 1, 1850),
    ('VA', 'Vatican City', '梵蒂冈', 'นครรัฐวาติกัน', '+379', 'EUR', 1, 1860),
    ('VE', 'Venezuela', '委内瑞拉', 'เวเนซุเอลา', '+58', 'VES', 1, 1870),
    ('VN', 'Vietnam', '越南', 'เวียดนาม', '+84', 'VND', 1, 1880),
    ('YE', 'Yemen', '也门', 'เยเมน', '+967', 'YER', 1, 1890),
    ('ZM', 'Zambia', '赞比亚', 'แซมเบีย', '+260', 'ZMW', 1, 1900),
    ('ZW', 'Zimbabwe', '津巴布韦', 'ซิมบับเว', '+263', 'ZWL', 1, 1910),
]


def init_countries_data():
    """Initialize 195 countries data"""
    session = DatabaseService.get_session()
    try:
        print("=== Starting Countries Data Initialization ===")

        # Check if countries already exist
        existing_count = session.query(Country).count()
        if existing_count > 0:
            print(f"WARNING: Found {existing_count} existing countries in database")
            response = input("Do you want to clear existing data and re-import? (yes/no): ")
            if response.lower() != 'yes':
                print("Initialization cancelled by user")
                return False

            # Clear existing data
            print("Clearing existing countries data...")
            session.query(Country).delete()
            session.commit()
            print("Existing data cleared")

        # Insert countries data
        print(f"Inserting {len(COUNTRIES_DATA)} countries...")

        inserted_count = 0
        for data in COUNTRIES_DATA:
            country_code, name_en, name_zh, name_th, phone_code, currency_code, is_active, sort_order = data

            country = Country(
                country_code=country_code,
                country_name_en=name_en,
                country_name_zh=name_zh,
                country_name_th=name_th,
                phone_code=phone_code,
                currency_code=currency_code,
                is_active=is_active,
                sort_order=sort_order
            )
            session.add(country)
            inserted_count += 1

            if inserted_count % 50 == 0:
                print(f"  Inserted {inserted_count} countries...")

        session.commit()

        # Verify
        final_count = session.query(Country).count()
        print(f"\nSuccessfully initialized {final_count} countries!")
        print(f"Top 5 countries by sort_order:")

        top_countries = session.query(Country).order_by(Country.sort_order).limit(5).all()
        for c in top_countries:
            print(f"  {c.country_code}: {c.country_name_en} / {c.country_name_zh} (sort: {c.sort_order})")

        return True

    except Exception as e:
        print(f"ERROR: Error during initialization: {str(e)}")
        session.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        DatabaseService.close_session(session)


if __name__ == '__main__':
    print("Countries Data Initialization Script")
    print("=" * 60)
    success = init_countries_data()
    if success:
        print("\nCountries initialization completed successfully!")
    else:
        print("\nCountries initialization failed!")
    print("=" * 60)
