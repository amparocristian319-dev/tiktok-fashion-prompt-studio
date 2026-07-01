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



## V15 更新：页面级图片理解调试

- API 配置中心新增“测试图片理解”按钮，不再只依赖 Logs。
- 点击“分析款式资产”后，页面直接显示 5 步流程：
  1. 读取图片
  2. 图片压缩
  3. 准备调用 Vision Model
  4. 请求已发送
  5. 模型返回成功 / 失败原因
- 用于判断到底是按钮没触发、图片太大、图片传输格式不兼容，还是 Vision Endpoint 不支持图片理解。



## V16 更新：快速视觉资产卡

原因：
- 图片理解测试已成功，说明 API 和 Vision Endpoint 能返回。
- 但完整“款式资产卡”提示词过长，要求图片模型一次性输出大量创意策略，后台会消耗 token，却容易长时间等待。
- V16 将图片模型阶段改成“短视觉识别”，只输出可见款式事实和少量适配判断。
- 创意方向、剧情池、场景规划等复杂内容改由后续文本模型基于资产卡扩展。

结果：
- 图片分析更快返回。
- 不再让 Vision 模型一次性生成 30 个方向 / 30 个 Hook / 30 个冲突。
- 仍然只生成文本，不生成图片或视频。



## V17 更新：正式生产界面

- 移除前端“文本测试 / 图片测试 / 调试 Step”这些测试态内容。
- 图片识别流程改成正式产品语气：生成款式资产卡、识别版型细节、提取可展示卖点。
- API 配置中心改为更克制的“模型接入中心”，不在界面反复提第三方服务商或技术调用词。
- 保留 V16 的核心修复：图片模型只做短视觉资产卡；复杂创意策略交给后续文本阶段。
- 仍然只生成文本提示词，不生成图片或视频。



## V18 更新：直连接口稳定版

- 改为直接请求 `/chat/completions`，不再依赖 OpenAI Python SDK 封装，便于定位“请求是否真正发出”。
- 图片识别阶段进一步缩短：只输出简洁 JSON 视觉识别结果。
- 再由文本模型把简洁识别结果整理成正式款式资产卡。
- 图片压缩上限调到 0.8MB，降低图片请求卡住概率。
- 接口超时缩短为 35 秒，避免长时间转圈。
- 仍然只生成文本提示词，不生成图片或视频。
