---
name: xc-app-knowledge
description: xc_app BCM 移动端 API 模块知识库。当开发涉及 BCM 移动端接口、App REST API 时，务必使用此技能。
---

# BCM 移动端（xc_app）

> BCM 系统的移动端接口模块，为移动应用提供后端 API 支持。

## 模块概述

xc_app 是 BCM 系统的移动端模块，通过 Controller 层为移动应用（App）提供后端 API 接口。模块结构轻量，仅包含 controllers 目录，不涉及独立的数据模型定义。

## 核心业务流程

移动端通过 API 接口访问系统业务数据，具体业务逻辑由其他模块承载。

## 数据模型

无独立数据模型，复用其他业务模块的模型。

## 主要功能模块

- **移动端 API**：为 BCM 移动应用提供数据接口

## 外部集成

无

## 系统术语

| 术语 | 说明 |
|------|------|
| BCM | Business Collaboration Management，即 D-BOMS 系统的另一个名称 |
