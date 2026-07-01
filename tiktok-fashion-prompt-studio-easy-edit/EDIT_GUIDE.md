# 修改指南：怎么改这个工具

这个版本已经改成“方便修改”的结构。正常情况下，你不需要改 `app.py` 代码。

## 1. 最常改的文件

### 改选项库
编辑：`data/options.json`

适合修改：

- 视频目标
- 内容大类
- 细分脚本类型
- 人物人设
- 人物关系
- 拍摄场景
- 拍摄结构
- 镜头语言
- 情绪风格
- 剧情冲突
- 服装卖点重点
- 口播风格
- 字幕风格
- CTA 风格
- AI 稳定性

### 改默认选择
编辑：`data/defaults.json`

适合修改：

- 默认视频目标
- 默认内容大类
- 默认输出数量
- 默认拍摄结构
- 默认稳定性模式
- 默认输出格式

### 改提示词
编辑：`prompt_templates/` 目录：

- `clothing_profile.md`：上传图片后，服装资产卡分析提示词
- `auto_recommend.md`：点击“AI 自动推荐设置”的提示词
- `video_prompt_generator.md`：最终生成 Seedance2.0 视频提示词的提示词

## 2. 在 GitHub 网页里怎么改

1. 打开你的 GitHub 仓库。
2. 点击要修改的文件，比如 `data/options.json`。
3. 点右上角铅笔图标。
4. 修改内容。
5. 点 `Commit changes`。
6. 等 Streamlit Cloud 自动更新，刷新网页。

## 3. 修改 `data/options.json` 的规则

这是 JSON 文件，必须注意：

- 字符串要用英文双引号 `"`。
- 每一项之间要有英文逗号 `,`。
- 最后一项后面不要加逗号。
- 不要使用中文引号。

正确：

```json
"SCENES": [
  "bedroom mirror",
  "car selfie",
  "coffee shop entrance"
]
```

错误：

```json
"SCENES": [
  “bedroom mirror”,
  “car selfie”,
]
```

## 4. 修改提示词的规则

### `auto_recommend.md`
必须保留：

```text
{clothing_profile}
```

### `video_prompt_generator.md`
必须保留：

```text
{clothing_profile}
{user_settings}
```

这些是程序自动插入服装资产卡和用户设置的位置。删掉后，生成效果会变差。

## 5. 什么时候需要改 `app.py`

只有这些情况才需要改 `app.py`：

- 新增一个页面模块
- 新增一个按钮
- 新增登录逻辑
- 新增数据库
- 新增生成视频 API
- 改整体页面布局

平时只改选项和提示词，不需要动 `app.py`。
