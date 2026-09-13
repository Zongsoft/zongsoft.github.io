# Zongsoft 官网与博客

[English](README.md) | 简体中文

官网：[zongsoft.com](https://zongsoft.com/) · 博客：[zongsoft.com/blog](https://zongsoft.com/blog/)

博客使用 Hugo 和仓库内的 `themes/zongsoft` 主题，GitHub Actions 自动构建并发布整个网站。主题保留本站的背景图、Oswald-Regular 标题字体和头像，以普通 CSS、原生 JavaScript 实现，不需要 Go、Node.js、npm、Sass 或外部主题模块。

## 写文章

原文仍在 `docs/_posts/`，图片仍在 `docs/images/`。新建 Markdown 文件，例如 `hello-hugo.md`：

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

写完后删除 `draft: true` 或改为 `false`，提交并推送至 `main`。文章 URL 独立于标题，修改标题不影响旧链接；已迁移的 10 篇文章保留原地址。`date` 是首次发表时间，需要标注更新时手动增加 `lastmod`，不使用文件修改时间。

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
| `docs/_posts/`、`docs/images/` | 文章原文与配图 |
| `content/blog/` | 博客首页及归档页元数据 |
| `hugo.toml` | 全站配置、文章挂载与旧 URL 规则 |
| `themes/zongsoft/layouts/` | HTML 模板：公共外壳、文章、列表、标签与目录 |
| `themes/zongsoft/assets/css/blog.css` | 可直接修改的普通 CSS，包含字体、颜色和响应式布局 |
| `themes/zongsoft/assets/js/blog.js` | 明暗切换、导航、代码复制、分享链接、图片放大与目录跟随 |
| `themes/zongsoft/static/blog/` | 原有标题字体、代码字体与背景图 |

Hugo 使用本地目录挂载读取原文，不使用 Go 模块下载。标题字体为原文件 `Oswald-Regular.ttf`，中文字符使用浏览器原有回退；首页文章列表沿用原系统无衬线字体。头像直接使用 `assets/avatar.jpg`。

归档、标签、分类和 RSS 由 Hugo 生成。目录、明暗主题、图片放大与复制功能使用原生 JavaScript，没有启用第三方访问统计和评论服务。仓库只保存源码和素材，不再保存旧生成器、第三方主题依赖及生成页面；需要恢复旧站时可查阅 Git 历史。

完整教程请参阅[《使用 Hugo 与 GitHub Actions 搭建博客站点》](https://zongsoft.com/blog/zh-cn/misc/github-site/)。文章保留首次发表日期和原地址，通过 `lastmod` 标注更新。文章版权声明沿用本站定制页脚中的 BY-NC-SA 4.0 声明。

文本文件使用 CRLF；代码缩进使用 Tab。YAML 的层级缩进按格式要求使用空格；`.sh` 使用 LF。第三方字体和图片保留原始二进制文件，主题保留 Archer 的 MIT 版权声明。
