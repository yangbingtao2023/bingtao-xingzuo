const { getDailyFortune } = require('../../utils/api');
const { getCache, setCache, CACHE_KEYS } = require('../../utils/cache');
const { ZODIAC_ICONS, ZODIAC_NAMES, ZODIAC_LIST } = require('../../utils/constants');

Page({
  data: {
    signKey: '',
    signName: '',
    signIcon: '',
    fortune: null,
    loading: true,
    error: false,
    errorMsg: '',
  },

  onLoad(options) {
    const { sign } = options;
    if (!sign) {
      wx.navigateBack();
      return;
    }
    this.setData({
      signKey: sign,
      signName: ZODIAC_NAMES[sign] || sign,
      signIcon: ZODIAC_ICONS[sign] || '✨',
    });
    this.loadFortune(sign);
  },

  async loadFortune(signKey) {
    this.setData({ loading: true, error: false });

    try {
      // 优先从缓存中取当日全部数据里找
      const cached = getCache(CACHE_KEYS.DAILY_FORTUNE);
      if (cached && cached.signs) {
        const found = cached.signs.find(s => s.sign_key === signKey);
        if (found) {
          this.setData({ fortune: found, loading: false });
          return;
        }
      }

      // 缓存未命中，调云函数
      const result = await getDailyFortune();
      if (result.code === 200 && result.data.signs) {
        const found = result.data.signs.find(s => s.sign_key === signKey);
        if (found) {
          setCache(CACHE_KEYS.DAILY_FORTUNE, result.data, 6 * 60 * 60 * 1000);
          this.setData({ fortune: found, loading: false });
          return;
        }
      }

    } catch (_) {
      // 云函数未部署，降级用模拟数据
    }

    // 模拟数据
    const meta = ZODIAC_LIST.find(z => z.key === signKey) || {};
    const mockContent = [
      '今天整体运势不错，适合主动出击。工作上可能会有意外惊喜，财运方面宜守不宜攻。感情方面多沟通会有收获。',
      '今天适合沉淀和思考。工作上按部就班即可，不宜冒进。感情方面给对方多一些空间，健康注意饮食规律。',
      '今天贵人运旺盛，多与人交流会带来新机会。工作上有创意灵感，财运小吉。注意休息，别熬夜。',
    ];
    const rng = Math.floor(Math.random() * 3);
    this.setData({
      fortune: {
        sign_key: signKey,
        sign_zh: meta.name || signKey,
        date_range: meta.dateRange || '',
        element: ['火象', '土象', '风象', '水象'][rng],
        planet: ['火星', '金星', '水星', '木星'][rng],
        lucky_number: Math.floor(Math.random() * 9) + 1,
        lucky_color: ['金色', '红色', '蓝色', '绿色'][rng],
        rating: 3 + Math.floor(Math.random() * 3),
        content: mockContent[rng],
        tags: [['爱情', '事业'], ['财运', '健康'], ['综合', '事业']][rng],
      },
      loading: false,
    });
  },

  onShareAppMessage() {
    const { signKey, signName, fortune } = this.data;
    const rating = fortune ? '★'.repeat(fortune.rating) + '☆'.repeat(5 - fortune.rating) : '';
    return {
      title: `${signName}今日运势 ${rating}`,
      path: `/pages/fortune/fortune?sign=${signKey}`,
    };
  },
});
