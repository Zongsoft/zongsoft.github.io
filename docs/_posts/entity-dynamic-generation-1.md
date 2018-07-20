---
title: 实体类的动态生成（一）
date: 2018-07-15 00:00:00
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
在应用开发中，通常都会涉及各种 POJO/POCO 实体类（DO, DTO, BO, VO）的编写，有时这些实体类还需要实现 `INotifyPropertyChanged` 接口以支持属性变更通知，一般我们都会手写这些代码或者通过工具根据数据库表定义抑或别的什么模板、映射文件之类的来静态生成它们。
但是，在业务实现中往往伴随着诸如“__如何简单且高效的获取某个实体实例有哪些属性发生过变更？__”、“__变更后的值是什么？__”这样的问题，而大致的解决方法有：

1. 由实体容器来跟踪实例的属性变更；
2. 改造实体类（譬如继承特定实体基类，在基类中实现这些基础构造）。

方法(1)需要配合一整套架构设计来提供支撑，也不是专为解决上述实体类的问题而设，并且实现和使用也都不够简单高效，故此略过不表。接下来我将通过几篇文章来详细阐述这些问题的来由以及解决方案，并给出完整的代码实现以及性能比对测试。

## 关于源码
下面将要介绍的所有代码均位于我们的开源系列项目（地址：[https://github.com/Zongsoft](https://github.com/Zongsoft)），项目主要采用 [LGPL 2.1授权协议](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)，欢迎大家参与并使用（__<span data-type="color" style="color:#F5222D">请遵照授权协议</span>__）。而本文相关的源码位于其中 [Zongsoft.CoreLibrary](https://github.com/Zongsoft/Zongsoft.CoreLibrary) 项目的 __feature-data__ 分支（[https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/feature-data](https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/feature-data)）及其中的 /samples/Zongsoft.Samples.Entities 范例项目，由于目前我正在忙着造 Zongsoft.Data 数据引擎这个轮子，不排除后面介绍到的代码会有一些调整，待该项目完成后这些代码亦会合并到 __master __分支中，敬请留意。

## 基础版本
万里长城也是从第一块砖头开始磊起来的，就让我们来搬第一块砖吧：

```csharp
public class User
{
    private uint _userId;
    private string _name;

    // 传统写法
    public uint UserId
    {
        get {
            return _userId;
        }
        set {
            _userId = value;
        }
    }

    // C# 7.0 语法
    public string Name
    {
        get => _name;
        set => _name = value;
    }

    // 懒汉写法：仅限不需要操作成员字段的场景
    public string Namespace
    {
        get;
        set;
    }
}
```

以上代码特地用了三种编码方式，它们被C#编译器生成的IL没有模式上的不同，故而性能没有任何区别，大家根据自己的口味采用某种即可，因为我们的源码由于历史原因可能会有一些混写，在此一并做个展示而已。

由于业务需要，我们希望实体类能支持属性变更通知，即让它支持 `INotifyPropertyChanged` 接口，这么简单的需求当然不在话下：

```csharp
public class User : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler PropertyChanged;

    private uint _userId;
    private string _name;

    public uint UserId
    {
        get => _userId;
        set {
            if(_userId == value)
                return;

            _userId = value;
            this.OnPropertyChanged("UserId"); // 传统写法
        }
    }

    public string Name
    {
        get => _name;
        set {
            if(_name == value)
                return;

            _name = value;
            this.OnPropertyChanged(nameof(Name)); // nameof 为 C# 7.0 新增操作符
        }
    }

    protected virtual void OnPropertyChanged(string propertyName)
    {
        // 注意 ?. 为 C# 7.0 新增操作符
        this.PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
```

一切看起来是那么完美，但是，当我们写了几个这样的实体类，尤其是有些实体类的属性还不少时，体验就有点糟糕了。自然我们会想到写个实体基类来实现属性变更通知的基础构造，当然，在某些特定场景也可以通过工具来生成类似上面这样的C#实体类文件，但工具生成的方式有一定局限性并且不易维护（譬如需要在生成的代码基础上进行特定改造），在此不再赘述。

## 实体基类
在进行基础类库或API设计的时候，我有个建议：__从应用场景开始__。具体的作法是，先尝试编写使用这些API的应用代码，待各种应用场景的使用代码基本都完成后，API接口也就自然而然的确定了。譬如，在我们这个需求中我希望这么去使用实体基类：

```csharp
public class User : ModelBase
{
    private uint _userId;
    private string _name;

    public uint UserId
    {
        get => _userId;
        set => this.SetPropertyValue(nameof(UserId), ref _userId, value);
    }

    public string Name
    {
        get => _name;
        set => this.SetPropertyValue(nameof(Name), ref _name, value);
    }
}
```

有了这样的实体基类后，增强了功能后代码依然如第一块砖的“基础版本”一样简洁，真是高兴啊！但这就够了么，能不能把具体实体类里面的成员字段也省了，交给基类来处理呢？嗯，有点意思，试着写下应用场景代码：

```csharp
public class User : ModelBase
{
    public uint UserId
    {
        get => (uint)this.GetPropertyValue(nameof(UserId));
        set => this.SetPropertyValue(nameof(UserId), value);
    }
}
```

看起来棒极了，代码变得更简洁了，真是天才啊！淡定，丧心病狂的 C# 设计者似乎看到了这种普遍的需求，于是在 C# 5 中增加了 `System.Runtime.CompilerServices.CallerMemberNameAttribute` 自定义标记，C# 编译器将自动把调用者名字生成出来传递给加注了该标记的参数，因此这样的代码还可以继续简化：

```csharp
public class User : ModelBase
{
    public uint UserId
    {
        get => (uint)this.GetPropertyValue();
        set => this.SetPropertyValue(value);
    }
}
```

但是，属性的 getter 里面的那个类型强制转换，怎么看都像是一朵“乌云”啊，能不能把它也去掉呢？嗯，利用C#的泛型类型推断可以完美解决它，继续强势进化：

```csharp
public class User : ModelBase
{
    public uint UserId
    {
        get => this.GetPropertyValue(() => this.UserId);
        set => this.SetPropertyValue(() => this.UserId, value);
    }
}
```

哇喔，有点小崇拜自己了，这代码漂亮的一批！至此，实体基类的API接口基本确定，已经迫不及待想要去实现它了。

__提示：__由于采用 `CallerMemberNameAttribute` 自定义标记的参数会导致 C# 编译器要求该参数必需有默认值，因此有些 `SetPropertyValue(...)` 方法重载版本中 `propertyName` 参数需要位于参数集的最后，为了与上面的范例代码对应就省略了这些参数的标记，并保持与原有范例相同的签名设计。

```csharp
using System;
using System.Linq.Expressions;

public class ModelBase : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler PropertyChanged;

    protected object GetPropertyValue([CallerMemberName]string propertyName = null);
    protected T GetPropertyValue<T>(Expression<Func<T>> property);

    protected void SetPropertyValue<T>(string propertyName, ref T field, T value);
    protected void SetPropertyValue<T>(string propertyName, T value);
    protected void SetPropertyValue<T>(Expression<Func<T>> property, T value);
}
```

实体基类的实现主要思路就是采用字典来记录各属性的变更值，有了这个基础，要继续增加诸如“获取哪些属性发生过变更”之类的需求自然就很容易了：

```csharp
public class ModelBase : INotifyPropertyChanged
{
    // other members

    public bool HasChanges(params string[] propertyNames);
    public IDictionary<string, object> GetChangedPropertys();
}
```

具体的代码就不在这里贴出了，有兴趣的可以参考：[https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/master/src/Common/ModelBase.cs](https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/master/src/Common/ModelBase.cs)，从功能角度上看，目前的设计还是不错的。但是，某些方法的设计有严重性能缺陷的，主要有以下几点：

1. 每次读写属性都会解析 <span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">Lambda 表达式的操作会产生巨大的性能损耗；</span></span>
2. <span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">采用字典来保存实体属性值的设计机制，会导致值类型的属性读写反复被装箱(Boxing)、拆箱(Unboxing)；</span></span>
3. <span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">字典的读写效率也远低于直接操作成员字段的语言原语方式。</span></span>

综上所述，虽然目前方案有性能缺陷，但应对一般场景其实是没有问题的，而且功能和易用性方面都是很好的；但是，性能对于后台程序猿而言犹如悬在头顶的<span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">达摩克利斯之剑</span></span>，这正是这个系列文章要最终解决的问题。在此之前，如果大家有关于这个问题的性能优化方案，欢迎关注我们的公众号（__<span data-type="color" style="color:#061178"><u>Zongsoft</u></span>__）留言讨论。

__<span data-type="color" style="color:#820014">敬请期待更精彩的下篇，关注我们的公众号可以第一时间看到哦！</span>__
