[English](README.md) | [简体中文](README.zh-CN.md)

# image-gen

通过 Playwright 控制 ChatGPT 网页界面来生成图片的 MCP 服务端。配合 Claude Code 使用 —— Claude 可以通过调用 `generate_image` 工具来生成图片。

## 工作原理

此服务端使用独立的 Chrome profile 启动 Chrome，导航至 ChatGPT 的图片生成页面，输入提示词，然后下载生成的图片。每次调用都会启动独立的 Chrome 进程，完成后退出。

独立的 Chrome profile（`./chrome-profile/`）与你日常使用的 Chrome 互不干扰 —— 只需认证一次，后续调用会复用登录状态。

## 环境要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- 已安装 Chrome（macOS: `/Applications/Google Chrome.app`）
- ChatGPT 账号（免费版可用，Plus 额度更高）

## 安装

> **重要**：先 `cd` 进入项目目录。安装后不要移动或重命名此目录 —— Claude Code 依赖步骤 3 中注册的绝对路径。

### 1. 安装依赖

```bash
uv sync
playwright install chromium
```

### 2. 登录 ChatGPT

```bash
uv run python init_auth.py
```

这会打开 Chrome。在浏览器中手动登录 ChatGPT，然后按 **ESC** 关闭浏览器。登录状态会保存在 `./chrome-profile/` 中。

### 3. 注册到 Claude Code

```bash
claude mcp add --transport stdio image-gen --scope user -- uv run --project "$(pwd)" "$(pwd)/server.py"
```

### 4. 测试（可选）

```bash
uv run python test_server.py
```

在不经过 MCP 层的情况下，直接生成一张测试图片到 `./test-output/`。

## 在 Claude Code 中使用

注册后，Claude 可以调用 `generate_image` 工具，传入提示词和输出目录。例如对 Claude 说：

> 生成一张小猫睡在云朵上的图片，保存到 ~/Desktop

## 局限性

- **单实例**：Chrome 独占锁定 profile，不支持并发调用。
- **ChatGPT 频率限制**：免费版图片生成额度有限，Plus 额度更高。
- **依赖 UI**：ChatGPT 的页面选择器可能会随时间变化。关键选择器记录在 `CLAUDE.md` 中。
- **仅限 macOS**：使用 `channel="chrome"`，假定 Chrome 安装在标准 macOS 路径下。
