// API 工具函数：封装云函数调用

/**
 * 调用云函数获取当日全部星座运势
 * @returns {Promise<{code: number, data: object}>}
 */
function getDailyFortune() {
  return new Promise((resolve, reject) => {
    if (!wx.cloud) {
      resolve({
        code: 500,
        message: '云开发未初始化，请在 app.js 中配置 env ID',
      });
      return;
    }
    wx.cloud.callFunction({
      name: 'getDailyFortune',
      data: {},
      success: (res) => resolve(res.result),
      fail: (err) => reject(err),
    });
  });
}

/**
 * 调用云函数获取单个星座运势详情
 * @param {string} signKey - 星座 key（如 'aries'）
 * @param {string} [date] - 日期 YYYY-MM-DD，默认今天
 * @returns {Promise<{code: number, data: object}>}
 */
function getFortuneDetail(signKey, date) {
  return new Promise((resolve, reject) => {
    if (!wx.cloud) {
      resolve({
        code: 500,
        message: '云开发未初始化',
      });
      return;
    }
    wx.cloud.callFunction({
      name: 'getFortuneDetail',
      data: { sign_key: signKey, date },
      success: (res) => resolve(res.result),
      fail: (err) => reject(err),
    });
  });
}

module.exports = {
  getDailyFortune,
  getFortuneDetail,
};
