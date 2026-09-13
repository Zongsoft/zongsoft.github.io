---
type: post
url: /blog/zh-cn/misc/github-site/
title: 使用 Hugo 与 GitHub Actions 搭建博客站点
date: 2018-07-10 18:00:00
lastmod: 2026-09-14T00:00:00+08:00
description: 用 Markdown 写作，用 Hugo 预览，让 GitHub Actions 自动构建和发布；家里和公司的电脑使用同一份配置，不再手工维护两套建站环境。
categories: misc
tags:
- github.io
- GitHub Pages
- GitHub Actions
- Hugo
- 建站
- 博客
---

## 写作与发布分开

这个博客使用 [Hugo](https://gohugo.io/) 生成静态页面，通过 [GitHub Actions](https://github.com/features/actions) 自动构建，最后发布到 [GitHub Pages](https://pages.github.com/)。官网和博客共用一个仓库、一个自定义域名。

日常写作只需要编辑 Markdown 和图片，然后提交到 GitHub。构建工具的版本、主题和配置都在仓库中，家里和公司的电脑使用同一套文件。只改文字时，可以直接使用 GitHub 网页编辑器；需要查看完整排版时，再启动本地预览。

本文首次发表于 2018 年，现已按本站使用的 Hugo 工作流重写。首次发表日期和原文章地址保持不变，更新时间单独记录。

## 获取项目

首次使用时克隆仓库：

```powershell
git clone https://github.com/Zongsoft/zongsoft.github.io.git
cd zongsoft.github.io
```

换电脑继续写作前，先同步远端已经提交的修改：

```powershell
git pull --ff-only
```

仓库中最常使用的文件如下：

| 路径 | 用途 |
| --- | --- |
| `docs/_posts/` | Markdown 文章原文 |
| `docs/images/` | 文章配图 |
| `hugo.toml` | 网站配置 |
| `.hugo-version` | 固定的 Hugo 版本 |
| `themes/zongsoft/` | 本站主题源码和资源 |
| `preview.cmd` | Windows 本地预览入口 |
| `build.cmd` | Windows 正式构建入口 |

官网首页继续使用根目录的 `index.html`，英文页面在 `en/`，共享静态资源在 `assets/`。Hugo 将官网和博客合并为同一个发布产物。

## 新建文章与草稿

在 `docs/_posts/` 新建 Markdown 文件，例如 `hello-hugo.md`。文件开头填写文章元数据：

```yaml
---
title: 我的第一篇文章
type: post
date: 2026-09-14T10:00:00+08:00
url: /blog/zh-cn/misc/hello-hugo/
categories: [misc]
tags: [Hugo, 博客]
draft: true
---

## 正文

从这里开始写文章。
```

`type: post` 将文件识别为博客文章；`date` 决定首次发表日期和列表排序；`url` 固定文章地址，之后修改标题或源文件名都不需要改动它。请为每篇文章设置不同的地址。

写作期间使用 `draft: true`。本地预览会显示草稿，正式构建会排除草稿。准备发布时删除这一行，或改为 `draft: false`。未来日期的文章默认也不会出现在正式站点中；若需要提前预览，可以运行 `preview.cmd --buildFuture`。

修改已发表的文章时保留原来的 `date`，需要展示更新时间时增加 `lastmod`：

```yaml
lastmod: 2026-09-15T18:00:00+08:00
```

本站不使用文件修改时间作为文章更新时间，因此换电脑、重新克隆仓库不会改变文章的日期。

## 添加图片与代码

将图片保存到 `docs/images/`，在正文中使用对应的公开地址：

```markdown
![图片说明](/blog/images/your-image.png)
```

路径以 `/blog/images/` 开头，不要写成本机的磁盘路径。图片文件和文章需要一起提交，文件名大小写必须一致。

使用 Markdown 围栏代码块，并在开头声明语言，例如 `csharp`、`xml`、`powershell`。主题会显示代码高亮和复制按钮。文章标题自动生成目录，正文图片支持点击放大；这些功能不需要额外安装插件。

## 本地预览

Windows 下双击仓库根目录的 `preview.cmd`，或在终端执行：

```powershell
.\preview.cmd
```

然后打开[本地博客](http://127.0.0.1:1313/blog/)，也可以访问[本地官网](http://127.0.0.1:1313/)。修改文章、模板或样式后，浏览器会自动刷新。按 Ctrl+C 可以停止服务。

首次运行时，脚本从 Hugo 官方 GitHub Releases 下载 `.hugo-version` 指定的程序，核对官方 SHA-256 校验值，并缓存在 `.tools/`。这一步需要访问 GitHub，后续预览可离线运行。不需要安装 Go、Node.js、npm 或 Sass，也不需要修改系统 PATH。

预览输出位于 `.tools/preview/`，正式构建输出位于 `public/`，两者互不覆盖。端口被占用时，可以指定其他端口：

```powershell
.\preview.cmd --port 1316
```

Linux 或 macOS 用户安装 `.hugo-version` 指定的 Hugo 标准版后，可直接运行：

```sh
hugo server -D --destination .tools/preview
```

## 修改主题

本站主题保留了双行站名“Zongsoft / Zongsoft Studio”、大图背景、头像，以及 Oswald-Regular 标题字体。

- 修改站名、副标题和背景图路径：编辑 `hugo.toml`。
- 修改配色、字号、间距和手机布局：编辑 `themes/zongsoft/assets/css/blog.css`。
- 修改文章列表、正文或公共页眉页脚：编辑 `themes/zongsoft/layouts/` 中对应的 HTML 模板。
- 修改目录、明暗切换、复制或图片放大行为：编辑 `themes/zongsoft/assets/js/blog.js`。
- 更换头像：替换 `assets/avatar.jpg`。

字体和背景图随主题保存，不依赖外部字体服务。CSS 是可以直接编辑的普通样式文件，无须先编译 Sass 或运行前端打包工具。官网独立使用的样式文件与博客主题分开维护。

## 构建与自动发布

发布前可以本地检查正式构建：

```powershell
.\build.cmd
```

生成结果在 `public/`，该目录不提交到 Git。确认文章和配图无误后，提交并推送源码：

```powershell
git add docs/_posts/hello-hugo.md docs/images/your-image.png
git commit -m "发布新文章"
git push origin main
```

上述图片文件名按实际文件修改；没有新增图片时，只提交文章即可。通过 GitHub 网页修改文章并提交到 `main`，也会触发同一发布流程。

工作流位于 `.github/workflows/pages.yml`，依次执行：读取固定的 Hugo 版本、下载并校验程序、构建完整网站、上传 Pages 产物、部署网站。拉取请求只做构建验证，不发布；推送到 `main` 才会部署。

首次配置仓库时，在 **Settings → Pages → Build and deployment** 中将 **Source** 设置为 **GitHub Actions**，并保留自定义域名 `zongsoft.com` 和现有 DNS 配置。以后每次推送无需重新设置。

在仓库的 **Actions** 页面查看当前提交的运行结果。部署成功后访问[博客](https://zongsoft.com/blog/)。构建失败时先查看失败步骤的日志，修复源码后重新提交，不要手工修改生成页面。

## 换电脑与日常维护

日常工作就是同步仓库、写文章、预览、提交。两台电脑共用仓库中的工具版本和主题配置，不需要手工复制配置文件。

升级 Hugo 时修改 `.hugo-version`，先本地构建并检查文章排版，再提交。不要同时随意升级构建工具和大幅调整主题，这样更容易判断变化来自哪里。原文、图片和主题都有 Git 历史，可以用普通的回退提交恢复，不需要重写仓库历史。
