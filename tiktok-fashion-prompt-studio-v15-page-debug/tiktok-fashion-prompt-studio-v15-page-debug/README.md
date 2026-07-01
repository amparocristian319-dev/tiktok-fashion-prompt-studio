# TikTok Fashion Prompt Studio V5

V5 重点更新：

- 大幅优化 UI，减少密集红色标签，整体更像正式工具。
- 上传图片后不展示大图，避免图片撑爆页面。
- 款式资产卡不描述颜色；颜色在“颜色变体”里单独填写。
- 默认不指定人物人设，使用参考图人物作为主体。
- 服装卖点不再手动全选，由款式资产卡自动提取。
- 场景默认由 AI 随机生成欧美真实生活场景，不局限于固定列表。
- 人物关系和剧情冲突使用大型随机池，生成时自动过滤冲突。
- 输出格式改为 Seedance 2.0 固定长提示词格式：固定技术段落 + 场景首帧描述 + 叙事内容对话+展示。
- 默认口播自动判断，字幕默认不要字幕。

## 修改位置

常规修改不需要动 Python：

- 改选项：`data/options.json`
- 改默认值：`data/defaults.json`
- 改资产分析提示词：`prompt_templates/clothing_profile.md`
- 改最终输出格式：`prompt_templates/video_prompt_generator.md`

## Streamlit Secrets 配置

```toml
ARK_API_KEY = "你的火山方舟API_KEY"
ARK_MODEL_ID = "你的模型ID或Endpoint ID"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
APP_PASSWORD = "你设置的网页登录密码"
```

如果你之前 GitHub 上传时外面套了一层文件夹，Streamlit 的 Main file path 要填：

```text
tiktok-fashion-prompt-studio-v5/app.py
```

如果你把文件直接放在仓库根目录，则填：

```text
app.py
```


## V6 更新
- 强化批量生成时的场景去重规则，避免几十条都落在同一个场景。
- 强化 15 秒口播控时规则，限制英文总词数，减少冗长台词。


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
