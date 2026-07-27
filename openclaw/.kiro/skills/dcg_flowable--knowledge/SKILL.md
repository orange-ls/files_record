---
name: "module_dcg_flowable"
description: "dcg_flowable BPMN工作流管理模块知识库，包含流程定义、流程实例、审批任务、任务历史、审批Mixin的数据模型和业务流程。当开发涉及 dcg_flowable 模块、工作流、审批流程、BPMN、flowable、bpmn.process.def、bpmn.task、BpmnAuditMixin、流程定义、流程实例、审批任务、任务转办、任务委托、抄送加签、action_submit、action_approve、action_reject 时，务必使用此技能。即使用户只是提到审批、工作流集成、流程审批相关的开发需求，也应该触发此技能。"
---

# BPMN工作流管理（dcg_flowable）

> Odoo 内置的 BPMN 工作流引擎，提供流程定义、实例管理、审批任务处理和业务模型审批集成能力。

## 模块概述

dcg_flowable 是信创系统的平台服务层核心模块，为所有需要审批流程的业务模块提供统一的工作流能力。模块基于 BPMN 2.0 标准，支持可视化流程设计、流程部署、实例管理和任务处理。

模块的核心设计是 `BpmnAuditMixin`（审批混入类），业务模块只需继承该 Mixin 即可获得完整的审批能力（提交、审批、驳回、转办、委托、抄送、加签等）。目前 quotation（报价系统）等多个业务模块通过继承此 Mixin 实现审批流程。

模块依赖 `base`、`base_setup`、`mail`，外部依赖 Python 库 `xmltodict` 用于解析 BPMN XML。

## 核心业务流程

1. 流程定义管理：上传/编辑 BPMN 流程文件 → 解析 XML 提取节点信息 → 绑定业务模型 → 创建任务节点规则
2. 流程发起：业务单据调用 `action_submit` → 绑定流程定义 → 创建流程实例 → 生成首个审批任务 → 发送通知（OA/邮件/Odoo消息）
3. 审批处理：审批人接收任务 → 审批通过(`action_approve`)/驳回(`action_reject`) → 流转到下一节点 → 直到流程结束
4. 特殊操作：转办(`action_transfer`) → 委托(`action_entrust`) → 抄送(`action_ccopy`) → 加签(`action_apostille`)
5. 流程监控：查看流程实例状态 → 查看任务历史 → 查看流程图

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `bpmn.process.def` | 流程定义表，存储 BPMN 流程文件、绑定业务模型 |
| `bpmn.process.instance` | 流程实例表，记录每次流程发起的实例信息 |
| `bpmn.task` | 审批任务表，当前待处理的审批任务 |
| `bpmn.task.history` | 任务历史表，已完成的审批任务记录 |
| `bpmn.task.node` | 任务节点表，流程中的各审批节点定义 |
| `bpmn.task.rule` | 任务规则表，节点的审批人分配规则 |
| `bpmn.execution` | 流程执行表，流程运行时的执行信息 |
| `bp.api.def` | API定义表，工作流相关的API配置 |
| `bp.base` | 基础类，工作流引擎的基础HTTP通信方法 |
| `bp.res.config.settings` | 配置设置表，工作流引擎连接配置 |
| `bp.res.groups` | 权限组扩展，工作流相关的权限组 |
| `mixin.bpmn.audit`（BpmnAuditMixin） | 审批混入类（AbstractModel），业务模块继承即获得审批能力 |
| `fs.res.config.settings` | Flowable服务配置 |

## 主要功能模块

- **流程设计**：BPMN 可视化编辑器（bpmn-js）、流程文件上传/解析、流程图预览
- **流程定义管理**：流程部署、版本管理、业务模型绑定（一个模型只能绑定一个流程）
- **流程实例管理**：实例创建、状态查询、实例终止
- **审批任务处理**：任务领取、审批/驳回、转办/委托、抄送/加签、批注评论
- **审批Mixin（BpmnAuditMixin）**：`action_submit`提交、`action_approve`审批、`action_reject`驳回、`action_transfer`转办、`action_entrust`委托、`action_ccopy`抄送、`action_apostille`加签、动态视图生成
- **消息通知**：OA消息推送、邮件通知、Odoo站内消息、飞书消息
- **向导工具**：流程同步向导、任务评论向导、任务转办向导、代码脚手架生成

## 外部集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Flowable BPM 引擎 | HTTP REST API | 流程定义部署、实例管理、任务操作（通过 bp.base 封装） |
| OA 系统 | HTTP API | 审批消息推送 |
| 邮件服务 | SMTP | 审批通知邮件发送 |
| 飞书 | HTTP API | 审批消息推送 |

## 系统术语

| 术语 | 说明 |
|------|------|
| 流程定义（Process Definition） | BPMN 流程模板，定义审批节点和流转规则 |
| 流程实例（Process Instance） | 一次具体的审批流程执行 |
| 审批任务（Task） | 分配给具体审批人的待办事项 |
| BpmnAuditMixin | 审批混入类，业务模型继承后自动获得审批能力 |
| assignee | 任务指派人，当前负责审批的用户 |
| candidateUser | 候选审批人，可以领取任务的用户 |
| candidateGroup | 候选审批组，组内成员可以领取任务 |
| 转办 | 将当前任务转交给其他人处理 |
| 委托 | 委托他人代为审批，审批后任务回到委托人 |
| 抄送 | 将审批信息发送给相关人员知晓 |
| 加签 | 在当前节点增加额外的审批人 |
