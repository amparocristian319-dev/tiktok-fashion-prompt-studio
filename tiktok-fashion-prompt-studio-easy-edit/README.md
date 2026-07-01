# TikTok Fashion Prompt Studio

这是“方便修改版”。常规修改不需要写代码：

- 改选项：`data/options.json`
- 改默认值：`data/defaults.json`
- 改提示词：`prompt_templates/`
- 详细说明：`EDIT_GUIDE.md`

# TikTok Fashion Prompt Studio

美区 TikTok 女装原生短视频提示词生成器。当前版本已加入简单访问密码，既可以本地运行，也可以部署成在线网页让别人打开网址后输入密码使用。

## 功能

1. 上传女装图片
2. 调用火山方舟豆包模型生成服装资产卡
3. 完整视频生成控制台
4. 批量生成 Seedance2.0 可用视频提示词
5. 输出 Hook、口播、字幕、动作脚本、正向提示词、Negative Prompt、Caption、评分
6. TXT / CSV 导出

## 文件说明

- `app.py`：Streamlit 网页主程序
- `config.py`：所有下拉框、多选项、脚本类型库
- `prompts.py`：服装分析提示词、自动推荐提示词、视频提示词生成提示词
- `volc_api.py`：火山方舟 OpenAI-compatible API 调用封装
- `.env.example`：环境变量示例，包含火山 API 配置和 APP_PASSWORD 访问密码
- `DEPLOY_ONLINE.md`：在线部署说明
- `requirements.txt`：依赖包

## 安装步骤

### 1. 安装 Python

建议安装 Python 3.10 或 3.11。

### 2. 进入项目文件夹

```bash
cd tiktok-fashion-prompt-studio
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 API Key

复制 `.env.example`，改名为 `.env`。

Windows PowerShell：

```powershell
copy .env.example .env
```

Mac / Linux：

```bash
cp .env.example .env
```

然后打开 `.env`，填写：

```env
ARK_API_KEY=你的火山方舟API_KEY
ARK_MODEL_ID=你的模型ID或Endpoint ID
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
APP_PASSWORD=你设置的网页访问密码
```

`ARK_MODEL_ID` 必须用你火山控制台里真实可用的模型 ID 或 endpoint ID。图片分析需要选择支持图片理解的模型/接入点。

### 5. 启动网页

```bash
streamlit run app.py
```

浏览器会自动打开。如果没有打开，复制终端里的本地地址访问，一般是：

```text
http://localhost:8501
```

## 使用顺序

1. 上传女装图片
2. 点击“分析衣服”
3. 检查服装资产卡，如果 AI 看错，直接在文本框里改
4. 选择生成设置
5. 点击“生成视频提示词”
6. 下载 TXT 或 CSV

## 常见问题

### 图片分析失败

通常是模型 ID 不支持图片理解。换成支持多模态/图片理解的模型或 endpoint。

### 提示词生成太慢

输出 100 条会消耗大量 token。第一次建议先生成 10 条或 30 条。

### CSV 没有完全分列

当前 CSV 是基础解析版：会提取视频方向、拍摄结构、Hook，并把完整文本放在 full_text。后续可以改成强制 JSON 输出，再精细拆分字段。

### 不想用火山

可以改 `volc_api.py`，替换成任何兼容 OpenAI SDK 的模型接口。


## 在线网页版

如果你不想让别人安装 Python，就把这个项目部署成在线网页。部署后别人只需要：

```text
打开网址
输入密码
上传服装图
生成提示词
```

具体看 `DEPLOY_ONLINE.md`。
