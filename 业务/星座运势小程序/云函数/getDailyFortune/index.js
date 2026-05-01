// 云函数：getDailyFortune
// 返回当天全部 12 星座运势数据
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event) => {
  const { date } = event;
  const wxContext = cloud.getWXContext();

  // 使用今天的日期，或传入的日期
  const today = date || new Date().toISOString().slice(0, 10);

  try {
    // 查询当天运势数据
    const { data: fortunes } = await db.collection('fortunes')
      .where({ date: today })
      .limit(12)
      .get();

    if (fortunes.length > 0) {
      return {
        code: 200,
        data: {
          date: today,
          signs: fortunes.map(f => ({
            sign_key: f.sign_key,
            sign_zh: f.sign_zh,
            sign_en: f.sign_en,
            date_range: f.date_range,
            element: f.element,
            planet: f.planet,
            lucky_number: f.lucky_number,
            lucky_color: f.lucky_color,
            rating: f.rating,
            content: f.content,
            tags: f.tags || [],
          })),
        },
      };
    }

    // 无当天数据 —— 尝试从 daily_meta 获取最新日期
    const { data: metaList } = await db.collection('daily_meta')
      .where({ _id: 'current' })
      .get();

    if (metaList.length > 0) {
      const fallbackDate = metaList[0].date;
      const { data: fallbackFortunes } = await db.collection('fortunes')
        .where({ date: fallbackDate })
        .limit(12)
        .get();

      return {
        code: 200,
        data: {
          date: fallbackDate,
          fetch_status: 'fallback',
          signs: fallbackFortunes.map(f => ({
            sign_key: f.sign_key,
            sign_zh: f.sign_zh,
            sign_en: f.sign_en,
            date_range: f.date_range,
            element: f.element,
            planet: f.planet,
            lucky_number: f.lucky_number,
            lucky_color: f.lucky_color,
            rating: f.rating,
            content: f.content,
            tags: f.tags || [],
          })),
        },
      };
    }

    // 完全无数据 —— 返回昨天日期
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yestDate = yesterday.toISOString().slice(0, 10);

    const { data: yestFortunes } = await db.collection('fortunes')
      .where({ date: yestDate })
      .limit(12)
      .get();

    if (yestFortunes.length > 0) {
      return {
        code: 200,
        data: {
          date: yestDate,
          fetch_status: 'stale',
          signs: yestFortunes.map(f => ({
            sign_key: f.sign_key,
            sign_zh: f.sign_zh,
            sign_en: f.sign_en,
            date_range: f.date_range,
            element: f.element,
            planet: f.planet,
            lucky_number: f.lucky_number,
            lucky_color: f.lucky_color,
            rating: f.rating,
            content: f.content,
            tags: f.tags || [],
          })),
        },
      };
    }

    return {
      code: 404,
      message: '暂无运势数据，请稍后再来',
    };
  } catch (err) {
    console.error('getDailyFortune error:', err);
    return {
      code: 500,
      message: '服务异常，请稍后重试',
    };
  }
};
