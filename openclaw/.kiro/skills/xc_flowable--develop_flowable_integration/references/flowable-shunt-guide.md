# @flowable_shunt 多版本路由指南

> 源码位置：`xc_addons/xc_common/flowable_shunt.py`

## 适用场景

当流程图升级（如审批节点变更）但旧流程实例仍在运行时，需要多版本并存。
通过 `@flowable_shunt` 装饰器实现按流程定义版本自动路由方法调用。

## 工作原理

1. `bpmn.process.def` 绑定到业务模型（`ir.model`），每个版本有唯一的 `p_def_id`
2. `ir.config_parameter` 中存储版本类名到 `p_def_id` 的映射
3. `@flowable_shunt` 装饰器在运行时检查当前流程实例的 `p_def_id`，
   匹配到对应版本类的方法并执行
4. 如果没有匹配到特定版本，回退到 V1 默认实现

### 路由逻辑（伪代码）

```python
def flowable_shunt(func):
    def wrapper(self, *args, **kwargs):
        # 1. 遍历当前模型的所有父类
        for parent_class in self.__class__.__bases__:
            # 2. 用父类的类名去 ir.config_parameter 查找对应的 p_def_id
            p_def_id_v = ir_config_parameter.get(parent_class.__name__)
            # 3. 如果匹配当前流程实例的 p_def_id，执行该版本的方法
            if p_def_id_v == self.p_def_id.p_def_id:
                return parent_class.func(self, *args, **kwargs)
        # 4. 没有匹配到，回退到 V1 默认实现
        return V1Class.func(self, *args, **kwargs)
```

## 版本类命名规范

版本类名 = 模型 `_name` 各段首字母大写拼接 + 版本标识

| _name | V1 默认类名 | 新版本类名示例 |
|-------|------------|---------------|
| `xc.borrow.flowable` | `XcBorrowFlowableV1` | `XcBorrowFlowable251121` |
| `xc.sn.flowable` | `XcSnFlowableV1` | `XcSnFlowableV2` |

新版本类名可以用日期（如 `251121`）或版本号（如 `V2`），只要在 `ir.config_parameter` 中正确映射即可。

## 创建新版本

```python
# xc_sn_flowable_v2.py
from odoo import models
from xc_addons.xc_common.flowable_shunt import flowable_shunt


class XcSnFlowableV2(models.Model):
    _inherit = ['xc.sn.flowable']  # 继承 V1 模型，不创建新 _name

    @flowable_shunt
    def get_flowable_button(self, business_no):
        """V2 版本的按钮逻辑"""
        buttons = []
        # ... V2 特有的按钮逻辑
        return buttons

    @flowable_shunt
    def action_param(self):
        """V2 版本的流程参数"""
        var = super().action_param()
        # ... V2 特有的参数
        return var

    @flowable_shunt
    def do_after(self, kwargs=None):
        """V2 版本的后处理"""
        return super().do_after(kwargs)
```

## 版本配置

在系统参数（设置 > 技术 > 参数 > 系统参数）中手动添加版本映射记录：

| key（类名） | value（p_def_id） |
|---|---|
| `XcBorrowFlowable251107` | `borrow_flowable_050303:1:9cefe362-fa71-11ef-b237-0242ac110002` |
| `XcBorrowFlowable251121` | `bcm_borrow_flowable:3:0526d26b-c91d-11f0-b237-0242ac110002` |

## 注意事项

- 只有需要变更的方法才加 `@flowable_shunt`，未变更的方法自动继承 V1
- 新版本类必须 `_inherit` V1 模型，不能创建新的 `_name`
- 在 `models/__init__.py` 中导入新版本文件
- V1 中的方法如果也需要版本路由，也要加 `@flowable_shunt`
- 装饰器内部有防重入机制（`_is_flowable_shunt_calling`），避免递归调用

## 真实案例：xc_borrow 多版本

xc_borrow 模块有三个版本并存：

```
xc_borrow/models/
├── xc_borrow_flowable_v1.py       ← V1 默认版本
├── xc_borrow_flowable_251107.py   ← 2025-11-07 版本
└── xc_borrow_flowable_251121.py   ← 2025-11-21 版本
```

每个新版本只重写了需要变更的方法（`get_flowable_button`、`action_param`、`rollback_after`），
其余方法自动继承 V1 的实现。
