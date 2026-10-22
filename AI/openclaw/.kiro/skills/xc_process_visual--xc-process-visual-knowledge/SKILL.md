---
name: xc-process-visual-knowledge
description: xc_process_visual 流程可视化模块知识库，包含基于 BPMN.js 的流程图渲染和任务节点状态标注。当开发涉及流程图可视化、BPMN.js 渲染、流程节点状态展示时，务必使用此技能。
---

# 信创流程可视化（xc_process_visual）

> 基于 BPMN.js 的流程定义可视化展示模块，用于查看流程图和任务节点状态。

## 模块概述

xc_process_visual 是流程可视化模块，依赖 xc_flowable 模块，使用 BPMN.js 渲染流程定义图，展示流程节点和任务状态。为用户提供直观的流程图查看能力。

## 核心业务流程

1. 选择流程定义 → 加载 BPMN XML → BPMN.js 渲染流程图 → 标注当前任务节点状态

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `process.visual` | 流程可视化主模型 |
| `process.visual.task` | 流程可视化任务节点 |

## 主要功能模块

- **流程图渲染**：基于 BPMN.js 的流程定义图形化展示
- **节点状态标注**：在流程图上标注各节点的审批状态

## 外部集成

无（数据来源于 xc_flowable 模块）

## 系统术语

| 术语 | 说明 |
|------|------|
| BPMN | Business Process Model and Notation，业务流程建模标记法 |
