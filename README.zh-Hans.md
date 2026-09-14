# Zongsoft 官网与博客

[English](README.md) | 简体中文

官网：[zongsoft.com](https://zongsoft.com/) · 博客：[zongsoft.com/blog](https://zongsoft.com/blog/)

博客使用 Hugo 和仓库内的 `themes/archer` 主题，GitHub Actions 自动构建并发布整个网站。主题保留本站的背景图、Oswald-Regular 标题字体和头像，以普通 CSS、原生 JavaScript 实现，不需要 Go、Node.js、npm、Sass 或外部主题模块。

## 写文章

文章原文直接保存在 `docs/`，配图保存在 `docs/images/`。新建 Markdown 文件，例如 `hello-hugo.md`：

```yaml
---
title: 新文章标题
type: post
date: 2026-09-14T10:00:00+08:00
url: /blog/zh-cn/misc/hello-hugo/
categories: [misc]
tags: [Hugo, 博客]
draft: true
---

这里是正文。

![图片说明](/blog/images/example.png)
```

写完后删除 `draft: true` 或改为 `false`，提交并推送至 `main`。文章 URL 通过元数据中的 `url` 明确设置，修改标题不会自动改变地址；需要更换地址时，可通过 `aliases` 保留旧链接的跳转。`date` 是首次发表时间，需要标注更新时手动增加 `lastmod`，不使用文件修改时间。

## 本地预览

Windows 双击 `preview.cmd`，或在终端执行：

```powershell
.\preview.cmd
```

打开 <http://127.0.0.1:1313/blog/>。官网同时位于 <http://127.0.0.1:1313/>。保存文章或模板会自动刷新，预览包含草稿；关闭终端或按 Ctrl+C 停止。

首次运行从 Hugo 官方 GitHub Releases 下载 `.hugo-version` 指定的 Windows 程序，并校验官方 SHA-256。程序缓存在 `.tools/`，之后可离线预览。需要首次下载时能够访问 GitHub。不修改 PATH，不安装 Go 或 Node；每台电脑复用同一版本配置。

生成正式发布文件：

```powershell
.\build.cmd
```

输出在 `public/`，不要提交该目录。其他系统可自行安装 `.hugo-version` 中的 Hugo 标准版，在仓库根目录执行 `hugo server -D` 或 `hugo --minify`。

## 自动发布

工作流：`.github/workflows/pages.yml`。

1. 在仓库 Settings → Pages → Build and deployment 将 Source 设置为 **GitHub Actions**。
2. 保留 Pages 的自定义域名 `zongsoft.com` 和现有 DNS 设置。自定义 Actions 部署以 Pages 设置为准，根目录 `CNAME` 作为原有域名记录保留。
3. 推送到 `main` 后，Actions 下载固定版本 Hugo、校验文件、构建并部署 `public/`。拉取请求只构建，不部署。

本地预览和 Actions 使用同一个 `.hugo-version`。升级时修改该文件并先验证构建和布局。工作流中的 Actions 也使用明确版本。

## 目录与定制

| 路径 | 用途 |
| --- | --- |
| `index.html`、`en/`、`assets/`、`styles/` | 现有官网静态文件；Hugo 将它们合并到发布产物 |
| `docs/`、`docs/images/` | 文章原文与配图 |
| `content/blog/` | 博客首页及归档页元数据 |
| `hugo.toml` | 全站配置、文章挂载与旧 URL 规则 |
| `themes/archer/layouts/` | HTML 模板：公共外壳、文章、列表、标签与目录 |
| `themes/archer/assets/css/blog.css` | 可直接修改的普通 CSS，包含字体、颜色和响应式布局 |
| `themes/archer/assets/js/blog.js` | 明暗切换、导航、代码复制、分享链接、图片放大与目录跟随 |
| `themes/archer/static/blog/` | 原有标题字体、代码字体与背景图 |

Hugo 使用本地目录挂载读取原文，不使用 Go 模块下载。标题字体为原文件 `Oswald-Regular.ttf`，中文字符使用浏览器原有回退；首页文章列表沿用原系统无衬线字体。头像直接使用 `assets/avatar.jpg`。

归档、标签、分类和 RSS 由 Hugo 生成。目录、明暗主题、图片放大与复制功能使用原生 JavaScript，阅读统计接入 GoatCounter，尚未启用评论服务。仓库只保存源码和素材，不再保存旧生成器、第三方主题依赖及生成页面；需要恢复旧站时可查阅 Git 历史。

文本文件使用 CRLF；代码缩进使用 Tab。YAML 的层级缩进按格式要求使用空格；`.sh` 使用 LF。第三方字体和图片保留原始二进制文件，主题保留 Archer 的 MIT 版权声明。

## 阅读、搜索与反馈

- 博文标题下显示 GoatCounter 浏览次数，站点为 `https://zongsoft.goatcounter.com/`。公开接口实测会返回超过 4 小时的旧缓存，因此使用从 1970-01-01 到 UTC 次日的累计日期范围，每天自动更换查询范围，并禁用浏览器缓存；统计覆盖全部现有文章的访问历史，不是当天访问量。服务端仍可能延迟更新，同日内不保证实时。HTTP 200 返回零时显示“0 次浏览”；HTTP 404 的零计数响应显示“统计待更新”；接口失败、响应无效或脚本被拦截时隐藏数字。计数只在正式环境的 `https://zongsoft.com` 文章页启用，本地预览、搜索页和官网不计数。
- 每篇文章的 `stats_path` 是稳定统计标识，首次设为文章 URL。以后调整文件名或 URL 时保留它，并通过 `aliases` 维护原地址跳转，避免浏览次数分散。
- [搜索页面](https://zongsoft.com/blog/search/)支持标题、标签、正文及代码中的关键词，多个空格分隔的词需同时匹配，标题匹配优先。索引由 Hugo 随页面构建，不需额外安装程序；搜索需要 JavaScript。目前采用关键词包含匹配，不提供错字纠正和语义搜索。
- 系列文章填写 `series`（系列名）与 `series_order`（正整数），文章开头自动显示该系列目录和当前篇目。目前已配置“实体类的动态生成”和“代码失控与状态机”。
- 正文标题旁的 `#` 按钮复制章节链接。文末“报告本文问题”打开预填标题和原文地址的 GitHub Issue 表单，由读者确认后提交；“在 GitHub 编辑”链接到对应 Markdown 文件。提交反馈需要 GitHub 账号。

GoatCounter 使用其官方统计脚本收集访问统计；数据由该服务处理。可在 `hugo.toml` 将 `goatcounter` 设为空字符串关闭统计，不影响正文或其他功能。不要把后台密码或 API Token 写进网站代码。

## 发布前检查

Actions 构建成功后执行 `python3 scripts/check-site.py`，检查文章必填元数据、日期格式、重复 URL、重复统计标识、系列序号，以及生成页面中的站内链接、章节锚点、图片和 CSS 资源。检查失败会阻止上传与部署；草稿与未来文章的元数据也会检查，只有已生成页面参与链接检查。外部网站链接不作为发布阻断条件。

检查器使用 Python 3.9+ 标准库，Actions 运行器已具备，不添加 npm 依赖，也不改变本地 Hugo 构建所需环境。如需手动验证，可在已有 Python 的环境运行：

```powershell
python scripts/check-site.py --hugo .tools/hugo/0.166.0/amd64/hugo.exe
python -m unittest discover -s scripts -p 'test_*.py'
```

文章必填字段以及 `stats_path`、`series`、`series_order` 使用顶层单行 YAML 值，便于检查；正文仍可使用完整 Markdown。浏览器截图与临时测试报告不提交到仓库。
