// 星座元数据常量

/** 12 星座完整列表（页面渲染顺序） */
const ZODIAC_LIST = [
  { key: 'aries',       name: '白羊座', icon: '♈', dateRange: '3.21-4.19' },
  { key: 'taurus',      name: '金牛座', icon: '♉', dateRange: '4.20-5.20' },
  { key: 'gemini',      name: '双子座', icon: '♊', dateRange: '5.21-6.21' },
  { key: 'cancer',      name: '巨蟹座', icon: '♋', dateRange: '6.22-7.22' },
  { key: 'leo',         name: '狮子座', icon: '♌', dateRange: '7.23-8.22' },
  { key: 'virgo',       name: '处女座', icon: '♍', dateRange: '8.23-9.22' },
  { key: 'libra',       name: '天秤座', icon: '♎', dateRange: '9.23-10.23' },
  { key: 'scorpio',     name: '天蝎座', icon: '♏', dateRange: '10.24-11.22' },
  { key: 'sagittarius', name: '射手座', icon: '♐', dateRange: '11.23-12.21' },
  { key: 'capricorn',   name: '摩羯座', icon: '♑', dateRange: '12.22-1.19' },
  { key: 'aquarius',    name: '水瓶座', icon: '♒', dateRange: '1.20-2.18' },
  { key: 'pisces',      name: '双鱼座', icon: '♓', dateRange: '2.19-3.20' },
];

/** key → 中文名映射 */
const ZODIAC_NAMES = {};
ZODIAC_LIST.forEach(z => { ZODIAC_NAMES[z.key] = z.name; });

/** key → 图标映射 */
const ZODIAC_ICONS = {};
ZODIAC_LIST.forEach(z => { ZODIAC_ICONS[z.key] = z.icon; });

module.exports = {
  ZODIAC_LIST,
  ZODIAC_NAMES,
  ZODIAC_ICONS,
};
