---
title: 实体类的动态生成（二）
date: 2018-07-16 00:00:00
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
由于采用字典的方式来保存属性变更值的底层设计思想，导致了性能问题，虽然.NET的字典实现已经很高效了，但相对于直接读写字段的方式而言依然有巨大的性能差距，同时也会导致对属性的读写过程中产生不必要的装箱和拆箱。
那么这次我们就来彻底解决这个问题，同时还要解决“__哪些属性发生过变更__”、“__获取变更的属性集__”这些功能特性，所以我们先把接口定义出来，以便后续问题讲解。

```csharp
/* 源码位于 Zongsoft.CoreLibary 项目的 Zongsoft.Data 命名空间中 */

/// <summary> 表示数据实体的接口。</summary>
public interface IEntity
{
    /// <summary>
    /// 判断指定的属性或任意属性是否被变更过。
    /// </summary>
    /// <param name="names">指定要判断的属性名数组，如果为空(null)或空数组则表示判断任意属性。</param>
    /// <returns>
    ///		<para>如果指定的<paramref name="names"/>参数有值，当只有参数中指定的属性发生过更改则返回真(True)，否则返回假(False)；</para>
    ///		<para>如果指定的<paramref name="names"/>参数为空(null)或空数组，当实体中任意属性发生过更改则返回真(True)，否则返回假(False)。</para>
    ///	</returns>
    bool HasChanges(params string[] names);

    /// <summary>
    /// 获取实体中发生过变更的属性集。
    /// </summary>
    /// <returns>如果实体没有属性发生过变更，则返回空(null)，否则返回被变更过的属性键值对。</returns>
    IDictionary<string, object> GetChanges();

    /// <summary>
    /// 尝试获取指定名称的属性变更后的值。
    /// </summary>
    /// <param name="name">指定要获取的属性名。</param>
    /// <param name="value">输出参数，指定属性名对应的变更后的值。</param>
    /// <returns>如果指定名称的属性是存在的并且发生过变更，则返回真(True)，否则返回假(False)。</returns>
    /// <remarks>注意：即使指定名称的属性是存在的，但只要其值未被更改过，也会返回假(False)。</remarks>
    bool TryGetValue(string name, out object value);

    /// <summary>
    /// 尝试设置指定名称的属性值。
    /// </summary>
    /// <param name="name">指定要设置的属性名。</param>
    /// <param name="value">指定要设置的属性值。</param>
    /// <returns>如果指定名称的属性是存在的并且可写入，则返回真(True)，否则返回假(False)。</returns>
    bool TrySetValue(string name, object value);
}
```

## 设计思想
根本要点是取消用字典来保存属性值回归到字段方式，只有这样才能确保性能，关键问题是如何在写入字段值的时候，标记对应的属性发生过变更的呢？应用布隆过滤器(<span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">Bloom Filter</span></span>)算法的思路来处理这个应用场景是一个完美的解决方案，因为布隆过滤器的空间效率和查询效率极高，而它的缺点在此恰好可以针对性的优化掉。

将每个属性映射到一个整型数（byte/ushort/uint/ulong）的某个比特位(**bit**)，如果发生过变更则将该 **bit** 置为 **1**，只要确保属性与二进制位顺序是确定的即可，算法复杂度是O(1)常量，并且比特位操作的效率也是极高的。

## 实现示范
有了算法，我们写一个简单范例来感受下：

```csharp
public class Person : IEntity
{
    #region 静态字段
    private static readonly string[] __NAMES__ = new string[] { "Name", "Gender", "Birthdate" };
    private static readonly Dictionary<string, PropertyToken<Person>> __TOKENS__ = new Dictionary<string, PropertyToken<Person>>()
    {
        { "Name", new PropertyToken<Person>(0, target => target._name, (target, value) => target.Name = (string) value) },
        { "Gender", new PropertyToken<Person>(1, target => target._gender, (target, value) => target.Gender = (Gender?) value) },
        { "Birthdate", new PropertyToken<Person>(2, target => target._birthdate, (target, value) => target.Birthdate = (DateTime) value) },
    };
    #endregion

    #region 标记变量
    private byte _MASK_;
    #endregion

    #region 成员字段
    private string _name;
    private bool? _gender;
    private DateTime _birthdate;
    #endregion

    #region 公共属性
    public string Name
    {
        get => _name;
        set
        {
            _name = value;
            _MASK_ |= 1;
        }
    }

    public bool? Gender
    {
        get => _gender;
        set
        {
            _gender = value;
            _MASK_ |= 2;
        }
    }

    public DateTime Birthdate
    {
        get => _birthdate;
        set
        {
            _birthdate = value;
            _MASK_ |= 4;
        }
    }
    #endregion

    #region 接口实现
    public bool HasChanges(string[] names)
    {
        PropertyToken<Person> property;

        if(names == null || names.Length == 0)
            return _MASK_ != 0;

        for(var i = 0; i < names.Length; i++)
        {
            if(__TOKENS__.TryGetValue(names[i], out property) && (_MASK_ >> property.Ordinal & 1) == 1)
                return true;
        }

        return false;
    }

    public IDictionary<string, object> GetChanges()
    {
        if(_MASK_ == 0)
            return null;

        var dictionary = new Dictionary<string, object>(__NAMES__.Length);

        for(int i = 0; i < __NAMES__.Length; i++)
        {
            if((_MASK_ >> i & 1) == 1)
                dictionary[__NAMES__[i]] = __TOKENS__[__NAMES__[i]].Getter(this);
        }

        return dictionary;
    }

    public bool TryGetValue(string name, out object value)
    {
        value = null;

        if(__TOKENS__.TryGetValue(name, out var property) && (_MASK_ >> property.Ordinal & 1) == 1)
        {
            value = property.Getter(this);
            return true;
        }

        return false;
    }

    public bool TrySetValue(string name, object value)
    {
        if(__TOKENS__.TryGetValue(name, out var property))
        {
            property.Setter(this, value);
            return true;
        }

        return false;
    }
    #endregion
}

// 辅助结构
public struct PropertyToken<T>
{
    public PropertyToken(int ordinal, Func<T, object> getter, Action<T, object> setter)
    {
        this.Ordinal = ordinal;
        this.Getter = getter;
        this.Setter = setter;
    }

    public readonly int Ordinal;
    public readonly Func<T, object> Getter;
    public readonly Action<T, object> Setter;
}
```

上面实现代码，主要有以下几个要点：

1. 属性设置器中除了对字段赋值外，多了一个位或赋值操作（这是一句非常低成本的代码）；
2. 需要一个额外的整型数的实例字段 `_MASK_` ，来标记对应更改属性序号；
3. 分别增加 `__NAMES__` 和* *`__TOKENS__` 两个静态只读变量，来保存实体类的元数据，以便更高效的实现 [IEntity ](https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/src/Data/IEntity.cs)接口方法。

根据代码可分析出其理论执行性能与原生实现基本一致，内存消耗只多了一个字节（如果可写属性数量小于9），由于 `__NAMES__` 和 `__TOKENS__` 是静态变量，因此不占用实例空间，理论上该方案的整体效率非常高。

## 性能对比
上面我们从代码角度简单分析了下整个方案的性能和消耗，那么实际情况到底怎样呢？跑个分呗（性能对比测试代码地址：[https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/feature-data/samples/Zongsoft.Samples.Entities](https://github.com/Zongsoft/Zongsoft.CoreLibrary/tree/feature-data/samples/Zongsoft.Samples.Entities)），具体代码就不在这里占用版面了，下面给出某次在我的老旧台式机（CPU:Intel __i5-3470__@__3.2GHz__ | RAM:__8GB__ | __Win10 __| __.NET 4.6__）上生成__100万__个实例的截图：

![跑分截图](/blog/images/performance-entity-event.png)

* “Native Object: __295__”表示原生实现版（即简单的读写字段）的运行时长（<em>单位：</em><em><strong>毫秒</strong></em><em>，下同</em>）；
* “Data Entity: __295__”为本案的运行时长，通常本方案比原生方案要慢10毫秒左右，偶尔能跑平（*属于运行环境抖动，可忽略*）；
* “Data Entity(TrySet): __835__”为本方案中 `TrySet(...)` 方法的运行时长，由于 `TrySet(...)` 方法内部需要进行字典查询所以有性能损耗亦属正常，在百万量级跑到这个时长说明性能也是很不错的，如果切换到 .NET Core 2.1 的话，得益于基础类库的性能改善，还能再享受一波性能红利。

综上所述，该方案付出极少的内存成本获得了与原生简单属性访问基本一致的性能，同时还提供了属性变更跟踪等新功能（即高效完成了 [Zongsoft.Data.IEntity](https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/src/Data/IEntity.cs) 接口中定义的那些重要功能特性），为后续业务开发提供了有力的基础支撑。

## 实现完善
上面的实现范例代码并没有实现 `INotifyPropertyChanged` 接口，下面补充完善下实现该接口后的属性定义：

```csharp
public class Person : IEntity, INotifyPropertyChanged
{
    // 事件声明
    public event PropertyChangedEventHandler PropertyChanged;

    public string Name
    {
        get => _name;
        set
        {
            if(_name == value)
                return;

            _name = value;
            _MASK_ |= 1;
            this.PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(Name)));
        }
    }
}
```

如上，属性的设置器中的做了一个新旧值的比对判断和对 `PropertyChanged` 事件激发，其他代码没有变化。

另外，我们使用的是 byte 类型的 `_MASK_` 的标记变量来保存属性的更改状态，如果当实体的属性数量超过 8 个，就需要根据具体数量换成相应的 `UInt16,UInt32,UInt64` 类型，但如果超过 64 就需要采用 `byte[]` 了，当然必须要变动下相关代码，假设以下实体类有 __100 __个属性（注意仅例举了第一个 `Property1` 和最后一个 `Property100` 属性）：

```csharp
public class MyEntity : IEntity
{
    #region 标记变量
    private readonly byte[] _MASK_;
    #endregion

    public Person()
    {
        _MASK_ = new byte[13]; // 13 = Math.Ceiling(100 / 8)
    }

    public object Property1
    {
        get => _property1;
        set
        {
            _property1 = value;
            _MASKS_[0] |= 1; // _MASK_[0 / 8] |= (byte)Math.Pow(2, 0 % 8);
        }
    }

    public object Property100
    {
        get => _property100;
        set
        {
            _property100 = value;
            _MASKS_[12] |= 8; // _MASK_[99 / 8] |= (byte)Math.Pow(2, 99 % 8);
        }
    }
}
```

变化内容为先根据当前属性的顺序号来确定到对应的标记数组的下标，然后再确定对应的掩码值。当然，也别忘了调整 Zongsoft.Data.IEntity 接口中各方法的实现。

```csharp
public class MyEntity : IEntity
{
    public bool HasChanges(params string[] names)
    {
        PropertyToken<UserEntity> property;

        if(names == null || names.Length == 0)
        {
            for(int i = 0; i < _MASK_.Length; i++)
            {
                if(_MASK_[i] != 0)
                    return true;
            }

            return false;
        }

        for(var i = 0; i < names.Length; i++)
        {
            if(__TOKENS__.TryGetValue(names[i], out property) && (_MASK_[property.Ordinal / 8] >> (property.Ordinal % 8) & 1) == 1)
                return true;
        }

        return false;
    }

    public IDictionary<string, object> GetChanges()
    {
        var dictionary = new Dictionary<string, object>(__NAMES__.Length);

        for(int i = 0; i < __NAMES__.Length; i++)
        {
            if((_MASK_[i / 8] >> (i % 8) & 1) == 1)
                dictionary[__NAMES__[i]] = __TOKENS__[__NAMES__[i]].Getter(this);
        }

        return dictionary.Count == 0 ? null : dictionary;
    }

    public bool TryGet(string name, out object value)
    {
        value = null;

        if(__TOKENS__.TryGetValue(name, out var property) && (_MASK_[property.Ordinal / 8] >> (property.Ordinal % 8) & 1) == 1)
        {
            value = property.Getter(this);
            return true;
        }

        return false;
    }

    public bool TrySetValue(string name, object value)
    {
        /* 相对之前版本没有变化 */
        /* No changes relative to previous versions */
    }
}
```

代码变化部分比较简单，只有掩码处理部分需要调整。

## 新问题
有了这些实现范式，定义个实体基类并在基类中完成主要功能即可推广应用了，但是，这里有个掩码类型和处理方式无法通用化实现的问题，如果要把这部分代码交由子类来实现的话，那么代码复用度会大打折扣甚至完全失去复用的意义。

为展示这个问题的艰难，在 [https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/tests/Entities.cs](https://github.com/Zongsoft/Zongsoft.CoreLibrary/blob/feature-data/tests/Entities.cs) 源文件中，写了属性数量不等的几个实体类（Person、Customer、Employee、SpecialEmployee），采用继承方式进行复用性验证，可清晰看到实现的非常冗长繁琐，对实现者的细节把控要求很高、实现上非常容易出错，更致命的是复用度还极差。并且当实体类需要进行属性增减，是非常麻烦的，需要仔细调整原有代码结构中掩码的映射位置，这对于代码维护无意是场恶梦。

## 新办法
解决办法其实很简单，正是本文的标题——“__动态生成__”，彻底解放实现者并确保实现的正确性。业务方不再定义具体的实体类，而是定义实体接口即可，实体类将由实体生成器来动态生成。我们依然“从场景出发”，先来看看业务层的使用。

```csharp
public interface IPerson : IEntity
{
    string Name { get; set; }
    bool? Gender { get; set; }
    DateTime Birthdate { get; set; }
}

public interface IEmployee : IPerson
{
    byte Status { get; set; }
    decimal Salary { get; set; }
}

var person = Entity.Build<IPerson>();
var employee = Entity.Build<IEmployee>();
```

## 总结
至此，终于得到了一个兼顾性能与功能并易于使用且无需繁琐的手动实现的最终方案，虽然刚开始看起来是一个多么平常又简单的任务。那么接下来我们该怎么实现这个动态生成器呢？最终它能性能无损的被实现出来吗？<span data-type="color" style="color:rgb(38, 38, 38)"><span data-type="background" style="background-color:rgb(255, 255, 255)">请关注我们的公众号（</span></span>__<span data-type="color" style="color:rgb(6, 17, 120)"><u>Zongsoft</u></span>__<span data-type="color" style="color:rgb(38, 38, 38)"><span data-type="background" style="background-color:rgb(255, 255, 255)">）留言讨论。</span></span>


__<span data-type="color" style="color:rgb(130, 0, 20)">敬请期待更精彩的下篇，关注我们的公众号可以第一时间看到哦！</span>__
