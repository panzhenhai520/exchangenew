#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ISO 3166-1 Alpha-2 国家代码和对应的货币信息
数据来源: ISO 3166-1 标准
"""

ISO_COUNTRIES_CURRENCIES = [
    {
        'country_code': 'AD',
        'country_name_en': 'Andorra',
        'country_name_zh': '安道尔',
        'country_name_th': 'อันดอร์รา',
        'currency_code': 'EUR',
        'currency_name_en': 'Euro',
        'currency_name_zh': '欧元',
        'currency_name_th': 'ยูโร',
        'currency_symbol': '€'
    },
    {
        'country_code': 'AE',
        'country_name_en': 'United Arab Emirates',
        'country_name_zh': '阿联酋',
        'country_name_th': 'สหรัฐอาหรับเอมิเรตส์',
        'currency_code': 'AED',
        'currency_name_en': 'UAE Dirham',
        'currency_name_zh': '阿联酋迪拉姆',
        'currency_name_th': 'เดอร์แฮมสหรัฐอาหรับเอมิเรตส์',
        'currency_symbol': 'د.إ'
    },
    {
        'country_code': 'AU',
        'country_name_en': 'Australia',
        'country_name_zh': '澳大利亚',
        'country_name_th': 'ออสเตรเลีย',
        'currency_code': 'AUD',
        'currency_name_en': 'Australian Dollar',
        'currency_name_zh': '澳大利亚元',
        'currency_name_th': 'ดอลลาร์ออสเตรเลีย',
        'currency_symbol': 'A$'
    },
    {
        'country_code': 'BR',
        'country_name_en': 'Brazil',
        'country_name_zh': '巴西',
        'country_name_th': 'บราซิล',
        'currency_code': 'BRL',
        'currency_name_en': 'Brazilian Real',
        'currency_name_zh': '巴西雷亚尔',
        'currency_name_th': 'เรียลบราซิล',
        'currency_symbol': 'R$'
    },
    {
        'country_code': 'CA',
        'country_name_en': 'Canada',
        'country_name_zh': '加拿大',
        'country_name_th': 'แคนาดา',
        'currency_code': 'CAD',
        'currency_name_en': 'Canadian Dollar',
        'currency_name_zh': '加拿大元',
        'currency_name_th': 'ดอลลาร์แคนาดา',
        'currency_symbol': 'C$'
    },
    {
        'country_code': 'CH',
        'country_name_en': 'Switzerland',
        'country_name_zh': '瑞士',
        'country_name_th': 'สวิตเซอร์แลนด์',
        'currency_code': 'CHF',
        'currency_name_en': 'Swiss Franc',
        'currency_name_zh': '瑞士法郎',
        'currency_name_th': 'ฟรังก์สวิส',
        'currency_symbol': 'CHF'
    },
    {
        'country_code': 'CN',
        'country_name_en': 'China',
        'country_name_zh': '中国',
        'country_name_th': 'จีน',
        'currency_code': 'CNY',
        'currency_name_en': 'Chinese Yuan',
        'currency_name_zh': '人民币',
        'currency_name_th': 'หยวนจีน',
        'currency_symbol': '¥'
    },
    {
        'country_code': 'DK',
        'country_name_en': 'Denmark',
        'country_name_zh': '丹麦',
        'country_name_th': 'เดนมาร์ก',
        'currency_code': 'DKK',
        'currency_name_en': 'Danish Krone',
        'currency_name_zh': '丹麦克朗',
        'currency_name_th': 'โครนเดนมาร์ก',
        'currency_symbol': 'kr'
    },
    {
        'country_code': 'EU',
        'country_name_en': 'European Union',
        'country_name_zh': '欧盟',
        'country_name_th': 'สหภาพยุโรป',
        'currency_code': 'EUR',
        'currency_name_en': 'Euro',
        'currency_name_zh': '欧元',
        'currency_name_th': 'ยูโร',
        'currency_symbol': '€'
    },
    {
        'country_code': 'GB',
        'country_name_en': 'United Kingdom',
        'country_name_zh': '英国',
        'country_name_th': 'สหราชอาณาจักร',
        'currency_code': 'GBP',
        'currency_name_en': 'British Pound',
        'currency_name_zh': '英镑',
        'currency_name_th': 'ปอนด์อังกฤษ',
        'currency_symbol': '£'
    },
    {
        'country_code': 'HK',
        'country_name_en': 'Hong Kong',
        'country_name_zh': '香港',
        'country_name_th': 'ฮ่องกง',
        'currency_code': 'HKD',
        'currency_name_en': 'Hong Kong Dollar',
        'currency_name_zh': '港币',
        'currency_name_th': 'ดอลลาร์ฮ่องกง',
        'currency_symbol': 'HK$'
    },
    {
        'country_code': 'IN',
        'country_name_en': 'India',
        'country_name_zh': '印度',
        'country_name_th': 'อินเดีย',
        'currency_code': 'INR',
        'currency_name_en': 'Indian Rupee',
        'currency_name_zh': '印度卢比',
        'currency_name_th': 'รูปีอินเดีย',
        'currency_symbol': '₹'
    },
    {
        'country_code': 'JP',
        'country_name_en': 'Japan',
        'country_name_zh': '日本',
        'country_name_th': 'ญี่ปุ่น',
        'currency_code': 'JPY',
        'currency_name_en': 'Japanese Yen',
        'currency_name_zh': '日元',
        'currency_name_th': 'เยนญี่ปุ่น',
        'currency_symbol': '¥'
    },
    {
        'country_code': 'KR',
        'country_name_en': 'South Korea',
        'country_name_zh': '韩国',
        'country_name_th': 'เกาหลีใต้',
        'currency_code': 'KRW',
        'currency_name_en': 'South Korean Won',
        'currency_name_zh': '韩元',
        'currency_name_th': 'วอนเกาหลีใต้',
        'currency_symbol': '₩'
    },
    {
        'country_code': 'MY',
        'country_name_en': 'Malaysia',
        'country_name_zh': '马来西亚',
        'country_name_th': 'มาเลเซีย',
        'currency_code': 'MYR',
        'currency_name_en': 'Malaysian Ringgit',
        'currency_name_zh': '马来西亚林吉特',
        'currency_name_th': 'ริงกิตมาเลเซีย',
        'currency_symbol': 'RM'
    },
    {
        'country_code': 'NO',
        'country_name_en': 'Norway',
        'country_name_zh': '挪威',
        'country_name_th': 'นอร์เวย์',
        'currency_code': 'NOK',
        'currency_name_en': 'Norwegian Krone',
        'currency_name_zh': '挪威克朗',
        'currency_name_th': 'โครนนอร์เวย์',
        'currency_symbol': 'kr'
    },
    {
        'country_code': 'NZ',
        'country_name_en': 'New Zealand',
        'country_name_zh': '新西兰',
        'country_name_th': 'นิวซีแลนด์',
        'currency_code': 'NZD',
        'currency_name_en': 'New Zealand Dollar',
        'currency_name_zh': '新西兰元',
        'currency_name_th': 'ดอลลาร์นิวซีแลนด์',
        'currency_symbol': 'NZ$'
    },
    {
        'country_code': 'PH',
        'country_name_en': 'Philippines',
        'country_name_zh': '菲律宾',
        'country_name_th': 'ฟิลิปปินส์',
        'currency_code': 'PHP',
        'currency_name_en': 'Philippine Peso',
        'currency_name_zh': '菲律宾比索',
        'currency_name_th': 'เปโซฟิลิปปินส์',
        'currency_symbol': '₱'
    },
    {
        'country_code': 'RU',
        'country_name_en': 'Russia',
        'country_name_zh': '俄罗斯',
        'country_name_th': 'รัสเซีย',
        'currency_code': 'RUB',
        'currency_name_en': 'Russian Ruble',
        'currency_name_zh': '俄罗斯卢布',
        'currency_name_th': 'รูเบิลรัสเซีย',
        'currency_symbol': '₽'
    },
    {
        'country_code': 'SE',
        'country_name_en': 'Sweden',
        'country_name_zh': '瑞典',
        'country_name_th': 'สวีเดน',
        'currency_code': 'SEK',
        'currency_name_en': 'Swedish Krona',
        'currency_name_zh': '瑞典克朗',
        'currency_name_th': 'โครนาสวีเดน',
        'currency_symbol': 'kr'
    },
    {
        'country_code': 'SG',
        'country_name_en': 'Singapore',
        'country_name_zh': '新加坡',
        'country_name_th': 'สิงคโปร์',
        'currency_code': 'SGD',
        'currency_name_en': 'Singapore Dollar',
        'currency_name_zh': '新加坡元',
        'currency_name_th': 'ดอลลาร์สิงคโปร์',
        'currency_symbol': 'S$'
    },
    {
        'country_code': 'TH',
        'country_name_en': 'Thailand',
        'country_name_zh': '泰国',
        'country_name_th': 'ไทย',
        'currency_code': 'THB',
        'currency_name_en': 'Thai Baht',
        'currency_name_zh': '泰铢',
        'currency_name_th': 'บาทไทย',
        'currency_symbol': '฿'
    },
    {
        'country_code': 'TW',
        'country_name_en': 'Taiwan',
        'country_name_zh': '台湾',
        'country_name_th': 'ไต้หวัน',
        'currency_code': 'TWD',
        'currency_name_en': 'Taiwan Dollar',
        'currency_name_zh': '台币',
        'currency_name_th': 'ดอลลาร์ไต้หวัน',
        'currency_symbol': 'NT$'
    },
    {
        'country_code': 'US',
        'country_name_en': 'United States',
        'country_name_zh': '美国',
        'country_name_th': 'สหรัฐอเมริกา',
        'currency_code': 'USD',
        'currency_name_en': 'US Dollar',
        'currency_name_zh': '美元',
        'currency_name_th': 'ดอลลาร์สหรัฐ',
        'currency_symbol': '$'
    },
    {
        'country_code': 'VN',
        'country_name_en': 'Vietnam',
        'country_name_zh': '越南',
        'country_name_th': 'เวียดนาม',
        'currency_code': 'VND',
        'currency_name_en': 'Vietnamese Dong',
        'currency_name_zh': '越南盾',
        'currency_name_th': 'ดองเวียดนาม',
        'currency_symbol': '₫'
    },
    {
        'country_code': 'ZA',
        'country_name_en': 'South Africa',
        'country_name_zh': '南非',
        'country_name_th': 'แอฟริกาใต้',
        'currency_code': 'ZAR',
        'currency_name_en': 'South African Rand',
        'currency_name_zh': '南非兰特',
        'currency_name_th': 'แรนด์แอฟริกาใต้',
        'currency_symbol': 'R'
    }
]


def get_country_by_code(country_code):
    """根据国家代码获取国家信息"""
    for country in ISO_COUNTRIES_CURRENCIES:
        if country['country_code'] == country_code.upper():
            return country
    return None


def get_currency_by_code(currency_code):
    """根据货币代码获取货币信息"""
    for country in ISO_COUNTRIES_CURRENCIES:
        if country['currency_code'] == currency_code.upper():
            return country
    return None


def get_all_countries():
    """获取所有国家列表"""
    return ISO_COUNTRIES_CURRENCIES


def get_unique_currencies():
    """获取去重的货币列表"""
    currencies = {}
    for country in ISO_COUNTRIES_CURRENCIES:
        currency_code = country['currency_code']
        if currency_code not in currencies:
            currencies[currency_code] = country
    return list(currencies.values()) 