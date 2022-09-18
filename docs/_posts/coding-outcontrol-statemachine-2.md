---
title: 代码失控与状态机（下）
date: 2018-09-03 18:00:00
comments: true
categories:
- zongsoft
tags:
- coding
- out of control
- state machine
- expression parser
---

## 序言
在[《代码失控与状态机（上）》](https://zongsoft.github.io/blog/zh-cn/zongsoft/coding-outcontrol-statemachine-1)的文末，我们留了一个解析「成员访问表达式」的“作业”，那么，通过本文我们一起来完成这个作业。

首先，为什么要苦哈哈的写一个这样看上去没什么用的解析器？因为在某些 IoC 或 AOP 容器中*（不幸的是我需要实现一个这样的* IoC *容器）*，常需要动态求解成员访问表达式的值，而解析表达式就是第一步。其实这个“作业”正是编译器技术中词法解析的简化版，自己手动撸一遍，对理解《编译原理》的前端处理技巧是一个很好的入门练手。

其次，我现在正在造一个 ORM 数据引擎，该数据引擎有个很酷的特性就是在 CRUD 中支持类似 [GraphQL](http://graphql.cn) 这样的功能（即数据模式表达式），所以我需要写一个类 [GraphQL](http://graphql.cn) 的解析器，这应该算是一个很有价值的案例。

如上，手写各种“表达式”解析器是很有现实意义和价值的。

## 源码
- 通用词法解析模块*（语法解析及编译器暂未实现）*
> [https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/master/src/Expressions](https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/master/src/Expressions)
- 成员访问表达式解析器
> [https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/feature-data/src/Reflection/Expressions](https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/feature-data/src/Reflection/Expressions)
- 数据模式表达式解析器
> [https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/src/Data/SchemaParser.cs](https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/src/Data/SchemaParser.cs)

## 基础知识
**BNF**(**B**ackus-**N**aur **F**orm)巴克斯范式，在计算机科学领域，**BNF** 是一种适用于上下文无关的语法的符号表述，常用于描述计算编程语言的语法（文法）、文档格式、指令集以及通信协议等，总之它适用于需要准确描述的地方，如果不用这个东西，我们几乎没办法准确而简洁的表述像计算机编程语言这样需要精准表达的东西。

除了基本的 **BNF** 以外，人们为了更简洁的表达而进行了扩展和增强，譬如：**EBNF**(**E**xtended **B**ackus–**N**aur **F**orm)、**ABNF**(**A**ugmented **B**ackus–**N**aur **F**orm)，我找了几篇文章供大家参考（尤其是前三篇）：

- 《[BNF和ABNF的含义与用法](http://kayo.iteye.com/blog/247908)》
- 《[语法规范：BNF与ABNF](https://kb.cnblogs.com/page/189566)》
- 《[EBNF:Extended Backus–Naur Form](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form)》
- 《[ABNF:Augmented BNF for Syntax Specifications(rfc5234)](http://www.ietf.org/rfc/rfc5234.txt)》
- 《[C# Language Specification](https://www.ecma-international.org/publications/files/ECMA-ST/Ecma-334.pdf)》*(应用BNF最强大的范例：C#语言规范) *

除非是去写编程语言的编译器，通常我们不用阅读和编写像 **YACC**(**Y**et **A**nother **C**ompiler **C**ompiler) 或 [ANTLR](http://www.antlr.org)(**AN**other **T**ool for **L**anguage **R**ecognition) 这些工具中的那些非常“精准”的 **BNF** 的语法。有关 YACC 和 ANTLR 的一个具体案例，我推荐下面这篇文章*（不用抠细节，主要关注语法定义部分）*：

[《TiDB 源码阅读系列文章（五）TiDB SQL Parser 的实现》](https://www.pingcap.com/blog-cn/tidb-source-code-reading-5)


我推荐大家阅读和采用各 SQL 手册中使用的 **BNF** 方言来学习应用，因为它们语法约定简单，对付一般应用场景足够用。下面是它们的链接（个人比较偏好我软的 Transact-SQL），敬请食用。

- Transact-SQL 语法约定
> [https://docs.microsoft.com/zh-cn/previous-versions/sql/sql-server-2012/ms177563(v=sql.110)](https://docs.microsoft.com/zh-cn/previous-versions/sql/sql-server-2012/ms177563(v=sql.110))
- PostgreSQL 手册
> [https://www.postgresql.org/docs/10/static/index.html](https://www.postgresql.org/docs/10/static/index.html)
- MySQL 手册
> [https://dev.mysql.com/doc/refman/8.0/en](https://dev.mysql.com/doc/refman/8.0/en)
- Oracle 手册
> [https://docs.oracle.com/en/database/oracle/oracle-database/18/sqlrf](https://docs.oracle.com/en/database/oracle/oracle-database/18/sqlrf)

## 语法规范
关于“成员访问表达式”的详细语法（文法）可以参考《C#语言规范》，下面让我们先看看之前写的那个成员表达式的例子：

```csharp
PropertyA
.ListProperty[100]
.MethodA(PropertyB, 'String\'Constant for Arg2', 200, ['key'].XXX.YYY)
.Children['arg1', PropertyC.Foo]
```

我尝试用自然语言来表述上面代码的意思：

1. 访问某个对象中名为 `PropertyA` 的成员（属性或字段）；
2. 访问上面成员值对象中名为 `ListProperty` 的成员（该成员为列表类型或该成员所属类型有个索引器）；
3. 访问上面成员值对象中名为 `MethodA` 的方法（方法的参数数目不限，此例为4个参数）；
4. 访问上面方法返回值对象中名为 `Children` 的成员（该成员为列表类型或该成员所属类型有个索引器）。

**补充说明：**
- 方法参数数量不定（零或多个），参数类型可以是常量（字符串、数字）或成员访问表达式；
- 列表属性或索引器参数至少一个多则不限，参数类型同方法参数；
- 字符串常量使用单引号或双引号标注，支持 `\` 反斜杠转义符；
- 数字常量支持尾缀标注，即“L”表示长整型、“M”或“m”表示 decimal 类型等。

如上，即使我写了这么长篇的文字，依然没有精确而完整的完成对“成员表达式”的语法表达，可见我们必须借助 **BNF** 这样东西才能进行精准表达。下面是它的 **BNF** 范式（采用的是 [Transact-SQL 语法规范](https://docs.microsoft.com/zh-cn/previous-versions/sql/sql-server-2012/ms177563(v=sql.110))）：

```plain
expression ::= {member | indexer}[.member | indexer][...n]

member ::=  identifier | method
indexer ::= "[" {expression | constant}[,...n] "]"
method ::= identifier([expression | constant][,...n])
identifier ::= [_A-Za-z][_A-Za-z0-9]*
constant ::= "string constant" | number
number ::= [0-9]+{.[0-9]}?[L|m|M|f|F]
```

如上，即使我们采用的不是能直接生成词法解析器(Parser)的“高精准”的 **BNF** 表达式，但它依然足够精确、简洁。

## 状态机图
有了确切的语法规范/文法（即 BNF 范式表达式）之后，我们就可以有的放矢的绘制表达式解析器的状态机图了。

![成员访问表达式解析器状态机图](/images/MemberExpression-StateDiagram.png "成员访问表达式解析器状态机图")


**状态说明：**
- **I**dentifier：标识态，表示处于成员（属性、字段、方法）名称状态；
- **S**eparator：分隔符态，表示处于成员分隔符（即圆点）状态；
- **G**utter：空隙态，表示索引器或方法参数结束后，所处于的空隙状态；
- **I**ndexer：索引器态，表示处于的索引器内部的就绪状态，它可以继续接受一个有效的非终结符，也可以是一个终结符；
- **P**arameter：参数态，表示处于索引器或方法参数的完结状态，它必须等待一个终结符（逗号或括号）；
- **S**tring：字符串常量态，表示处于字符串常量的内部，它可以接受任意字符，如果遇到终结符（匹配的单引号或双引号）则转入参数态；
- **N**umber：数字常量态，表示处于数字字面量，它可以接受任意数字字符，如果遇到终结符（尾缀符）则转入参数态。

因为方法和索引器的参数有可能是表达式，因此在实现上需要进行递归栈处理，所以流程图中标有压栈(**P**ush)、出栈(**P**op)的行为，通过虚线表示对应的激发操作。所有左方括号 `[` 通路会激发压栈操作，同时右方括号 `]` 通路会激发对应的出栈操作；因为版面问题，上述流程图并没有标注出圆括号*（方法参数）*通路的出入栈的部分，但是逻辑等同于方括号*（索引器）*部分。

**提示：**
- 如果在状态迁移判定中出现状态图中未定义的字符，则表示输入参数有特定的语法错误。
- 如果当文本解析完成时递归栈仍不为空，则说明索引器或方法的参数没有匹配完毕。

关于解析器状态机的设计，我没有发现具有普适性的设计指导方案，大家可以根据自己的理解设定不同于上图的状态定义；至于对状态设置粒度的把握，总体原则是要具备逻辑或概念上的自恰性、并方便绘图和编程实现就可以了。


## 源码解析
位于 [Zongsoft.Reflection.Expressions](https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/feature-data/src/Reflection/Expressions) 命名空间中的接口和类整体上与 System.Linq.Expressions 命名空间中的相关类的设计类似。大致类图如下：

![成员访问表达式解析静态类图](/images/MemberExpression-ClassDiagram.png "成员访问表达式解析静态类图")


提供解析功能的是 MemberExpressionParser 这个内部静态类（状态机类），它的 Parse(string text) 即为状态驱动函数，它遍历输入参数的文本字符，交给具体的私有方法 DoXXX(context) 进行状态迁移判定，如此循环即完成整个解析工作，整体结构与[《代码失控与状态机（上）》](https://zongsoft.github.io/blog/zh-cn/zongsoft/coding-outcontrol-statemachine-1)中介绍的状态机的程序结构一致，具体代码如下：

```csharp
public static IMemberExpression Parse(string text, Action<string> onError)
{
    if(string.IsNullOrEmpty(text))
        return null;

    //创建解析上下文对象
    var context = new StateContext(text.Length, onError);

    //状态迁移驱动
    for(int i = 0; i < text.Length; i++)
    {
        context.Character = text[i];

        switch(context.State)
        {
            case State.None:
                if(!DoNone(ref context, i))
                    return null;

                break;
            case State.Gutter:
                if(!DoGutter(ref context, i))
                    return null;

                break;
            case State.Separator:
                if(!DoSeparator(ref context, i))
                    return null;

                break;
            case State.Identifier:
                if(!DoIdentifier(ref context, i))
                    return null;

                break;
            case State.Method:
                if(!DoMethod(ref context, i))
                    return null;

                break;
            case State.Indexer:
                if(!DoIndexer(ref context, i))
                    return null;

                break;
            case State.Parameter:
                if(!DoParameter(ref context, i))
                    return null;

                break;
            case State.Number:
                if(!DoNumber(ref context, i))
                    return null;

                break;
            case State.String:
                if(!DoString(ref context, i))
                    return null;

                break;
        }
    }

    //获取最终的解析结果
    return context.GetResult();
}
```

**代码简义：**
- 其中表示状态的枚举与上面的解析器状态机流程图的定义完全一致。
- 内部的 StateContext 结构用来保存解析过程中的各种数据、状态、字符缓存等，以及与上下文相关的操作方法等。
- 内部的 StateVector 结构用来保存解析过程中的标记开关（布尔）的状态，譬如当前数值常量的类型、当前字符是否位于字符串常量的转义符态、标识(**I**dentifier)中间是否含有空白字符等。

## 其他延展
在 [Zongsoft.Data](https://github.com/Zongsoft/Zongsoft.Data) 数据引擎里面有个数据模式(Schema)的概念，它是一种在数据操作中定义数据形状的表达式，有点类似于 [GraphQL](http://graphql.cn) 表达式的功能（不含查询条件）。

譬如有一个名为 `Corporation` 的企业实体类，它除了企业编号、名称、简称等单值属性外，还有企业法人、部门集合等这样的“一对一”和“一对多”的复合（导航）属性等。现在假设我们调用数据访问类的 `Select` 方法进行查询调用：

```csharp
var entities = dataAccess.Select<Corporation>(
    Condition.GreaterThanEqual("RegisteredCapital", 100));
```

以上代码表示查询 `Corporation` 实体对应的表，条件为 `RegisteredCapital` 注册资本大于等于100万元的记录，但缺乏表达 `Corporation` 实体关联的导航属性的语义。采用数据模式(Schema)来定义操作的数据形状，大致如下：

```csharp
var schema = @"
CorporationId, Name, Abbr, RegisteredCapital,
Principal{Name, FullName, Avatar},
Departments:10(~Level, NumberOfPeople)
{
    Name, Manager
    {
        Name, FullName, JobTitle, PhoneNumber
    }
}";

var entities = dataAccess.Select<Corporation>(
    schema,
    Condition.GreaterThanEqual("RegisteredCapital", 100) &
    Condition.Like("Principal.Name", "钟%"));
```

通过数据访问方法中的 `schema` 参数，我们可以方便的定义数据形状（含一对多导航属性的分页和排序设置），这样就省去了多次访问数据库进行数据遍历的操作，大大提高了运行效率，同时简化了代码。

数据模式中各成员以逗号分隔，如果是复合属性则可以用花括号来限定其内部属性集，对于一对多的复合属性，还可以定义其分页和排序设置。以下是它的 **BNF** 范式：

```plain
schema ::=
{
    * |
    ! |
    !identifier |
    identifier[paging][sorting]["{"schema [,...n]"}"]
} [,...n]

identifier ::= [_A-Za-z][_A-Za-z0-9]*
number ::= [0-9]+

paging ::= ":"{
    {*|?}|
    number[/{?|number}]
}

sorting ::=
"("
    {
        [~|!]identifier
    }[,...n]
")"
```

**提示：**惊叹号表示排除的意思，一个惊叹号表示排除之前的所有成员定义；以惊叹号打头的成员标识，表示排除之前定义的该成员（如果之前有定义的话，没有则忽略）。

**分页设置的释义：**
> `*` 返回所有记录（即不分页）；
> `?` 返回第一页，页大小为系统默认值，等同于 `1/?` 格式（数据引擎默认设置）；
> `n` 返回 n 条记录，等同于 `1/n` 格式；
> `n/m` 返回第 n 页，每页 m 行；
> `n/?` 返回第 n 页，页大小为系统默认值；

![数据模式解析器状态机图](/images/DataSchema-StateDiagram.png "数据模式解析器状态机图")


以上是数据模式表达式的解析器状态机图，具体实现代码这里就不再赘述，总体上跟“成员访问表达式”解析器类似。

## 结尾
在很多应用状态机场景的编程中，绘制一个状态机图对于实现是具有非常重要的指导意义，希望通过这两个具体的案例能对大家有所启示。

其实 Linux/Unix 中的命令行，也是一个很好的案例，有兴趣的可以尝试写下它的 **BNF** 和解析状态机图。

这次我们介绍了文本解析相关的状态机的设计和实现，其实还有与工作流相关的通用状态机也是一个非常有趣的应用场景，通用状态机可以应用在游戏、工作流、业务逻辑驱动等方面。去年下半年因为业务线的需要，我花了差不多一两个礼拜的时间实现了一个完备的通用状态机，自我感觉设计得不错，但因为时间局促，在状态泛型实现上有个小瑕疵，以后做完优化后再来介绍它的架构设计和实现，这个系列就先且到此为止罢。
