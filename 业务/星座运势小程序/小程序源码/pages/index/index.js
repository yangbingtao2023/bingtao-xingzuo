const app = getApp();
const { getDailyFortune } = require('../../utils/api');
const { getCache, setCache, CACHE_KEYS } = require('../../utils/cache');
const { ZODIAC_LIST } = require('../../utils/constants');

Page({
  data: {
    date: '',
    signs: [],
    loading: true,
    error: false,
    errorMsg: '',
  },

  onLoad() {
    this.loadFortunes();
  },

  onShow() {
    // 每次回到首页刷新日期显示
    this.setData({ date: this.formatDate(new Date()) });
  },

  async loadFortunes() {
    const today = this.formatDate(new Date());

    // 先查缓存
    const cached = getCache(CACHE_KEYS.DAILY_FORTUNE);
    if (cached && cached.date === today) {
      this.setData({
        signs: this.enrichZodiacList(cached.signs),
        date: today,
        loading: false,
      });
      return;
    }

    this.setData({ loading: true, error: false });

    try {
      const result = await getDailyFortune();
      if (result && result.code === 200) {
        const { signs, date: fortuneDate } = result.data;
        setCache(CACHE_KEYS.DAILY_FORTUNE, result.data, 6 * 60 * 60 * 1000);
        this.setData({
          signs: this.enrichZodiacList(signs),
          date: fortuneDate || today,
          loading: false,
        });
        return;
      }
    } catch (_) {
      // 云函数未部署，降级用模拟数据
    }

    // 模拟数据：云函数就绪后自动切换
    const mockSigns = ZODIAC_LIST.map(z => ({
      key: z.key,
      name: z.name,
      icon: z.icon,
      dateRange: z.dateRange,
      rating: 3 + Math.floor(Math.random() * 3), // 3-5
      hasData: true,
    }));
    this.setData({
      signs: mockSigns,
      date: today,
      loading: false,
      error: false,
    });
  },

  // 将 API 返回的数组按 ZODIAC_LIST 顺序排列，补全元数据
  enrichZodiacList(signs) {
    const signMap = {};
    if (signs && signs.length > 0) {
      signs.forEach(s => { signMap[s.sign_key] = s; });
    }
    return ZODIAC_LIST.map(z => {
      const data = signMap[z.key];
      return {
        key: z.key,
        name: z.name,
        icon: z.icon,
        dateRange: data ? data.date_range : z.dateRange,
        rating: data ? data.rating : 0,
        hasData: !!data,
      };
    });
  },

  formatDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  },

  onTapSign(e) {
    const { key } = e.currentTarget.dataset;
    if (!key) return;
    wx.navigateTo({
      url: `/pages/fortune/fortune?sign=${key}`,
    });
  },

  onPullDownRefresh() {
    this.loadFortunes().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  onShareAppMessage() {
    return {
      title: '今日星座运势，看看你的运气如何？',
      path: '/pages/index/index',
    };
  },
});
