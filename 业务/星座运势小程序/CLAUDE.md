# 星座运势小程序

> 微信工具型小程序：12 星座每日运势查询
> 变现：流量主广告 + 后续付费深度报告

## 子目录

| 目录 | 说明 | 状态 |
|------|------|------|
| 设计/ | 产品设计 + 架构设计 | ✅ |
| 数据管道/ | Python：抓取 → 标准化 → 发布到云开发 | ✅ |
| 云函数/ | Node.js：getDailyFortune / getFortuneDetail | ✅ |
| 小程序源码/ | 前端：WXML/WXSS/JS + Vant Weapp | ✅ |
| 运营素材/ | 分享图、文案 | 待建 |

## 快速开始

### 1. 数据管道

```bash
cd 数据管道
uv sync
# 先确保 fetcher 已产出 latest.json，然后：
uv run python transform_horoscope.py            # 转换数据
uv run python publish_to_cloudbase.py validate   # 验证格式
uv run python publish_to_cloudbase.py publish --dry-run  # 试运行
```

### 2. 云函数

在微信开发者工具中，右键 `云函数/` 下的函数目录 → 上传并部署。

### 3. 小程序

在微信开发者工具中导入 `小程序源码/miniprogram/` 目录。

### 4. 打开前配置

1. `app.js` → `wx.cloud.init({ env: '你的环境ID' })`
2. `app.json` → 填入真实的 `adunit-xxx`（UV >= 1000 后）
3. 补齐 `images/` 下的 tabBar 图标

## 依赖

| 端 | 技术 | 关键依赖 |
|----|------|---------|
| 数据管道 | Python 3.12 + uv | requests, feedparser |
| 云函数 | Node.js | wx-server-sdk |
| 小程序 | 原生 | Vant Weapp (npm) |

## 相关

- 上游数据源：`工具/app/xiangyu-horoscope-fetcher/`（RSS 抓取）
- 内容 API：天聚数行 TianAPI（100 次/天免费）
- UI 组件库：Vant Weapp v1.x

## 变更记录

| 日期 | 变更内容 |
|------|---------|
| 2026-05-01 | 初始创建：MVP 全链路 |
