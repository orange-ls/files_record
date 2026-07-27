# 开发规范

## 代码规范
- **基于 Odoo 14 CE 开发，遵循 Odoo 14 官方编码规范，灵活使用框架内置机制和方法避免重复造轮子（agent 应基于对 Odoo 开源项目的理解自行执行，无需额外说明）。**
- 代码注释使用中文，复杂业务逻辑处必须添加注释。
- 代码开发要考虑逻辑边界的处理，异常回滚，适当的错误处理和日志记录。
- 注重代码性能，遵循python语言的和odoo框架的性能最佳实践，model中关键业务字段灵活使用索引，数据库查询优化，寻找使用缓存的机会.
- 对代码进行合理的封装，灵活使用各种代码设计模式，公共方法抽取。
- 避免在循环中执行 SQL 或 ORM 查询，批量操作优先：`execute_values`、`executemany`
- 使用 `sudo()` 时必须注释说明原因

## 项目特有约定
- 自定义model名和module名统一使用 `xc`作为前缀，这里的`xc`是`信创`的拼音简写,如 `xc.sales.order`
- 没有明确说明时，所有系统删除功能默认使用逻辑删除，统一使用字段 `active = fields.Boolean(string='是否有效', default=True)`
- Controller API 返回统一使用 `xc_common` 的 `AjaxResult.success()` / `AjaxResult.error()` 封装,必须 `try-except` 并使用日志logging记录请求入参数和出参
- 项目通用工具类放在`xc_addons\xc_common`目录下，项目开发过程中读取`xc_addons\xc_common\README.md`文件, 利用合适的工具类进行开发
- 通用工具类自动归纳：在开发过程中，如果编写了具有通用复用价值的工具函数/类，将工具类代码放到 `xc_addons/xc_common/` 目录下（新建 `.py` 文件或追加到已有文件）：
  - 判断标准：该函数/类不依赖特定业务模块的上下文，可被多个模块复用
