// 云函数：getFortuneDetail
// 返回单个星座的详细运势
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event) => {
  const { sign_key, date } = event;

  if (!sign_key) {
    return { code: 400, message: '请提供 sign_key 参数' };
  }

  const queryDate = date || new Date().toISOString().slice(0, 10);
  const docId = `${queryDate}_${sign_key}`;

  try {
    // 精确查询
    const { data } = await db.collection('fortunes')
      .where({ _id: docId })
      .get();

    if (data.length > 0) {
      const f = data[0];
      return {
        code: 200,
        data: {
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
        },
      };
    }

    return {
      code: 404,
      message: `暂无 ${queryDate} 的 ${sign_key} 运势数据`,
    };
  } catch (err) {
    console.error('getFortuneDetail error:', err);
    return {
      code: 500,
      message: '服务异常，请稍后重试',
    };
  }
};
