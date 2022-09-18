---
title: 代码失控与状态机（上）
date: 2018-08-05 19:20:00
comments: true
categories:
- zongsoft
tags:
- coding
- out of control
- state machine
---

## 前言

前几天和某某同学吃饭席间，他聊到每当要修改老项目中自己写的代码时就痛苦不堪，问我是不是也有同感。我觉得这应该是不少程序猿的心声，之所以会这样，大致有两个主因：

1. 项目的整体设计很糟糕，只管往上堆砌各种功能、补丁，对于代码质量和结构关系基本无暇顾及，最终积重难返滑向失控。
2. 对技术缺乏必要的敬畏心，基础不够扎实、知识面较窄，不能（无法）进行合理的规划，最终导致停留在低水平的代码堆砌上，只求完成功能就万事大吉。

程序猿饭桌上总少不了对产品经理的吐槽：“***产品经理又对业务流程进行了疯狂调整，我觉得这会导致状态机无法支持了。***”他的这个槽点让我一时有些语塞，倒不是怀疑产品经理的脑洞还能大到把状态机开到失控，只是诧异难道我们还有比状态机更适合应对业务流程变更的武器吗？

事实上状态机对于软件工程师来说应该是个很基础的知识点，它原理简单却拥有强大的适应力并被广泛应用 *（譬如：游戏开发、工作流、编译器、正则表达式等解析器中）* ，掌握好它的原理和应用，能帮助我们从容应对很多棘手问题，它于程序猿应对复杂流程性问题，就好比医生使用抗生素应对细菌感染一样的最佳武器。同时，它还是防止代码失控的一剂良药。

## 基本概念

状态机一般泛指“有限状态机(<span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)"><strong>F</strong></span></span><span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">inite </span></span><span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)"><strong>S</strong></span></span><span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">tate </span></span><span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)"><strong>M</strong></span></span><span data-type="color" style="color:rgb(51, 51, 51)"><span data-type="background" style="background-color:rgb(255, 255, 255)">achine</span></span>)”，《离散数学》中有关于它的专门章节，以下谨为我对相关概念的形式上的非精准释义，如有出入请以教科书或相关学术资料为准。

* **状态：**顾名思义表示某个时刻系统处于一个特定的阶段。通常我们不考虑中间态，也可以把中间态进行退化处理。当状态发生变更，就叫状态转换(**T**ransfer)或状态迁移(**T**ransition)。
* **事件：**驱动系统进行状态转换/迁移的源，提供这种源的也常被称为“触发器(**T**rigger)”。
* **行为：**当系统进行状态转换时进行的响应处理，提供响应处理的程序也常被称为“处理器(**H**andler)”。

有了上面的基本概念，我们来看一个最简单的状态图：

![状态图](/images/StateDiagram-1.png "状态图")


你可能会奇怪这个图怎么跟网上那些状态机图不一样，连状态转换条件都没有呢？这是因为，我觉得在了解状态机之前，最好先将确立以下两种概念：

- **状态驱动：** 状态机负责根据输入来驱动状态流转。
- **迁移判定：** 在状态流转过程中确定当前状态是否需要进行转换/迁移，以及转换/迁移到哪个状态中的判定机制。

所以，在常见的状态机图中标注的那些状态转换条件只是“**迁移判定**”的一种具体表现形式，它即可以由状态机内置，也可以是独立的判定器来处理，又或者由状态图预先定义好，如此等等。

建立“**状态驱动**”和“**迁移判定**”这两个被抽象化的概念，有助于我们深入理解状态机的机理，并且对我们设计一个鲁棒性和扩展性更好到状态机有实际指导意义。

## 状态机图

以下是表示一个‘简陋’的 Email 地址格式的解析器状态图，状态迁移条件采用正则表达式来表达，其中图二又称为“**状态迁移图**”。


![节点式状态机图](/images/StateDiagram-2.png "图一：节点式状态机图")
图一：节点式


![表格式状态机图](/images/StateDiagram-3.png "图二：表格式状态机图")
图二：表格式（<span data-type="background" style="background-color:#D4380D">红色格</span>表示拒绝或异常；<span data-type="background" style="background-color:#BFBFBF">灰色格</span>表示忽略或无意义；其他表示迁移条件）


## 代码实现

有了上面的状态图，就像建筑工人拿到了详细的建筑设计图纸；现在我们只需要对着状态机图，把它映射成代码即可完成一个基本状态机。状态机图越详细，实现起来就越容易，同时代码的可维护性也越好。

```csharp
public class Email
{
    public string Identifier { get; private set;}
    public string Host { get; private set; }
    public string Domain { get; private set; }

    private Email() {}

    public static Email Parse(string text)
    {
        if(string.IsNullOrEmpty(text))
            return null;

        var state = State.None;

        /* The State-Driven */
        for(int i=0; i<text.Length; i++) {
            var chr = text[i];

            switch(state)
            {
                case State.None:
                    //do state transition decision

                    break;
                case State.Identifier:
                    //do state transition decision

                    break;
                case State.Delimiter:
                    //do state transition decision

                    break;
                case State.Host:
                    //do state transition decision

                    break;
                case State.Dot:
                    //do state transition decision

                    break;
                case State.Domain:
                    //do state transition decision

                    break;
            }
        }

        return new Email(...);
    }

    private enum State
    {
        None,
        Identifier,
        Delimiter,
        Host,
        Dot,
        Domain,
    }
}

```

上面的代码虽然看起来没什么技术含量，但它已经具备了一个状态机最基本的三大要素了（**状态**、**状态驱动**、**迁移判定**），针对具体业务场景我们只需完善和优化它的程序结构，底层原理的基本要义其实就是这么简单。

![Notitle](https://cdn.nlark.com/yuque/0/2018/png/86907/1533456263971-7fd48027-62d1-42ca-b3f9-dcb9f19c04cc.png)


## 失控的大脑

人脑是一个很神奇的存在，它很擅长处理抽象思维，对于逻辑推理也有很好的应对能力，但却有个不擅长处理并发任务的Bug。比如当面临很多个逻辑分支，各分支的判定条件彼此关联，大脑很快就会陷入繁杂的状态中无法自拔。

表现在解决复杂流程相关的任务时就是，写着写着你会发觉脑子好像不够用了，而程序中的 Bug 却像打地鼠游戏中的老鼠一样层出不穷。不难想象，即使脑力过人的你在勉强写完后的某天，产品经理带着他的脑洞又来找你了，在他的威逼利诱下你打开了一个月前的代码，忽然，觉得还是抱着产品经理同归于尽算了……

这大概是某某同学，面对自己曾经的代码时痛苦的根源所在，因为普通人面对复杂流程问题时，终归受人脑算力所限。本质上这是人脑算力有限的一个困境，人类解决这个困境的一个行之有效的办法就是“**分而治之**”，即将一个大问题或复杂问题不断进行分解分化，直至达到人脑能相对轻松理解和处理的程度。

为什么说状态机是解决此类问题的一剂良药？

通过状态机图可以很容易的看到它天生具有“**分解**、**分化**”的特征，一个复杂的流程由多个流程节点组成，这些节点可以理解为对流程的分解，流程节点之间的转移条件（迁移判定）可以看成是被分化后的逻辑分支，如果大脑直接处理整个流程很容易陷入纷扰的流程分支和各种细节中，但是，当我们把眼光聚焦在某个流程节点和它的转移条件上的时候，大脑需要处理的信息量就变得非常少了。

所以，当我们直面一个繁杂的流程图的时候，第一感觉就是复杂、脑阔痛，这其实是大脑的正常反应，当你把眼光聚焦到“Start”节点上，并顺着它往下推，每个节点的信息量一定是大脑能轻松处理的量级，这种顺藤摸瓜的方式反过来也正是流程设计的套路。我有时会被自己刚画完的状态机图给惊讶到，怎么这么复杂？因为当我一点点把细节补充上去后，整体性自然会变得复杂了，但是局部依然是简单的，**而简单就是可靠、鲁棒、可维护性的同义词**。

代码只是状态机图的相关元素的一种表现形式，它与“节点式”或“表格式”的状态机图并无本质不同。

另外，状态机图相对代码而言，它更专注于流程本身，而代码毕竟是具体实现层面的东西，除了流程本身还包括程序结构、业务代码等与流程无关的代码，这些额外的东西对我们解读流程造成了干扰，因而相对纯粹的状态机图就好比是代码实现的“地图”。
经过一段时间后，我们可能已经不记得实现细节了，这时看着状态机图来进行代码解读和修改将会大大提高效率和准确度，这就是提升代码可维护性的有力手段。

如上，状态机是防止代码失控的一剂良药，制备完善的状态机图就是防止代码失控的一种有效手段。


### 课后作业
试着脱离状态机图撸一个“成员访问表达式”的解析器去体验下失控的感受。下次，我们将一起来实现这个东西。

-----

### 附注：
**成员访问表达式：**访问对象方法、属性、字段、索引器（包括字典、列表）这些成员的表达式，其中方法和索引器（包括字典、列表）的参数支持常量和成员表达式（即表达式递归）。详细的文法请参考C#语言手册。譬如：

```csharp
PropertyA
.ListProperty[100]
.MethodA(PropertyB, 'StringConstant for Arg2', 200, ['key'])
.Children['arg1', 'arg2']
```
