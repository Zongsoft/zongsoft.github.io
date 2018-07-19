---
title: 搭建 github.io 博客站点
date: 2018-07-10 18:00:00
comments: true
categories: misc
tags:
- github.io
- github pages
- Hexo
- 建站
- 博客
---

## 前言
很多人都有搭建博客或知识库站点的想法，可自己买云服务器太不划算，部署管理也是个问题；基于免费又热门的 [GitHub Pages](https://pages.github.com/) 来搭建博客站点倒是省钱省力省事的好办法，于是上网一搜，满屏都是关于使用 Jekyll 来搭建站点的文章，这个 Jekyll 是基于 Ruby 开发的，上手得先装一大坨东西、各种啰嗦各种坑，看的一点欲望都没有了。

### 神器出现
平地一声雷，炸出了 [Hexo (https://hexo.io/zh-cn)](https://hexo.io/zh-cn/) 这个神器。它只需要 NodeJS 即可，完全不依赖其他乱七八糟的玩意，安装部署超级简单，功能完善、漂亮主题也很多，妥妥的就是它了。

* __Hexo __官网：[https://hexo.io/zh-cn/](https://hexo.io/zh-cn/)
> 安装简单，并且官网上提供了[很多主题](https://hexo.io/themes/)可供选择。

* 我喜欢的一款主题 (__Archer__)
> [http://firework.studio/archer-demo/](http://firework.studio/archer-demo/)
> [https://github.com/fi3ework/hexo-theme-archer](https://github.com/fi3ework/hexo-theme-archer)


## 建站步骤
有关一般建站步骤，请参考本文后面的“参考文章”部分，在进行后续操作之前，请按照 Hexo 官网的安装指引，确保 NodeJS 和 Hexo 已经成功安装。

友情提示：在此之前请务必详读 Hexo 官网中的[文档](https://hexo.io/zh-cn/docs/index.html)。

我们的站点源码：[https://github.com/Zongsoft/zongsoft.github.io](https://github.com/Zongsoft/zongsoft.github.io)，没必要把 Hexo 运行环境和使用的主题文件都保存在站点仓库中，所以需要将这些不需要的目录和文件加入到 __.gitignore__ 文件中；站点的 Hexo 基本配置(*hexo.config.yml*)和相应主题配置文件(*hexo.config-theme.archer*)需要保留，以便下次或别人构建时将其覆盖还原为默认配置。

### 站点构建
在首次 clone 获取我们[站点源码](https://github.com/Zongsoft/zongsoft.github.io)后，按顺序执行下列命令，__注意：__推荐在 Git Bash 中进行操作。

1. 初始化 Hexo 站点目录：
```bash
hexo init site && cd site
```

2. 安装相关插件：
```bash
npm i hexo-generator-json-content --save && npm i hexo-wordcount --save
```

3. 获取 Archer 主题：
```bash
git clone https://github.com/fi3ework/hexo-theme-archer.git themes/archer
```

4. 覆盖 Hexo 默认配置文件：
```bash
cp  ../hexo.config.yml _config.yml
```

5. 覆盖 Archer 主题默认配置文件：
```bash
cp ../hexo.config-theme.archer.yml themes/archer/_config.yml
```

6. 加入定制的页面布局：
```bash
cp ../post-footer.ejs themes/archer/layout/_partial/post-footer.ejs
```

7. 安装 Hexo 站点：
```bash
npm install
```


### 文章写作
上面的构建过程稍微需要花点时间，但只要构建一次之后就不用管它了。

* 通过 `hexo new [layout] <title>` 命令来创建一个文章，也可以手动把写好的文章拷贝到源目录(/docs/\_posts/)中。
* 执行 `hexo generate` 命令生成静态页面(/blog)，生成之后，可以使用 `hexo server` 命令来查看实际效果。
* 最后，执行相关 Git 命令将这些改动提交到远程仓库中。

__注意：__创建了一篇新文章后，务必要设置好文章的元信息（即标题、创建时间、所属分类、Tags等），具体定义请参考 Hexo 官网的这篇文章：[https://hexo.io/zh-cn/docs/front-matter.html](https://hexo.io/zh-cn/docs/front-matter.html)

__提示：__如果生成有问题，可以执行 `hexo clean` 命令来清空输出目录，之后再把项目所需的资源文件手动拷贝到输出目录的相应子目录中。

## 其他备注
1. 修改 post.ejs (*site/themes/archer/layout/*) 模板，增加对 post-footer.ejs 局部模板的引用：
```html
<main class="main post-page">
    <article class="article-entry">
        <%- page.content %>
    </article>

<%- partial('_partial/post-footer') %>
```

2. 修改 post.ejs 模板中的分页指示的标签：
> ~~<span data-type="color" style="color:#F5222D">&lt;div class=&quot;nextSlogan&quot;&gt;Next Post&lt;/div&gt;</span>~~
> <span data-type="color" style="color:#389E0D">&lt;a class=&quot;nextSlogan&quot; href=&quot;&lt;%- url_for(page.prev.path) %&gt;&quot;&gt;Next Post&lt;/a&gt;</span>
> <span style="color:gray">... ...</span>
> ~~<span data-type="color" style="color:#F5222D">&lt;div class=&quot;prevSlogan&quot;&gt;Previous Post&lt;/div&gt;</span>~~
> <span data-type="color" style="color:#389E0D">&lt;a class=&quot;prevSlogan&quot; href=&quot;&lt;%- url_for(page.next.path) %&gt;&quot;&gt;Previous Post&lt;/a&gt;</span>

3. 调整了 Archer 主题的 \_post\_page.scss (*site/themes/archer/src/scss/\_partial/*) 中的部分样式：
```css
// ========== paginator ========== //
.post-paginator {
    li {
        max-width:18rem;
    }

    .nextTitle,
    .prevTitle{
        font-size:1.2rem; //remove this line
    }
}

// ========== content ========== //
.abstract-content,
.article-entry {
    > p {
        text-indent:2em;
    }
}
```



## 参考文章
* 《使用 Hexo & GitPage 搭建博客》
[https://yuque.com/skyrin/coding/tm8yf5](https://yuque.com/skyrin/coding/tm8yf5)

* 《从多说到跟帖：推荐网易云跟帖》
[https://blog.vadxq.com/dstogentie/](https://blog.vadxq.com/dstogentie/)

* 《集成gitment或者gitalk评论系统》
[http://www.huyanbing.me/2017/10/20/46383.html](http://www.huyanbing.me/2017/10/20/46383.html)
