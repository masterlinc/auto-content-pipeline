<!-- AUTO-CONTENT-PIPELINE TEMPLATE -->
<!-- 这是样例，复制到你的 vault _config/ 后请按你的账号改 -->
<!-- 风格文件必须改：style-document.md / style-cover.md -->
<!-- 配置文件建议改：style-config.yaml / sources.json -->

# 封面风格规范（锁定版）

> **⚠️ 这是固化版本。要改必须跟 linc 确认。**

## 基本规格

- **比例**：3:4（小红书官方推荐）
- **尺寸**：1242 × 1660 像素
- **格式**：PNG
- **文件大小**：≤ 1MB

## 配色（3 套主色板，按事件类型选）

### 🔥 突发新闻 / 国际局势
- 主色：`#FF3B30`（警示红）
- 辅色：`#1A1A1A`（深黑）、`#FFFFFF`（白）
- 强调：`#FFD60A`（亮黄）
- 情绪：紧张、震撼

### ⚡ 科技 / 财经
- 主色：`#0A84FF`（科技蓝）
- 辅色：``#1C1C1E``（暗灰）、`#FFFFFF`
- 强调：`#30D158`（增长绿）或 `#FF453A`（跌红）
- 情绪：理性、专业

### 📍 民生 / 社会
- 主色：`#FF9500`（温暖橙）
- 辅色：`#FFFFFF`、`#2C2C2E`
- 强调：`#FFCC00`（阳光黄）
- 情绪：贴近、有温度

## 必含元素

1. **主标题**：6-12 个字，最大字号（占封面 1/3 高度）
2. **副标题/数据**：一行数字或关键词，次级字号
3. **装饰元素**：1-2 个大 emoji（🔥💥⚡📍💡🎯）作为视觉焦点
4. **底色块**：上方 1/3 区域纯色背景，让标题突出
5. **信息源角标**：右下角小字 "📍 <来源>"（如"📍 BBC""📍 央视新闻"）

## 字体选择

- **主标题**：思源黑体 Bold（CN 通用）或阿里巴巴普惠体 Bold
- **副标题**：思源黑体 Medium
- **数据**：DIN Alternate Bold（数字专用，视觉冲击强）
- **角标**：思源黑体 Regular，字号 ≤ 24px

> ⚠️ agent 生成时不要硬编码字体（中文 web font 不稳），用通用 fallback：黑体 / Sans-serif Bold。

## 布局（3 个模板）

### 模板 A：上 1/3 纯色 + 大标题

```
┌─────────────────────────┐
│ [纯色背景 1/3]            │
│                          │
│ 🔥 [主标题大字]            │
│ ──────────────           │
│ ⚡ [副标题/数据]           │
├─────────────────────────┤
│                          │
│  [主体视觉：插画/3D/图片]   │
│                          │
│         [来源角标] 📍 XX │
└─────────────────────────┘
```

适用：突发新闻、社会事件

### 模板 B：左侧色块 + 右侧大字

```
┌──────┬──────────────────┐
│      │                  │
│ 🔥   │   [主标题大字]     │
│      │                  │
│ 1/3  │  ──────────────  │
│ 纯色 │   [副标题]         │
│ 块   │                  │
│      │                  │
│      │   [视觉元素]       │
│      │           📍 XX   │
└──────┴──────────────────┘
```

适用：科技产品、数据新闻

### 模板 C：全图 + 浮层文字

```
┌─────────────────────────┐
│                          │
│  [震撼背景图：新闻现场/   │
│   科技产品/数据可视化]    │
│                          │
│    [半透明黑色蒙层]        │
│                          │
│ 🔥 [主标题大字]            │
│    [副标题]              │
│                  📍 XX   │
└─────────────────────────┘
```

适用：国际局势、明星八卦、视觉化数据

## 视觉元素提示词模板

### 突发新闻
```
Background: dramatic gradient from #FF3B30 to #1A1A1A,
floating particles, newsroom ambient,
foreground: large bold Chinese typography "[主标题]",
accent: ⚡ emoji 3D rendered, gloss finish,
mood: urgent, breaking news,
style: modern flat illustration + photographic overlay
```

### 科技产品
```
Background: clean #0A84FF gradient,
abstract geometric shapes, holographic effect,
foreground: minimal product silhouette,
text: bold modern typography "[产品名]",
accent: ✨ glowing effect,
mood: futuristic, professional,
style: Apple keynote style, soft 3D
```

### 民生社会
```
Background: warm #FF9500 gradient,
soft shapes, human silhouette, urban context,
text: friendly bold typography "[主题]",
accent: 🌅 sunrise motif,
mood: warm, relatable,
style: editorial illustration, slightly retro
```

## Style Version

```
version: 1.0
frozen_at: 2026-08-22
last_modified_by: linc
```

## 严禁

- ❌ 真实人脸（肖像权）
- ❌ 品牌 logo / 商标（小红书审核会卡）
- ❌ 黑白色调（饱和度低、点击率差）
- ❌ 元素堆砌（最多 5 个元素）
- ❌ 文字超过 4 行（封面是视觉不是阅读）

## 修改流程

linc 改 → 更新 version → 通知 agent 重读。
agent **不会**自动改这份。