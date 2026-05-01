// 运势内容展示组件
Component({
  properties: {
    fortune: {
      type: Object,
      value: null,
      observer(newVal) {
        if (newVal) {
          this.processFortune(newVal);
        }
      },
    },
  },

  data: {
    rating: 0,
    luckyNumber: null,
    luckyColor: '',
    element: '',
    planet: '',
    dateRange: '',
    tags: [],
    content: '',
  },

  methods: {
    processFortune(f) {
      this.setData({
        rating: f.rating || 0,
        luckyNumber: f.lucky_number,
        luckyColor: f.lucky_color || '',
        element: f.element || '',
        planet: f.planet || '',
        dateRange: f.date_range || '',
        tags: f.tags || [],
        content: f.content || '',
      });
    },
  },
});
