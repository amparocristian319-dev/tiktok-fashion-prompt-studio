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



## V27 更新：七牛云 Kodo 图片 URL 上传

根因：
- base64 图片会形成很大的 JSON 请求体，在 Streamlit Cloud 到模型接口之间可能出现 `write operation timed out`。
- 这时请求体还没写完，模型接口后台自然看不到 token 消耗。

解决：
- 用户拖入图片后，系统自动压缩图片。
- 如果配置了七牛云 Kodo，系统自动上传到七牛，拿到公网图片 URL。
- 图片识别阶段只把 URL 发给模型，不再发送大 base64。
- 如果未配置七牛，系统会用 0.35MB 小图 Base64 兜底，但不推荐长期使用。

当前已预填：
- Bucket: `tiktok-fashion-vision-suryus`
- Domain: `thhne79gp.hd-bkt.clouddn.com`
- Scheme: `http`，因为七牛测试域名通常不支持 HTTPS。



## V28 更新：dotenv 依赖错误修复

- 移除 `from dotenv import load_dotenv`。
- 移除 `python-dotenv` 依赖。
- Streamlit Cloud 直接从 Secrets 读取配置，不需要 `.env`。
- 保留七牛云 Kodo 图片 URL 上传架构。



## V29 更新：永久 Secrets 配置模式

- 删除页面临时 API 配置输入区。
- 前端不再保存密钥，不再显示密钥输入框。
- 所有火山 API 和七牛云配置统一从 Streamlit Secrets 读取。
- 刷新页面、重启 App 后配置不会丢失。
- 页面只显示配置状态：API Key 是否已配置、七牛云是否已配置、Bucket、图片域名等。
- 保留七牛云 Kodo 图片 URL 上传方案，避免 base64 write timeout。



## V30 更新：生成阶段稳定性优化

原因：
- V29 的场景规划阶段开启了 thinking，并设置 `max_tokens=12000`，输出数量为 10 时容易长时间停在第一步。
- 页面看起来像卡死，其实是在等待一个同步 API 调用返回。

修复：
- 场景规划阶段改为轻量规划：`thinking_type="disabled"`，120 秒等待。
- 最终 Seedance 提示词生成阶段继续开启深度思考：`thinking_type="enabled"`，300 秒等待。
- 根据输出数量动态控制 max_tokens，避免无意义超长输出。
- 生成失败时显示“生成诊断”，方便判断是否 request_started / response_received / timeout。



## V31 更新：逐条生成 + 可见进度

- 不再一次性生成全部场景和全部提示词。
- 改为 Video 1/N、Video 2/N 逐条规划、逐条生成。
- 前端显示：
  - 当前第几条
  - 正在规划场景
  - 正在生成提示词
  - 已完成第几条
- 每完成一条就把结果写入预览区。
- 这样即使模型慢，也能看到真实进度，不再长期停在“正在规划”。



## V32 更新：启动稳定版

- 输出格式下拉框只保留 3 个真实可执行选项：
  - Seedance 2.0 标准完整提示词
  - 只要固定格式 Prompt
  - 分镜脚本
- 默认输出格式固定为 `Seedance 2.0 标准完整提示词`。
- 逐条生成逻辑保留，启动后可以按 Video 1/N、Video 2/N 看到进度。
- 直播预览改为 code 预览，避免 Streamlit text_area widget key 导致刷新/重复生成异常。
- 每条生成的提示词会根据输出格式执行不同输出规则。
- 生成失败时会显示诊断信息，便于判断 Secrets、timeout、输出数量等问题。



## V33 更新：AI 自动推荐策略稳定版

原因：
- “AI 自动推荐创意策略”只是辅助推荐，不应该开启深度思考。
- 之前这一步 `thinking_type=enabled`、`max_tokens=5000`、`timeout=240`，会导致页面长时间执行，右侧控制台变灰。

修复：
- 自动推荐改成轻量模型调用：
  - `thinking_type="disabled"`
  - `max_tokens=2200`
  - `request_timeout=90`
- 推荐提示词缩短到 800-1200 字。
- 增加自动推荐诊断信息。
- 最终 Seedance 提示词生成阶段仍保留逐条生成和深度思考。



## V34 更新：格式、重复场景、超时修复

- 不是固定黑名单，而是“同批场景去重 / 开场任务去重”。
- 如果上一条出现洗衣房、洗衣机、烘干机，后续会主动换成不同生活空间。
- 如果上一条出现拆快递、开箱、刚收到包裹，后续会主动换成不同开场任务。
- TikTok Shop 转化不再默认等于拆快递，只作为购买渠道或弱 CTA。
- 输出格式改为：
  - 【总体分析】
  - 【分镜程式向逆推】
  - 【时间轴动作编排与台词（15秒）】
  - 【服装稳定性控制】
- 不再输出旧格式：Scene / First frame / Camera / Dialogue / Clothing display / Stability notes。
- 资产卡增加场景适配说明、非优先高频场景、同批重复规避说明。
- 生成超时加长：
  - 场景规划 180 秒
  - 单条提示词生成 420 秒



## V35 更新：视频目标默认留空

- `video_goals` 默认改为空数组。
- 前端标题改为“视频目标（默认不填）”。
- 留空代表 AI 根据款式资产卡自动判断，不会强行混合 TikTok Shop 转化、广告素材、Hook、评论区互动等目标。
- 这样可以减少“全是拆快递 / 全是广告素材 / 全是评论区导向”的偏移。



## V36 更新：结果卡片折叠查看

- 生成结果不再整页平铺。
- 默认只展开 Video 01。
- Video 02、Video 03 等默认折叠，避免页面太长。
- 增加“快速查看某一条”下拉框。
- 支持下载当前这一条 TXT。
- 保留下载全部 TXT / CSV。
- 生成过程中只预览“最新完成的一条”，不是把全部内容堆在页面上。



## V37 更新：修复 config 模块导入错误

- 移除 `from config import (...)`。
- `app.py` 改为自带 JSON 配置读取逻辑。
- 即使 Streamlit Cloud 因主文件路径/嵌套文件夹问题没有正确加载 `config.py`，也不会再出现 `ModuleNotFoundError: config`。
- 仍然保留 `data/options.json` 和 `data/defaults.json` 作为可编辑配置源。
- 如果 JSON 读取失败，app.py 会使用内置 fallback，保证应用能启动。
