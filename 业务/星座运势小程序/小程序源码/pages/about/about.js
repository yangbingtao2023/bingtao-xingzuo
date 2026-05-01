Page({
  data: {
    appVersion: '1.0.0',
    updateDate: '2026-05-01',
  },

  onShareAppMessage() {
    return {
      title: '每日星座运势，看看你的星座今天如何？',
      path: '/pages/index/index',
    };
  },
});
