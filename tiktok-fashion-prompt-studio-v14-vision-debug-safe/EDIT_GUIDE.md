# V5 修改指南

## 1. 改最终输出格式

打开：

```text
prompt_templates/video_prompt_generator.md
```

这里控制最终生成的 Seedance 2.0 提示词格式。

## 2. 改款式资产分析

打开：

```text
prompt_templates/clothing_profile.md
```

这里控制上传图片后，AI 怎么分析衣服。当前版本已禁止描述颜色。

## 3. 增加人物关系 / 剧情冲突

打开：

```text
data/options.json
```

找到：

```json
"RELATIONSHIPS": []
```

或：

```json
"CONFLICTS": []
```

添加新的文字即可。注意 JSON 每一项之间要有英文逗号。

## 4. 改默认选项

打开：

```text
data/defaults.json
```

当前默认：

- 拍摄结构：自动判断
- AI 稳定性：平衡模式
- 口播风格：自动判断
- 字幕风格：不要字幕
- 人设：默认不选，由页面逻辑使用参考图人物

## 5. 更新 GitHub 后怎么生效

在 GitHub 网页里修改或上传覆盖文件后，点 Commit changes。Streamlit 通常会自动重启；如果没更新，去 Streamlit Cloud 点 Reboot app。


## V6 额外说明
如果你后续还想继续强化“场景不重复”和“15 秒控时”，重点改这两个文件：
- prompt_templates/auto_recommend.md
- prompt_templates/video_prompt_generator.md


## V7 更新
- 移除具体场景示例锚定，强化批量场景去重，避免 AI 偷懒反复生成同一类场景。
- 强化 15 秒台词控时：英文总词数建议 28-45，最多 55 词；单条只展开 1-2 个服装卖点。
- 页面明确：只生成文本提示词，不生成图片或视频。


## V8 更新
- 场景不再依赖固定内置库，改为基于多维变量随机裂变，降低独立多次生成时的场景重复概率。
- 新增兼容性过滤：若内容类型 / 人群 / 卖点与款式资产卡不匹配，自动跳过并重组，不强行输出冲突结果。
- 继续保持 15 秒台词控时与只输出文本提示词。


## V9 更新
- 新增两步生成：先进行本批场景深度规划，再生成 Seedance 2.0 文本提示词。
- 场景不是固定库硬选，而是从大生活分类进入，继续深挖具体场所、装修、布局、物件、光线、声音、动作。
- 资产卡兼容过滤优先：如果人群、内容类型、卖点与产品不匹配，自动跳过并重组。
- 仍然只生成文本提示词，不生成图片或视频。


## V10 更新
- CTA 不再一刀切禁止。系统会根据视频目标判断：原生种草保持轻 CTA，TikTok Shop 转化/评论区回复/促销场景可以自然出现 link、sale、Buy all the colors 等表达。
- 仍禁止无依据、夸张、机械的广告腔，例如绝对化承诺和反复催买。



## V11 更新：高端 API 配置中心

V11 新增 `API Control Center`，用于展示火山方舟 / 豆包 Seed 2.1 Pro 接入状态。

推荐 Streamlit Secrets：

```toml
ARK_API_KEY = "你的火山方舟 API Key"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_SEED21_PRO_MODEL_ID = "你的豆包 Seed 2.1 Pro 模型ID或Endpoint ID"
APP_PASSWORD = "你设置的网页访问密码"
```

可选分离模型：

```toml
ARK_TEXT_MODEL_ID = "文本生成模型ID或Endpoint ID"
ARK_VISION_MODEL_ID = "图片理解模型ID或Endpoint ID"
```

只填 `DOUBAO_SEED21_PRO_MODEL_ID` 时，系统会同时用于图片资产分析、场景深度规划和 Seedance 文本提示词生成。



## V12 更新：页面式 API 配置

V12 将 API 配置中心改成类似独立设置页的高端样式，并支持两种方式：

1. 临时页面配置：适合快速测试，不用马上进 Streamlit 后台。
2. Streamlit Secrets 长期配置：适合正式上线，密钥不会写进 GitHub。

临时页面配置会保存到当前 Streamlit 会话，刷新或重启后可能丢失。正式使用仍建议复制 TOML 到 Streamlit Secrets。



## Seed 2.1 Pro Ready Preset

This package has the user's Doubao Seed 2.1 Pro endpoint pre-filled:

```toml
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_SEED21_PRO_MODEL_ID = "ep-20260625032114-7d4xz"
```

API Key is intentionally not hardcoded into the project. Configure it in Streamlit Secrets:

```toml
ARK_API_KEY = "你的火山方舟 API Key"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_SEED21_PRO_MODEL_ID = "ep-20260625032114-7d4xz"
APP_PASSWORD = "123456"
```



## V13 更新：API 调试与防卡死

- OpenAI-compatible 客户端加入 60 秒超时，避免一直转圈不返回。
- 图片上传后自动压缩到约 2MB 再传给图片理解模型，降低 10MB 大图超时风险。
- API 配置中心新增“测试文本连接”按钮。
- 图片分析报错会明确提示：是否 Vision Endpoint 不支持 image_url / 图片理解。



## V14 更新：图片理解排查安全版

- API 配置中心不再回显真实 API Key，避免截图泄露。
- 新增 `ARK_IMAGE_INPUT_MODE`：`data_url` / `raw_base64`。
- 如果图片理解一直卡住，先用 `data_url`；不行再切换 `raw_base64`。
- 日志会打印 `[vision-call] model=... bytes=... mode=...`，方便确认请求确实发出。
- 注意：如果 API Key 已经在截图里暴露，建议立刻去火山方舟重新生成 Key，旧 Key 作废。
