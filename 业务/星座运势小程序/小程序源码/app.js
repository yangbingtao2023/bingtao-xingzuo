// 小程序入口
App({
  onLaunch() {
    // 初始化云开发
    if (wx.cloud) {
      wx.cloud.init({
        env: 'yangbingtao-d1gmeitgw3a00bb90',
        traceUser: true,
      });
    }

    // 获取系统信息
    const windowInfo = wx.getWindowInfo();
    const deviceInfo = wx.getDeviceInfo();
    const appBaseInfo = wx.getAppBaseInfo();
    this.globalData.statusBarHeight = windowInfo.statusBarHeight;
    this.globalData.navBarHeight = deviceInfo.platform === 'ios' ? 44 : 48;
    this.globalData.platform = deviceInfo.platform;
    this.globalData.fontSizeSetting = appBaseInfo.fontSizeSetting;
  },

  globalData: {
    statusBarHeight: 0,
    navBarHeight: 0,
    platform: '',
    fontSizeSetting: 0,
    // 今日运势缓存
    dailyFortune: null,
    dailyFortuneDate: null,
  },
});
