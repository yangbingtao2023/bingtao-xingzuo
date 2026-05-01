// 星座卡片组件
Component({
  properties: {
    signKey: { type: String, value: '' },
    name: { type: String, value: '' },
    icon: { type: String, value: '' },
    dateRange: { type: String, value: '' },
    rating: { type: Number, value: 0 },
    hasData: { type: Boolean, value: false },
  },

  methods: {
    onTap() {
      this.triggerEvent('tap', { signKey: this.properties.signKey });
    },
  },
});
