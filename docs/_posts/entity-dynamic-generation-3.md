---
title: 实体类的动态生成（三）
date: 2018-07-17 00:00:00
comments: true
categories:
- zongsoft
tags:
- entity
- emit
- dynamic
- generate
- compile
- 实体
- 动态编译
- 动态生成
---

## 前言
在 .NET 中主要有两种动态生成并编译的方式，一种是通过 `System.Linq.Expressions` 命名空间中的 `LambdaExpression` 类的 `CompileToMethod(...)` 方法，但是这种方法只支持动态编译到静态方法，因为这个限制我们只能放弃它而采用 Emitting 生成编译方案，虽然 Emitting 方案强大但是实现起来麻烦不少，必须要手动处理底层 IL 的各种细节，脑补一些 C# 编译器的实现机理，同时还要了解一些基本的 __IL__(<span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)"><strong>I</strong></span></span><span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">ntermediate </span></span><span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)"><strong>L</strong></span></span><span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">anguage</span></span>) 和 __CLR__(JVM) 执行方面的知识。

## 基础知识
因为要采用 Emitting 技术方案，必然需要了解 IL，如果你之前没有怎么接触过，也不用灰心，网上有大量关于 IL 的入门文章，“30分钟入门”还是没问题的哈，毕竟 IL 相对 8086/8088 汇编来说，真的平易近人太多了。

首先你需要一个类似 [ILSpy(http://ilspy.net) ](http://ilspy.net)这样的工具来查看生成的IL或反编译程序集，最近版本还会提供 IL 与对应 C# 的比照解释，用户体验真是体贴得不要不要的。

一、不同于 8086/8088 这样基于寄存器的指令集，IL 和 Java 字节码一样都是基于栈的指令集，它们最明显的区别就是指令的参数指定方式的差异。以“int x = 100+200”操作为例，IL 的指令序列大致是：
```plain
ldc.i4 100
ldc.i4 200
add
stlocl.0
```

* 前两行代码分别将100和200这两个32位整数加载到运算栈(__E__valuation __S__tack)中；
* 第3行的 add 是加法运算指令，它会从运算栈弹出(Pop)两次以得到它需要的两个操作数(Operand)，计算完成后又会将自己的计算结果压入(Push)到计算栈中，这时栈顶的元素就是累加的结果（即整数300）；
* 第4行的 stloc.0 是设置本地变量的指令，它会从计算栈弹出(Pop)一个元素，然后将该元素保存到特定本地变量中（本示例是第一个本地变量）。注：本地变量必须由方法预先声明。

二、基本上汇编语言或类似 IL 这样的中间指令集都没有高级语言中天经地义的 if/else、switch/case、do/while、for/foreach 这样的基本语言结构，它们只有类似 goto/jump/br 这样的无条件跳转和 br.true/br.false/beq/blt/bgt/ceq/clt/cgt 等之类的条件跳转指令，高级语言中的很多基本语言结构都是由编译器或解释器转换成底层的跳转结构的，所以在 Emitting 中我们也需要脑补编译器中这样的翻译机制，将那些 if/else、while、for 之类的翻译成对应的跳转结构。

需要特别指出的是，因为 C/C++/C#/JAVA 之类的高级语言的逻辑运算中有“短路”的内置约定，所以在转换成跳转结构时，必须留意处理这个问题，否则会破坏语义并可能导致运行时错误。

三、因为 IL 支持类名、字段、属性、方法等元素名称中包含除字母、数字、下划线之外的其他字符，所有各高级语言编译器都会利用该特性，主要是为了避免与特定高级语言中用户代码发生命名冲突，我们亦会采用该策略。

有了上面的基础知识，自己稍微花点时间阅读一些 IL 代码，再来翻阅 Zongsoft.Data.Entity 类的源码就简单了。

另外，在反编译阅读 IL 代码的时候，如果你反编译的是 Debug 版本，会发现生成的 IL 对本地变量的处理非常啰嗦，重复保存又紧接着加载本地变量的操作，这是因为编译器没有做优化导致，不用担心，换成用 Release 编译就好很多了，但是依然还是有一些手动优化的空间。

## 接口说明
实体动态生成器类的源码位于 Zongsoft.CoreLibrary 项目中（[https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/src/Data/Entity.cs](https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/src/Data/Entity.cs)），这是一个静态类，其主要公共方法定义如下：

```csharp
public static Entity
{
    public static T Build<T>();
    public static T Build<T>(Action<T> map);
    public static IEnumerable<T> Build<T>(int count, Action<T, int> map = null);

    public static object Build(Type type);
    public static object Build(Type type, Action<object> map);
    public static IEnumerable Build(Type type, int count, Action<object, int> map = null);
}
```

公共的 `Save()` 方法是一个供调试之用的方法，它会将动态编译的程序集保存到文件中，以便使用 ILSpy 这样的工具反编译查看，待 feature-data 合并到 master 分支之后会被移除。

## 关于跑分
在 [https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/samples/Zongsoft.Samples.Entities/Program.cs](https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/samples/Zongsoft.Samples.Entities/Program.cs) 类中的 `PerformanceDynamic(int count)` 是动态生成的跑分（性能测试）代码，需要注意的是，如果是首次动态创建某个实体接口，内部会先进行动态编译。

下面这两种方式跑分测试方式会有不同的性能表现，大家先琢磨下原因再接着往下阅读。

```csharp
private static void PerformanceDynamic(int count)
{
    // 获取构建委托，可能会触发内部的预先编译（即预热）
    var creator = Data.Entity.GetCreator(typeof(Models.IUserEntity));

    // 创建跑分计时器
    var stopwatch = new Stopwatch();
    stopwatch.Start(); //开始计时

    /* 第一种跑分 */
    for(int i = 0; i < count; i++)
    {
        // 调用构建委托来创建实体类实例
        var user = (Models.IUserEntity)creator();

        user.UserId = (uint)i;
        user.Avatar = ":smile:";
        user.Name = "Name: " + i.ToString();
        user.FullName = "FullName";
        user.Namespace = "Zongsoft";
        user.Status = (byte)(i % byte.MaxValue);
        user.StatusTimestamp = (i % 11 == 0) ? DateTime.Now : DateTime.MinValue;
        user.CreatedTime = DateTime.Now;
    }

    stopwatch.Restart(); //重新计时

    /* 第二种跑分 */
    int index = 0;
    // 动态构建指定 count 个实体类实例（懒构建）
    var entities = Data.Entity.Build<Models.IUserEntity>(count);

    foreach(var user in entities)
    {
        user.UserId = (uint)index;
        user.Avatar = ":smile:";
        user.Name = "Name: " + index.ToString();
        user.FullName = "FullName";
        user.Namespace = "Zongsoft";
        user.Status = (byte)(index % byte.MaxValue);
        user.StatusTimestamp = (index++ % 11 == 0) ? DateTime.Now : DateTime.MinValue;
        user.CreatedTime = DateTime.Now;
    }

    stopwatch.Stop(); //停止计时
}
```

在我的老台式机上跑一百万（即count=1,000,000）次，第二种跑分代码比第一种差不多要慢50~100毫秒左右，两者区别就在于 for 循环与 Enumerable/Enumerator 模式的区别，我曾尝试对 `Build<T>(int count)` 方法内部的 `yield return` （由C#编译器将该语句翻译成 Enumerable/Enumerator 模式）改为手动实现，优化的思路是：因为在这个场景中，我们已知 `count` 数量，基于这个必要条件可以剔除 Enumerator 循环中一些不必要的条件判断代码。但是手动写了 Enumerable/Enumerator 后发现，为了代码安全性还是无法省略一些必要的条件判断，因为不能确定用户是否会采用 entities.GetEnumerator() + while 的方式来调用，也就是说即使在确定 `count` 的条件下也占不到任何性能上的便宜，毕竟基本的代码安全性还是要优先保障的。

如上述所述，动态生成的代码并无性能问题，只是在应对一次性创建上百万个实体实例并遍历的场景下，为了排除 Enumerable/Enumerator 模式对性能的一点点“干扰”（这是必须的）采取了一点优化手段，在实际业务中通常不需这么处理，特此说明。

## 使用说明
将原有业务系统中各种实体类改为接口，这些接口可以继承自 `Zongsoft.Data.IEntity` 也可以不用，不管实体接口是否从 `Zongsoft.Data.IEntity` 接口继承，动态生成的实体类都会实现该接口，因此依然可以将动态创建的实体实例强制转换为该接口。

__注意：__实体接口中不能含有事件、方法定义，即只能包含属性定义。

### 变更通知
如果实体需要支持属性变更通知，则实体接口必须增加对 `System.ComponentModel.INotifyPropertyChanged` 接口的继承，但这样的支持需要付出一点点性能成本，以下是动态生成后的部分C#代码。

```csharp
public interface IPerson
{
    string Name { get; set; }
}

// 不支持的属性变更通知版本
public class Person : IPerson, IEntity
{
    public string Name
    {
        get => _name;
        set => {
            _name = value;
            _MASK_ |= 1;
        }
    }
}

/* 增加对属性变更通知的特性 */
public interface IPerson : INotifyPropertyChanged
{
    string Name { get; set; }
}

// 支持属性变更通知版本
public class Person : IPerson, IEntity, INotifyPropertyChanged
{
    // 事件声明
    public event PropertyChangedEventHandler PropertyChanged;

    public string Name
    {
        get => _name;
        set => {
            if(_name == value)  // 新旧值比对判断
                return;

            _name = value;
            _MASK_ |= 1;
            this.PropertyChanged?.Invoke(this, new PropertyChangedEventArgs("Name"));
        }
    }
}
```

所谓一点点性能成本有两点：①需要对新旧值进行比对，比对方法的实现性能对此处有至关影响；②对 `PropertyChanged` 事件的有效性判断并调用事件委托。当然，如果这是必须的 feature 需求，那就无所谓成本了。

提示：关于新旧值比对的说明，如果属性类型是基元类型，动态生成器会生成 bne/be 这样的特定 IL 指令；否则如果该类型重写了 == 操作符则会使用该操作符的实现；否则会调用 Object.Equals(...) 静态方法来比对。

### 扩展属性
在某些场景，需要手动处理属性的 getter 或 setter 的业务逻辑，那该如何在动态生成中植入这些逻辑代码呢？在 `Zongsoft.Data.Entity` 类中有个 `PropertyAttribute` 自定义特性类，可以利用它来声明扩展属性的实现。譬如下面的示例：

```csharp
public static UserExtension
{
    public static string GetAvatarUrl(IUser user)
    {
        if(string.IsNullOrEmpty(user.Avatar))
            return null;

        return "URL:" + user.Avatar;
    }
}

public interface IUser
{
    string Avatar { get; set; }

    [Entity.Property(Entity.PropertyImplementationMode.Extension, typeof(UserExtension))]
    string AvatarUrl { get; }
}

/*
  以下的 User 实体类为动态生成器生成的部分示意代码。
*/
public class User : IUser, IEntity
{
    private string _avatar;

    public string Avatar
    {
        get => _avatar;
        set {
            _avatar = value;
            _MASK_ |= xxx;
        }
    }

    public string AvatarUrl
    {
        get {
            return UserExtension.GetAvatarUrl(this);
        }
    }
}
```

上面的代码比较好理解，就不多说，如果 `IUser` 接口中的 `AvatarUrl` 属性是可读写属性或者有 `System.ComponentModel.DefaultValueAttribute` 自定义特性修饰，那么该属性就会有对应的字段，对应的属性扩展方法也可以获取该字段值。

```csharp
public static class UserExtension
{
    public static string GetAvatarUrl(IUser user, string value)
    {
        if(string.IsNullOrEmpty(value))
            return $"http://...{user.Avatar}...";

        return value;
    }
}

public interface IUser
{
    string Avatar { get; set; }

    [Entity.Property(Entity.PropertyImplementationMode.Extension, typeof(UserExtension))]
    string AvatarUrl { get; set; }
}

/*
  以下的 User 实体类为动态生成器生成的部分示意代码。
*/
public class User : IUser, IEntity
{
    private string _avatar;
    private string _avatarUrl;

    public string Avatar
    {
        get => _avatar;
        set {
            _avatar = value;
            _MASK_ |= xxx;
        }
    }

    // 只有读取获取扩展方法
    public string AvatarUrl
    {
        get => Extension.GetAvatarUrl(this, _avatarUrl);
        set {
            _avatarUrl = value;
            _MASK_ |= xxx;
        }
    }
}
```

当然扩展属性方法支持读写两种，下面是同时实现了两个版本的扩展方法的样子：

```csharp
public static class UserExtension
{
    public static string GetAvatarUrl(IUser user, string value)
    {
        throw new NotImplementedException();
    }

    public static bool SetAvatarUrl(IUser user, string value)
    {
        throw new NotImplementedException();
    }
}

/*
  以下的 User 实体类为动态生成器生成的部分示意代码。
*/
public class User : IUser, IEntity
{
    public string AvatarUrl
    {
        get => UserExtension.GetAvatarUrl(this, _avatarUrl);
        set {
            if(UserExtension.SetAvatarUrl(this, _avatarUrl))
            {
                _avatarUrl = value;
                _MASK_ |= xxx;
            }
        }
    }
}
```

__扩展属性方法的定义约定：__

1. 必须是一个公共的静态方法；
2. 读取方法名以 Get 打头，后面接扩展属性名并区分大小写；
3. 读取方法的第一个参数必须是要扩展实体接口类型，第二个参数可选，如果有的话必须是扩展属性的类型；返回类型必须是扩展属性的类型；
4. 设置方法名以 Set 打头，后面接扩展属性名并区分大小写；
5. 设置方法的第一个参数必须是要扩展实体接口类型，第二参数是扩展属性的类型，表示设置的新值；返回类型必须是布尔类型，返回真(True)表示设置成功否则返回失败(False)，只有返回真对应的成员字段才会被设置更新。

### 单例模式
某些场景中，属性需要采用单例模式来实现，譬如一些集合类型的属性。

```csharp
public interface IDepartment
{
    [Entity.Property(Entity.PropertyImplementationMode.Singleton)]
    ICollection<IUser> Users { get; }
}

/*
  以下的 Department 实体类为动态生成器生成的部分示意代码。
*/
public class Department : IDepartment, IEntity
{
    private readonly object _users_LOCK;
    private ICollection<IUser> _users;

    public Department()
    {
        _users_LOCK = new object();
    }

    public ICollection<IUser> Users
    {
        get {
            if(_users == null) {
                lock(_users_LOCK) {
                    if(_users == null) {
                        _users = new List<IUser>();
                    }
                }
            }

            return _users;
        }
    }
}
```

实现采用的是双检锁模式，必须注意到，每个单例属性都会额外占用一个用于双检锁的 `object` 类型变量。
如果属性类型是__集合接口__，那么动态生成器会选择一个合适的实现该接口的__集合类__；当然，你也可以自定义一个工厂方法来创建对应的实例，在实体属性中通过 `PropertyAttribute` 自定特性中声明工厂方法所在的类型即可。

注意：工厂方法必须是一个公共的静态方法，有一个可选的参数，参数类型为实体接口类型。

```csharp
public static class DepartmentExtension
{
    public static ICollection<IUser> GetUsers(IDepartment department)
    {
        return new MyUserCollection(department);
    }
}

public interface IDepartment
{
    [Entity.Property(Entity.PropertyImplementationMode.Singleton, typeof(DepartmentExtension))]
    ICollection<IUser> Users { get; }
}

/*
  以下的 Department 实体类为动态生成器生成的部分示意代码。
*/
public class Department : IDepartment, IEntity
{
    private readonly object _users_LOCK;
    private ICollection<IUser> _users;

    public Department()
    {
        _users_LOCK = new object();
    }

    public ICollection<IUser> Users
    {
        get {
            if(_users == null) {
                lock(_users_LOCK) {
                    if(_users == null) {
                        _users = DepartmentExtension.GetUsers(this);
                    }
                }
            }

            return _users;
        }
    }
}
```

### 默认值和自定义初始化
有时我们需要只读属性，但又不需要单例模式这种相对较重的实现机制，可以采用 `DefaultValueAttribute` 这个自定义特性来处理这种情况。

提示：实体接口或属性声明的所有自定义特性都会被生成器添加到实体类的对应元素中，后面的演示代码可能会省略这些生成的自定义特性，特此说明。

```csharp
public interface IDepartment
{
    [DefaultValue("Popeye")]
    string Name { get; set; }

    [DefaultValue]
    ICollection<IUser> Users { get; }
}

/*
  以下的 Department 实体类为动态生成器生成的部分示意代码。
*/
public class Department : IDepartment, IEntity
{
    private string _name;
    private ICollection<IUser> _users;

    public Department()
    {
        _name = "Popeye";
        _users = new List<IUser>();
    }

    [DefaultValue("Popeye")]
    public string Name
    {
        get => _name;
        set {
            _name = value;
            _MASK_ |= xxx;
        }
    }

    [DefaultValue()]
    public ICollection<IUser> Users
    {
        get => _users;
    }
}
```

除了支持固定(Mutable)默认值，还支持动态(Immutable)的，所谓动态值是指它的值不在 `DefaultValueAttribute` 中被固化，即指定 `DefaultValueAttribute` 的值为一个静态类的类型，该静态类中必须有一个名为 Get 打头并以属性名结尾的方法，该方法可以没有参数，也可以有一个实体接口类型的参数，如下所示。

```csharp
public static DepartmentExtension
{
    public static DateTime GetCreationDate()
    {
        return DateTime.Now;
    }
}

public interface IDepartment
{
    [DefaultValue(typeof(DepartmentExtension))]
    DateTime CreationDate { get; }
}

/*
  以下的 Department 实体类为动态生成器生成的部分示意代码。
*/
public class Department : IDepartment, IEntity
{
    private DateTime _creationDate;

    public Department()
    {
        _creationDate = DepartmentExtension.GetCreationDate();
    }

    public DateTime CreationDate
    {
        get => _creationDate;
    }
}
```

如果 `DefaultValueAttribute` 默认值自定义特性中指定的是一个类型(即 `System.Type`)，并且该类型不是一个静态类的类型，并且属性类型也不是 `System.Type` 的话，那则表示该类型为属性的实际类型，这对于某些属性被声明为接口或基类的情况下尤为有用，如下所示。

```csharp
public interface IDepartment
{
    [DefaultValue(typeof(MyManager))]
    IUser Manager { get; set; }

    [DefaultValue(typeof(MyUserCollection))]
    ICollection<IUser> Users { get; }
}

/*
  以下的 Department 实体类为动态生成器生成的部分示意代码。
*/
public class Department : IDepartment, IEntity
{
    private IUser _manager;
    private ICollection<IUser> _users;

    public Department()
    {
        _managert = new MyManager();
        _users = new MyUserCollection();
    }

    public IUser Manager
    {
        get => _manager;
        set => _manager = value;
    }

    public ICollection<IUser> Users
    {
        get => _users;
    }
}
```

### 其他说明
默认生成的实体属性为公共属性（即非显式实现方式），当出现实体接口在继承中发生了属性重名，或因为某些特殊需求导致必须对某个实体属性以显式方式实现，则可通过 `Entity.PropertyAttribute` 自定特性中的 `IsExplicitImplementation=true` 来开启显式实现机制。

在实体接口中声明的各种自定义特性(Attribute)，都会被动态生成器原样添加到生成的实体类中。因此之前范例中，凡是接口以及接口的属性声明的各种自定义特性（包括：`DefaultValueAttribute` 、 `Entity.PropertyAttribute` ）都会被添加到动态生成的实体类的相应元素中，这对于某些应用是一个必须被支持的特性。

## 性能测试
在[《实体类的动态生成（二）》](https://zongsoft.github.io/blog/zh-cn/zongsoft/entity-dynamic-generation-2/)中，我们已经验证过设计方案的执行性能了，但结合上面介绍的功能特性细节，还需再提醒的是：因为开启 `DefaultValueAttribute` 、扩展属性方法、单例属性、属性变更通知都会导致生成的代码与最基本字段访问方式有所功能增强，对应要跑的代码量增多，因此对跑分是有影响，但这种影响是确定可知的，它们是 feature 所需并非实现方案、算法缺陷所致，敬请知晓。

譬如图二就是增加了属性变更通知（即实体接口继承了 `INotifyPropertyChanged` ）导致的性能影响（Dynamic Entity 所在行）。

![图一](/images/performance-entity-event.png)
![图二](/images/performance-entity+event.png)

## 写在最后的话
该实体类动态生成器简单易用、运行性能和内存利用率都非常不错（包括提供 IEntiy 接口的超赞功能），将会成为今后我们所有业务系统的基础结构之一，所以后续的文章中（如果还有的话）应该会经常看到它的应用。


算下来花了整整三天时间*（白天晚上都在写）*才完成《实体类的动态生成》系列文章，真心觉得写文章比写代码还累，而且这还是省略了应该配有的一些流程图、架构图的情况下。计划接下来我会为 [Zongsoft(https://github.com/Zongsoft)](https://github.com/zongsoft) 系列开源项目撰写该有的所有文档，照这次这个写法，心底不由升起一丝莫名恐惧和淡淡忧伤来。

__如果你觉得这次的文章对你有所帮助，又或者你觉得我们的开源项目做的还不错，请务必为我们点赞并关注我们的公众号，这或许是我坚持写下去的最大动力来源了。__

<br />

最后，因为写这个东西耽搁了不少造 [Zongsoft.Data](https://github.com/Zongsoft/Zongsoft.Data) 这个轮子的时间，所以接下来得全力去造轮子了。打算每周至少一篇干货满满的技术文章在公众号首发，希望不会让自己失望吧。

关于 [Zongsoft.Data](https://github.com/zongsoft/zongsoft.data) 它一定会是一款性能满血、易用且足够灵活的数据引擎，首发即会支持四大关系型数据库，后续会加入对 __Elasticsearch __的支持，总之，它应该是不同于市面上任何一款 ORM 数据引擎的开源产品。我会陆续与大家分享有关它的一些设计思考以及实现中遇到的问题，当然，也可以在 github 上围观我的进展。
