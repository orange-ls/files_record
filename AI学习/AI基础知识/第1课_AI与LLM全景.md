# 第1课 AI与LLM全景

## 学习目标

学完本课，你应该能够回答下面这些问题：

- AI是什么？
- 为什么会出现机器学习？
- 深度学习和机器学习有什么区别？
- Transformer为什么改变了整个AI行业？
- GPT为什么突然火起来？
- ChatGPT到底属于AI中的哪一层？
- LLM究竟是什么？

## 一、本课为什么重要？

很多人在学习LLM的时候，一上来就是 Token、Embedding、Attention、Transformer，结果很快迷失方向。因此第一课的目标只有一个：**建立AI知识地图**。

## 二、AI的发展历史

```text
人工智能（AI）
├── 机器学习（ML）
│   ├── 传统机器学习
│   └── 深度学习（DL）
│       ├── CNN
│       ├── RNN
│       └── Transformer
│           ├── BERT
│           ├── GPT
│           ├── Llama
│           ├── Qwen
│           └── DeepSeek
```

GPT只是AI体系中的一个分支，而不是AI本身。

## 三、什么是AI？

AI（Artificial Intelligence）是让计算机表现出类似人类智能的一门学科，包括视觉、语音、自然语言、决策等众多方向。

## 四、机器学习

传统编程：

```python
if score > 60:
    print("合格")
```

机器学习：

> 数据 + 正确答案 → 学出规则 → 用规则预测新数据。

## 五、深度学习

深度学习是机器学习的重要分支，通过多层神经网络自动学习复杂特征，目前几乎所有大模型都属于深度学习。

## 六、神经网络

神经网络来源于生物神经元模型：

输入 → 加权 → 激活 → 输出。

大量神经元连接后形成多层神经网络。

## 七、为什么RNN失败？

RNN按顺序处理文本，难以记住长距离依赖，因此在长文本任务中表现受限。

## 八、Transformer诞生

2017年Google发表《Attention Is All You Need》，提出Transformer架构，可并行处理整个句子，大幅提升训练效率和效果。

## 九、GPT为什么成功？

GPT（Generative Pre-trained Transformer）结合Transformer架构、海量数据和大规模参数训练，遵循Scaling Law，使模型能力持续提升。

## 十、什么是LLM？

LLM（Large Language Model）具备：

1. 海量参数；
2. 海量文本预训练；
3. 核心任务：预测下一个Token（Next Token Prediction）。

## 十一、ChatGPT的位置

```text
AI
└── ML
    └── DL
        └── Transformer
            └── GPT
                └── ChatGPT（产品）
```

ChatGPT是建立在GPT模型之上的聊天产品，而不仅仅是模型。

## 实践

1. 调研5个主流LLM（GPT、Llama、Qwen、DeepSeek、Gemma）。
2. 绘制AI知识树。

## 推荐资料

- 李宏毅《生成式AI导论》
- 3Blue1Brown《神经网络》
- Build a Large Language Model (From Scratch)
- The Illustrated Transformer

## 总结

LLM本质上是基于Transformer架构的大规模神经网络，其核心任务始终是预测下一个Token。
