---
title: 平滑的加权轮询均衡算法
date: 2022-09-15 00:00:00
comments: true
categories:
- zongsoft
tags:
- balancing
- weighted
- round-robin
- smooth
- 加权轮询
- 负载均衡
- 权重均衡
---

## 前言

在反向代理、路由、分布式应用调度等场景中通常都需要用到负载均衡算法，负载均衡的关键要点是“**均衡**”，即确保调用请求能均衡的落到多个处理节点上，负载均衡算法一般使用随机或轮询都可以保证均衡性。

现实中由于服务器性能或资源分配的差异，导致我们需要为服务节点设置不同的权重，权重高的节点得到更多流量，同时降低低权重节点的流量比例。也即带权重的均衡算法。

下面我们讨论几种常见的负载均衡算法，并针对其中一种给出完整的算法讲解及实现。

## 一、随机

这是最简单的负载均衡算法，每次生成一个随机数，然后对服务节点数进行取模，模值即为服务节点序号，很明显这只能做到“均匀”，无法根据各服务节点的权重进行加权分配。不过略加调整即可实现加权分配：
构造一个范围为总权重值的序列，然后用随机数对总权重取模，模值所在区间即为对应的服务节点。譬如：有三个服务节点，其权重分别为：`50`、`30`、`20`，则节点集图像大致如下：
> `|<-----------A----------->|<-----B----->|<---C--->|`
> `|<0--------------------50>|<51-------80>|<81--100>|`

### 代码简示：

```csharp
struct Node<TKey> where TKey : IEquatable<TKey>
{
	public Node(TKey key, int boundary) {
		this.Key = key;
		this.Boundary = boundary;
	}

	public TKey Key;
	public int Boundary;
}

class NodeSelector
{
	int _total;
	Node<string> _nodes;

	void Initialize() {
		_total = 50 + 30 + 20;
		_nodes = new[] {
			new Node<string>("Node-A", 50),
			new Node<string>("Node-B", 50 + 30),
			new Node<string>("Node-C", 50 + 30 + 20),
		};
	}

	string Select() {
		var value = Randomizer.GenerateInt32() % _total;

		for(int i = 0; i < _nodes.Length; i++) {
			if(value <= _nodes[i].Boundary)
				return _nodes[i].Key;
		}

		return null;
	}
}
```

随机算法的表现恰如其名，在一个甚至多个调度周期内也无法确保各节点的权重匹配度，只能在大样本条件下满足权重的概率分布，总之就两字：随缘。

## 二、一致哈希

关于一致性哈希算法的文章已经汗牛充栋，亦不是本文的重点，所以就不再赘述。在构建哈希环的时候需要依据服务节点的权重比来设置相应数量的虚拟节点，之后确定服务节点的算法与上述随机算法基本差不多。

## 三、平滑加权轮询

终于来到本文的重点部分，我们假设有三个服务节点，其权重分别为：`4`、`2`、`1`，那么在一个调度周期内，最简单调度序列如：`{A,A,A,A,B,B,C}`、`{C,B,B,A,A,A,A}` 或 `{B,B,C,A,A,A,A}`，但直觉这样的调度顺序不友好，因为它会在某一阵把压力都落到同一个节点上，导致某个节点突然很忙的情况，类似汽车换挡的那种顿挫感。

如果调度序列变成：`{A,B,A,C,A,B,A}` 或 `{A,A,B,A,C,A,B}` 这样就显得“平滑”和“均衡”多了，我们主要参考 Nginx 和 LVS 采用的两种算法。

### Nginx 算法

- Nginx 的实现源码：https://github.com/nginx/nginx/blob/52327e0627/src/http/ngx_http_upstream_round_robin.c
- Nginx 的算法摘要：https://github.com/nginx/nginx/commit/52327e0627f49dbda1e8db695e63a4b0af4448b1
	> on each peer selection we increase current_weight of each eligible peer by its weight, select peer with greatest current_weight and reduce its urrent_weight by total number of weight points distributed among peers.

#### 算法详解
- 当前节点集初始值均为零：`{0,0,0}`
- 所有节点的当前权重值加上设定的权重值
- 在当前节点集中选取最大权重值的节点作为命中节点
- 命中节点的当前权重值减去总权重值作为其新权重值，其他节点保持不变

设 `A`、`B`、`C` 三个节点的权重分别为：`4`、`2`、`1`，演算步骤如下：
步骤 | 选择前当前值 | 选择节点(命中) | 选择后当前值
:--:|:----------:|:------------:|:---------:|
 1 | { 4, 2, 1} | A | {-3, 2, 1}
 2 | { 1, 4, 2} | B | { 1,-3, 2}
 3 | { 5,-1, 3} | A | {-2,-1, 3}
 4 | { 2, 1, 4} | C | { 2, 1,-3}
 5 | { 6, 3,-2} | A | {-1, 3,-2}
 6 | { 3, 5,-1} | B | { 3,-2,-1}
 7 | { 7, 0, 0} | A | { 0, 0, 0}

由上发现三个节点的命中次数符合 **4:2:1**，而且权重大的节点不会霸占选择权。经过一个周期(7轮选择)后，当前权重值又回到了`{0, 0, 0}`，以上过程将按照周期进行循环，完全符合我们先前期望的平滑性。

#### 数学证明
该算法的合理性和平滑性的数学证明：https://tenfy.cn/2018/11/12/smooth-weighted-round-robin

### LVS 算法

**L**inux **V**irtual **S**erver 采用的是另外一种，算法[wiki](http://kb.linuxvirtualserver.org/wiki/Weighted_Round-Robin_Scheduling)文档：http://kb.linuxvirtualserver.org/wiki/Weighted_Round-Robin_Scheduling

从算法步骤和计算量上看，相对 Nginx 而言 LVS 算法略微简单一些，性能可能会略好一点点（*但都是同一个量级*）；通过模拟数据发现当节点权重差异较大时，其平滑性没有 Nginx 算法好。

## 总结

在 [Zongsoft.Data](https://github.com/Zongsoft/Framework/tree/master/Zongsoft.Data) 数据访问框架的读写分离中需要将读写操作路由到不同权重的数据库，于是采用 Nginx 的平滑权重轮询均衡算法实现了数据源路由选择器，下面分别是平滑权重轮询器和数据路由的代码：

- 平滑权重轮询源码：https://github.com/Zongsoft/Framework/blob/master/Zongsoft.Core/src/Components/Weighter.cs
- 数据源权重选择器：https://github.com/Zongsoft/Framework/blob/master/Zongsoft.Data/src/Common/DataSourceSelector.cs


-----

## 参考资料：
- [Nginx 平滑的基于权重轮询算法分析](https://tenfy.cn/2018/11/12/smooth-weighted-round-robin)
- [Nginx 负载均衡及算法分析](https://pandaychen.github.io/2019/12/15/NGINX-SMOOTH-WEIGHT-ROUNDROBIN-ANALYSIS)
- [Nginx SWRR 算法解读](http://claude-ray.com/2019/08/10/nginx-swrr)
