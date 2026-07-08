# 第2课 Token

## 学习目标

学完本课，你应该能够理解：

- 什么是Token
- Token与汉字、英文、字符的区别
- 为什么LLM按Token工作
- 什么是上下文窗口
- Token为什么决定API费用
- 如何估算Token数量

## 一、什么是Token？

Token是模型处理文本的最小单位，不等于汉字，也不等于英文单词。

例如：

```text
我喜欢AI
```

可能被切分为：

```text
我 | 喜欢 | AI
```

英文：

```text
unbelievable
```

可能切分为：

```text
un | believ | able
```

## 二、为什么不用字符？

字符数量过多、语义利用率低，而Token兼顾词义与词表规模，因此训练效率更高。

## 三、Tokenizer的作用

Prompt首先经过Tokenizer切分为Token，再映射成整数ID送入模型。

流程：

```text
Prompt
   ↓
Tokenizer
   ↓
Token
   ↓
Token ID
   ↓
Embedding
```

## 四、上下文窗口（Context Window）

上下文窗口表示模型一次能够看到的最大Token数量，例如：

- 8K
- 32K
- 128K
- 200K
- 1M

超过窗口的内容通常无法参与当前推理。

## 五、为什么API按Token收费？

模型推理成本与Token数量近似线性相关，因此绝大多数LLM API均按输入Token和输出Token分别计费。

## 六、估算Token数量

经验值：

- 1个中文≈1~2 Token
- 1个英文单词≈1~2 Token
- 1000个汉字约1500~2000 Token（视Tokenizer而定）

实际应使用Tokenizer工具统计。

## 实践

1. 使用OpenAI Tokenizer统计不同文本Token数量。
2. 安装`tiktoken`：

```bash
pip install tiktoken
```

编写Python程序统计一段文本的Token数量。

## 推荐资料

- OpenAI Tokenizer
- tiktoken
- Hugging Face Tokenizers

## 总结

Token是LLM理解世界的基本单位。所有Prompt都会先经过Tokenizer切分为Token，再进入Embedding和Transformer，因此Token是理解大模型工作原理的第一块基石。
