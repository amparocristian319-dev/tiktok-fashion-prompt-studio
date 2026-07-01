# TikTok Fashion Prompt Studio 在线部署说明（密码版）

推荐部署方式：GitHub + Streamlit Community Cloud。

## 1. 上传到 GitHub

1. 注册/登录 GitHub。
2. 新建仓库，例如：`tiktok-fashion-prompt-studio`。
3. 上传项目文件：`app.py`、`config.py`、`prompts.py`、`volc_api.py`、`requirements.txt`、`README.md`、`.gitignore`。
4. 不要上传 `.env`。`.env` 里有 API Key 和密码。

## 2. 部署到 Streamlit Community Cloud

1. 打开 Streamlit Community Cloud。
2. 选择 GitHub 登录。
3. New app。
4. 选择刚才的 GitHub 仓库。
5. Main file path 填：`app.py`。
6. 打开 Advanced settings。
7. Secrets 填入：

```toml
ARK_API_KEY = "你的火山方舟API_KEY"
ARK_MODEL_ID = "你的模型ID或Endpoint ID"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
APP_PASSWORD = "你设置的访问密码"
```

8. 点击 Deploy。

## 3. 使用方式

部署成功后会得到一个 `streamlit.app` 网页链接。

别人打开链接后，先输入 `APP_PASSWORD`，密码正确才能进入工具。

## 4. 安全提醒

- 不要把 `.env` 上传到 GitHub。
- 不要把 API Key 发给别人。
- GitHub 仓库建议先设为 Private。
- 如果你怀疑 API Key 泄露，马上去火山控制台重置。


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
