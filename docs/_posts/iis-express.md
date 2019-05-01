---
title: 关于 IIS Express 常用设置
date: 2019-05-01 19:00:00
comments: true
categories:
- misc
tags:
- Visual Studio
- IIS Express
- site binding
- request limit
---

# 关于 IIS Express 常用设置

<a name="site-binding"></a>
## 站点绑定
IIS Express Web 服务器默认只绑定了 `localhost` 的主机名，这就意味着无法通过内网或其他自定义域名进行访问，可通过如下操作添加其他绑定。

在Web宿主项目中的 **.vs** 目录中的 **config** 子目录中，有名为“**applicationhost.config**”配置文件，打开它后，找到如下节点：

```
system.applicationHost/sites/site[name=xxxx]/bindings
```

1. 在该绑定集中的添加一个首节点，假定绑定端口号为： `12345`

```xml
<binding protocol="http" bindingInformation="*:12345:*" />
```

2. 以管理员方式运行“命令提示符”，然后在终端执行器中执行下面命令：

```shell
netsh http add urlacl url="http://*:12345:*" user=everyone
```


<a name="request-limit"></a>
## 请求内容长度限制
IIS Express Web 服务器默认限制了HTTP的请求内容大小，这会导致在上传较大文件时请求被拒绝，通过如下方式可重置默认限制值。

在Web宿主项目中的 **.vs** 目录中的 **config** 子目录中，有名为“**applicationhost.config**”配置文件，打开它后，找到如下节点：

```
system.webServer/security/requestFiltering
```

1. 在该节点下添加如下子节点，假定重新设置请求内容长度限制为： `500MB`

```xml
<requestLimits maxAllowedContentLength="524288000" />
```

2. 然后修改Web宿主项目的 **Web.config** 文件中的如下配置节：

```xml
<system.web>
  <httpRuntime maxRequestLength="524288000" />
</system.web>
```
