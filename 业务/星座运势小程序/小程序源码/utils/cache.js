// 本地缓存工具

/** 缓存键名常量 */
const CACHE_KEYS = {
  DAILY_FORTUNE: 'daily_fortune_cache',
  FORTUNE_DETAIL_PREFIX: 'fortune_detail_',
};

/** 默认缓存 TTL：6 小时 */
const DEFAULT_TTL = 6 * 60 * 60 * 1000;

/**
 * 写入缓存
 * @param {string} key - 缓存键
 * @param {*} data - 要缓存的数据
 * @param {number} [ttl] - 过期时间（毫秒），默认 6 小时
 */
function setCache(key, data, ttl) {
  const expiresAt = Date.now() + (ttl || DEFAULT_TTL);
  const cache = { data, expiresAt };
  try {
    wx.setStorageSync(key, cache);
  } catch (err) {
    console.warn('缓存写入失败:', err);
  }
}

/**
 * 读取缓存
 * @param {string} key - 缓存键
 * @returns {*|null} 缓存数据，过期或不存在返回 null
 */
function getCache(key) {
  try {
    const cache = wx.getStorageSync(key);
    if (!cache) return null;
    if (Date.now() > cache.expiresAt) {
      wx.removeStorageSync(key);
      return null;
    }
    return cache.data;
  } catch (err) {
    console.warn('缓存读取失败:', err);
    return null;
  }
}

/**
 * 清除指定缓存
 * @param {string} key
 */
function clearCache(key) {
  try {
    wx.removeStorageSync(key);
  } catch (err) {
    console.warn('缓存清除失败:', err);
  }
}

/**
 * 检查缓存是否有效
 * @param {string} key
 * @returns {boolean}
 */
function hasCache(key) {
  return getCache(key) !== null;
}

module.exports = {
  CACHE_KEYS,
  setCache,
  getCache,
  clearCache,
  hasCache,
};
