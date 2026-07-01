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



## V19 更新：请求等待时间可配置

- V18 的 35 秒是调试用，确实偏短。
- V19 默认等待时间改为 120 秒，更适合图片识别。
- 新增 `ARK_REQUEST_TIMEOUT`，可在页面配置或 Streamlit Secrets 里设置。
- 支持 60 / 90 / 120 / 180 / 240 / 300 秒。
- 建议正式使用：120 秒；大图或网络慢：180 秒；排查接口错误：60 秒。



## V20 更新：稳定链路架构

根因重构：
- 不再依赖 SDK 封装，改为直接请求 `/chat/completions`。
- 图片阶段只做短 JSON 识别，文本阶段再整理正式款式资产卡。
- 图片默认使用 `raw_base64`，并自动在格式错误时尝试 `data_url`。
- 请求等待时间默认 180 秒。
- UI 保持正式产品语气，调试信息隐藏在“高级诊断”里。
- 仍然只生成文本提示词，不生成图片或视频。



## V21 更新：资产轻分析 + 生成深度规划

- 资产识别阶段不做深度思考，只做可见款式结构提取，默认等待 120 秒。
- 创意策略、场景规划、Seedance 提示词生成阶段允许深度规划，默认等待更久。
- 新增独立超时参数：
  - `ARK_ASSET_TIMEOUT = "120"`
  - `ARK_GENERATION_TIMEOUT = "240"`
- 前端不展示推理细节，只展示进度状态，例如“思考中：正在规划场景”“思考中：正在过滤不兼容组合”“思考中：正在生成提示词”。
- 仍然只输出文本提示词，不生成图片或视频。



## V22 更新：Thinking 参数和链路修复

- 资产识别阶段：`thinking.type=disabled`，不做深度思考，等待 120 秒。
- 资产识别图片压缩上限恢复到 2MB，保证服装纹理和结构识别质量。
- 提示词生成阶段：`thinking.type=enabled`，允许深度规划，等待 240–300 秒。
- 文本与图片识别使用不同超时策略。
- 视觉模型 ID 不再自动回退到文本模型 ID，减少误用。
- 请求链路直接 POST 到 `/chat/completions`，并在“高级诊断”中记录 request_started / response_received / timeout / http_error。
- 默认图片编码格式为官方 OpenAI 兼容的 data URL。
- 仍然只输出文本提示词，不生成图片或视频。



## V23 更新：NameError 修复

- 修复模型接入中心里 `asset_timeout` / `generation_timeout` 未定义导致的 NameError。
- 页面配置现在会真正显示并保存：
  - 默认请求等待时间
  - 资产识别等待时间
  - 提示词生成等待时间
- 保持 V22 架构：资产识别关闭 thinking，提示词生成开启 thinking。



## V24 更新：状态卡变量修复

- 修复模型接入中心状态卡中的 `asset_timeout_status` / `generation_timeout_status` 未定义问题。
- 保留 V23/V22 架构：资产识别关闭 thinking，提示词生成开启 thinking。
- 页面配置、状态卡、Secrets 示例现在都包含三类等待时间。



## V25 更新：资产卡前端显示修复

原因：
- 款式资产卡实际已经生成，并保存在 `st.session_state.clothing_profile`。
- 但前端文本框使用了 `key="clothing_profile_editor"`。
- Streamlit 会优先使用 widget key 对应的旧值，导致成功提示出现，但文本框仍然显示空白。

修复：
- 生成资产卡后，同时写入：
  - `st.session_state.clothing_profile`
  - `st.session_state.clothing_profile_editor`
- 文本框初始化时也会同步资产卡内容。
