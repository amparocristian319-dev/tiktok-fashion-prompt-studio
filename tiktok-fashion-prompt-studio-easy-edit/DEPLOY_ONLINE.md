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
