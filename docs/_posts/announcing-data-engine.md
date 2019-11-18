---
title: Zongsoft.Data 发布公告
date: 2019-11-19 00:00:00
comments: true
categories:
- zongsoft
tags:
- ORM
- entity framework
- data access
- data engine
- 数据访问
- 数据引擎
---

# Zongsoft.Data 发布公告

很高兴我们的 **ORM** 数据访问框架([**_Zongsoft.Data_**](https://github.com/Zongsoft/Zongsoft.Data))在历经两个 **SaaS** 产品的应用之后，今天正式宣布对外推广！
这是一个类 [**GraphQL**](https://graphql.cn/) 风格的 **ORM**(**O**bject/**R**elational **M**apping) 数据访问框架。


<a name="intro"></a>
## 又一个轮子？

在很长时间里，**.NET** 阵营似乎一直缺乏一个被普遍使用的 **ORM** 数据访问框架，从最早的原生 **ADO.NET** 到舶来品 **iBatis.NET** 和 **Hibernate.NET**，后来又经历了 **Linq for SQL** 与 **E**ntity **F**ramework 的混战，可能是因为 **E**ntity **F**ramework 早期版本的模糊定位和反复变更的设计导致了它失之霸主之位，进而造就了一段百舸争流、群雄共逐的战国时代。在历经漫长而反复的期待、失望、纠结和痛苦之后，我终于决定动手造一个轮子。


<a name="design"></a>
## 设计理念

在开始动手之前，先确定以下基本设计原则：

- 数据库优先(**D**ata**b**ase **F**irst)
- 严格的 POCO/POJO 支持
- 映射模型与代码完全隔离
- 禁止业务层出现 **SQL** 和类 **SQL** 代码

在一个业务系统中，数据结构及其关系毋庸置疑是最底层的基础性结构，数据库应由系统架构师或开发负责人进行仔细设计 _（**N**o **S**chema/**W**eakly **S**chema 的思潮是涂抹了蜂蜜的毒药）_，数据访问映射以数据库表结构关系为基石，在此之上业务层亦以概念映射模型为准绳，层级之间相互隔离。

领域模型实体避免通过注解 _(标签)_ 来进行元数据定义，应确保严格符合 POCO/POJO 范式。通过语义化的 **S**chema 来声明访问的数据结构关系，禁止应用层的 **SQL** 和 **Linq** 式的类 **SQL** 代码可降低业务层对数据层的依赖、提升代码可维护性外，还具备更加统一可控的便利性，并为数据访问引擎的实现提供了更大的优化空间和自由度。


<a name="samples"></a>
## 范例说明

下面通过三个的例子 _（注：例子均基于 [**Zongsoft.Community**](https://github.com/Zongsoft/Zongsoft.Community) 项目）_ 来佐证上面的部分设计理念，更多示例和阐述请参考 [**_Zongsoft.Data_**](https://github.com/Zongsoft/Zongsoft.Data) 项目的 [**_README.md_**](https://github.com/Zongsoft/Zongsoft.Data/blob/master/README-zh_CN.md) 文档和 [**_Zongsoft.Community_**](https://github.com/Zongsoft/Zongsoft.Community) 项目的代码。

> **提示：** 下面的范例均基于 [**_Zongsoft.Community_**](https://github.com/Zongsoft/Zongsoft.Community) 开源项目，该项目是一个完整的论坛社区的后台程序。你可能需要预先阅读一下该项目的[《数据库表结构设计》](https://github.com/Zongsoft/Zongsoft.Community/blob/master/database/Zongsoft.Community.md)文档，以便更好的理解范例代码的业务逻辑。


<a name="sample_1"></a>
### 示例一

导航查询及导航过滤
```csharp
var forums = this.DataAccess.Select<Forum>(
    Condition.Equal("SiteId", this.User.SiteId) &
    Condition.In("Visibility", Visibility.Internal, Visibility.Public) |
    (
        Condition.Equal("Visibility", Visibility.Specified) &
        Condition.Exists("Users",
                  Condition.Equal("UserId", this.User.UserId) &
                  (
                      Condition.Equal("IsModerator", true) |
                      Condition.NotEqual("Permission", Permission.None)
                  )
        )
    ),
    "*, MostRecentThread{ThreadId,Title,Creator{Name,Nickname,Avatar}}"
);
```
上述数据访问的查询方法大致生成如下SQL脚本：
```sql
SELECT
    t.*,
    t1.ThreadId AS 'MostRecentThread.ThreadId',
    t1.Title AS 'MostRecentThread.Title',
    t1.CreatorId AS 'MostRecentThread.CreatorId',
    t2.UserId AS 'MostRecentThread.Creator.UserId',
    t2.Name AS 'MostRecentThread.Creator.Name',
    t2.Nickname AS 'MostRecentThread.Creator.Nickname',
    t2.Avatar AS 'MostRecentThread.Creator.Avatar'
FROM Forum t
    LEFT JOIN Thread AS t1 ON
        t.MostRecentThreadId=t1.ThreadId
    LEFT JOIN UserProfile AS t2 ON
        t1.CreatorId=t2.UserId
WHERE
    t.SiteId = @p1 AND
    t.Visibility IN (@p2, @p3) OR
    (
        t.Visibility = @p4 AND
        EXISTS
        (
            SELECT u.SiteId, u.ForumId, u.UserId
            FROM ForumUser u
            WHERE u.SiteId = t.SiteId AND
                  u.ForumId = t.ForumId AND
                  u.UserId = @p5 AND
                  (
                      u.IsModerator = @p6 OR
                      u.Permission != @p7
                  )
        )
    );
```

> 上述示例通过 `Select` 查询方法的 `schema` 参数 _（即值为 `*, MostRecentThread{ThreadId,Title,Creator{Name,Nickname,Avatar}}` 的参数）_ 从数据结构关系的层次指定了查询数据的形状，因而不再需要 **SQL** 或类 **SQL** 语法中 **JOIN** 这样命令式的语法元素，它不光提供了更简洁且语义化的 **API** 访问方式，而且还给数据访问引擎底层提供了更大的优化空间和自由度。
> 
> 如果将 `Select` 查询方法的 `schema` 参数值改为 `*,Moderators{*},MostRecentThread{ThreadId,Title,Creator{Name,Nickname,Avatar}}` 后，数据访问引擎会将查询内部分解为一对多的两条 **SQL** 语句进行迭代执行，而这些都不需要业务层进行分拆处理，因而提升了效率并降低了业务层的复杂度。
> 
> **注：** 将 **S**chema 模式表达式通过 **W**eb **API** 提供给前端应用，将大大减少后端开发的工作量，提升前后端的工作效率。


<a name="sample_2"></a>
### 示例二

一对多的关联新增
```csharp
// 构建待新增的实体对象
var forum = new
{
    SiteId = this.User.SiteId,
    GroupId = 100,
    Name = "xxxx",

    // 一对多的导航属性
    Users = new ForumUser[]
    {
      new ForumUser { UserId = 1001, IsModerator = true },
      new ForumUser { UserId = 1002, Permission = Permission.Read },
      new ForumUser { UserId = 1003, Permission = Permission.Write },
    }
}

// 执行数据新增操作
this.DataAccess.Insert<Forum>(forum, "*, Users{*}");
```
上述数据访问的新增方法大致生成如下SQL脚本：
```sql
/* 主表插入语句，执行一次 */
INSERT INTO Forum (SiteId,ForumId,GroupId,Name,...) VALUES (@p1,@p2,@p3,@p4,...);

/* 子表插入语句，执行多次 */
INSERT INTO ForumUser (SiteId,ForumId,UserId,Permission,IsModerator) VALUES (@p1,@p2,@p3,@p4,@p5);
```

> 上述示例通过 `Insert` 新增方法的 `schema` 参数（即值为 `*,User{*}` 的参数）指定了新增数据的形状，由数据访问引擎根据映射定义自动处理底层的 **SQL** 执行方式，确保业务层代码的简洁和更高的执行效率。


<a name="sample_3"></a>
### 示例三

一对一和一对多的关联更新，对于“一对多”的导航属性，还能确保该属性值 _(集合类型)_ 以 **UPSERT** 模式写入。
```csharp
public bool Approve(ulong threadId)
{
    //构建更新的条件
    var criteria =
        Condition.Equal(nameof(Thread.ThreadId), threadId) &
        Condition.Equal(nameof(Thread.Approved), false) &
        Condition.Equal(nameof(Thread.SiteId), this.User.SiteId) &
        Condition.Exists("Forum.Users",
            Condition.Equal(nameof(Forum.ForumUser.UserId), this.User.UserId) &
            Condition.Equal(nameof(Forum.ForumUser.IsModerator), true));

    //执行数据更新操作
    return this.DataAccess.Update<Thread>(new
    {
        Approved = true,
        ApprovedTime = DateTime.Now,
        Post = new
        {
            Approved = true,
        }
    }, criteria, "*,Post{Approved}") > 0;
}
```
上述数据访问的更新方法大致生成如下SQL脚本：
```sql
/* 以下代码为支持 OUTPUT/RETURNING 子句的数据库（如：SQLServer,Oracle,PostgreSQL） */

/* 根据更新的关联键创建临时表 */
CREATE TABLE #TMP
(
    PostId bigint NOT NULL
);

/* 更新主表，并将更新的关联键输出到内存临时表 */
UPDATE T SET
    T.[Approved]=@p1,
    T.[ApprovedTime]=@p2
OUTPUT DELETED.PostId INTO #TMP
FROM [Community_Thread] AS T
    LEFT JOIN [Community_Forum] AS T1 ON /* Forum */
        T1.[SiteId]=T.[SiteId] AND
        T1.[ForumId]=T.[ForumId]
WHERE
    T.[ThreadId]=@p3 AND
    T.[Approved]=@p4 AND
    T.[SiteId]=@p5 AND EXISTS (
        SELECT [SiteId],[ForumId]
        FROM [Community_ForumUser]
        WHERE [SiteId]=T1.[SiteId] AND
              [ForumId]=T1.[ForumId] AND
              [UserId]=@p6 AND
              [IsModerator]=@p7
    );

/* 更新关联表 */
UPDATE T SET
    T.[Approved]=@p1
FROM [Community_Post] AS T
WHERE EXISTS (
    SELECT [PostId]
    FROM #TMP
    WHERE [PostId]=T.[PostId]);
```

> 上述示例通过 `Update` 更新方法的 `schema` 参数（即值为 `*,Post{Approved}` 的参数）指定了更新数据的形状，数据访问引擎将根据数据库类型生成高效的 **SQL** 语句，对于业务层而言这一切都是无感的、透明的。
> 
> 对于一对多的导航属性，数据访问引擎默认将以 **UPSERT** 模式处理子集的写入，关于 **UPSERT** 更多信息请参考 [**_Zongsoft.Data_**](https://github.com/Zongsoft/Zongsoft.Data) 项目文档。


<a name="performance"></a>
## 性能

我们希望提供最佳的**综合性价比**，对于一个 **ORM** 数据访问引擎来说，性能的关注点主要 _(不限)_ 有这些要素：

1. 生成简洁高效的 **SQL** 脚本，并尽可能利用特定数据库的最新 **SQL** 语法；
2. 数据查询结果的实体组装(**P**opulate)过程必须高效；
3. 避免反射，有效的语法树缓存。

实现层面我们采用 **E**mitting 动态编译技术对实体组装(**P**opulate)、数据参数绑定等进行预热处理，可查阅 [**_DataPopulator_**](https://github.com/Zongsoft/Zongsoft.Data/blob/master/src/Common/DataPopulatorProviderFactory.cs) 等相关类的源码深入了解。


<a name="other"></a>
## 其他

得益于 **“以声明方式来表达数据结构关系”** 的语义化设计理念，相对于命令式设计而言，它使得程序意图更加聚焦，天然地对底层数据的表达和优化更加宽容与自由。

更多详细内容 _（譬如：读写分离、继承表、数据模式、映射文件、过滤器、验证器、类型转换、数据隔离）_ 请查阅相关文档。


<a name="support"></a>
## 支持赞助

我们欢迎并期待任何形式的**推广**支持！

如果你认同我们的设计理念请为这个项目点赞(**S**tar)，如果你认为该项目很有用，并且希望支持它未来的发展，请给予必要的资金来支持它：

1. 关注 **Zongsoft 微信公众号**，对我们的文章进行打赏；
2. 加入 [**Zongsoft 知识星球圈**](https://t.zsxq.com/2nyjqrr)，可以获得在线问答和技术支持；
3. 如果您的企业需要现场技术支持与辅导，又或者需要开发新功能、即刻的错误修复等请[发邮件](mailto:zongsoft@qq.com)给我。
