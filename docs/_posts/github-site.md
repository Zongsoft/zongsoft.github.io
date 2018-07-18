---
title: 搭建 github.io 博客站点
date: 2018-07-18 18:00:00
comments: true
categories: misc
tags:
- github.io
- github pages
- Hexo
- 建站
- 博客
- 知识库
---


## 前言
很多人都有搭建博客或知识库站点的想法，可自己买云服务器太不划算，部署管理也是个问题；基于免费又热门的 [GitHub Pages](https://pages.github.com/) 来搭建博客站点倒是省钱省力省事的好办法，于是上网一搜，满屏都是关于使用 Jekyll 来搭建站点的文章，这个 Jekyll 是基于 Ruby 开发的，上手得先装一大堆东西、各种啰嗦各种坑，看的一点欲望都没有了。

### 神器出现
平地一声雷，炸出了 [Hexo (https://hexo.io/zh-cn)](https://hexo.io/zh-cn/) 这个神器。它只需要 NodeJS 即可，完全不依赖其他乱七八糟的玩意，安装部署超级简单，功能完善、漂亮主题也很多，妥妥的就是它了。

* __Hexo __官网：[https://hexo.io/zh-cn/](https://hexo.io/zh-cn/)
> 安装简单，并且官网上提供了[很多主题](https://hexo.io/themes/)可供选择。

* 我喜欢的一款主题 (__Archer__)
> [http://firework.studio/archer-demo/](http://firework.studio/archer-demo/)
> [https://github.com/fi3ework/hexo-theme-archer](https://github.com/fi3ework/hexo-theme-archer)


## 建站步骤
1. 在 Github 上创建一个站点库，譬如：zongsoft.github.io
2. 按照 Hexo 官网的提示，安装 Hexo，即命令：`npm install hexo-cli -g` 
3. 进入本地站点目录，初始化生成站点，即命令：`hexo init blog && cd blog && npm install` 
4. 在 GitHub 中 fork 指定的 Hexo 主题库，方便我们调整自己主题设置
5. 将 fork 的主题库克隆到站点库中，然后安装主题库的指引，执行安装命令即可

## 我的站点
友情提示：在此之前请务必详读 Hexo 官网中的[文档](https://hexo.io/zh-cn/docs/index.html)。

我们的站点（[https://github.com/Zongsoft/zongsoft.github.io](https://github.com/Zongsoft/zongsoft.github.io)）没必要把 Hexo 运行环境和使用的主题文件都放到 GitHub 项目仓库中，所以需要将这些不需要提交目录和文件加入到 .gitignore 文件中。每个站点的一些基本配置（站点标题、描述、目录、生成规则等）和主题配置需要保留，并避免与默认的配置文件名冲突。

### 站点构建
在首次 clone 获取我们站点源码后，按顺序执行下列命令，__注意：__推荐在 Git Bash 中进行操作。

1. 初始化 Hexo 站点目录，命令：`hexo init site && cd site` 
2. 安装相关插件，命令：`npm i hexo-generator-json-content --save && npm i hexo-wordcount --save` 
3. 获取 Archer 主题，命令：`git clone https://github.com/fi3ework/hexo-theme-archer.git themes/archer` 
4. 覆盖 Hexo 默认配置文件，命令：`cp  ../hexo.config.yml _config.yml` 
5. 覆盖 Archer 主题默认配置文件，命令：`cp ../hexo.config-theme.archer.yml themes/archer/_config.yml`
6. 安装 Hexo 站点，命令：`npm install` 

### 文章写作
上面的构建过程稍微需要花点时间，但只要构建一次之后就不用管它了。

* 通过 `hexo new [layout] <title>` 命令来创建一个文章，也可以手动把写好的文章拷贝到源目录(/docs/\_posts/)中。
* 执行 `hexo generate` 命令生成静态页面(/blog)，生成之后，可以使用 `hexo server` 命令来查看实际效果。
* 最后，执行相关 Git 命令将这些改动提交到远程仓库中。

__注意：__创建了一篇新文章后，务必要设置好文章的元信息（即标题、创建时间、所属分类、Tags等），具体定义请参考 Hexo 官网的这篇文章：[https://hexo.io/zh-cn/docs/front-matter.html](https://hexo.io/zh-cn/docs/front-matter.html)


## 参考文章
《使用 Hexo & GitPage 搭建博客》
[https://yuque.com/skyrin/coding/tm8yf5](https://yuque.com/skyrin/coding/tm8yf5)

《从多说到跟帖：推荐网易云跟帖》
[https://blog.vadxq.com/dstogentie/](https://blog.vadxq.com/dstogentie/)

《集成gitment或者gitalk评论系统》
[http://www.huyanbing.me/2017/10/20/46383.html](http://www.huyanbing.me/2017/10/20/46383.html)
