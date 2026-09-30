-- =============================================================================
-- xc_quotwise 已下线模型：遗留元数据清理 + 物理表删除（一次性运维脚本）
--
-- 适用症状：升级 xc_quotwise 报
--   KeyError: 'xc.quotwise.product.draft'
--   ... ir_model.py ... _process_end -> record.unlink -> _process_ondelete
--
-- 原因：静态 Selection 字段在安装时会被反射成 ir_model_fields_selection 记录并带 xmlid
--   （如 xc_quotwise.selection__xc_quotwise_product_draft__state__draft）。
--   模型从代码删除后，升级时 ir.model.data._process_end 认定这些旧 xmlid 已不在模块数据里，
--   于是 record.unlink() 回收它们；而 ir.model.fields.selection.unlink 会先执行
--   _process_ondelete()，第一行就是 self.env[selection.field_id.model]，模型已不在注册表 -> KeyError，
--   整个升级事务回滚。所以必须在升级之前把选择项记录清掉。
--
-- 执行前提：数据库备份（后面会 DROP 表，不可逆）
-- 执行方式：整体执行本文件，执行完再回 Odoo 点“升级 xc_quotwise”
-- 幂等性：可重复执行
-- =============================================================================

-- 若上一轮执行被中断或报错，会话还停在 aborted 事务里（再次执行会报
-- “current transaction is aborted, commands ignored until end of transaction block”），
-- 这里无条件回滚一次清空状态：不在事务中时仅产生 WARNING，不会影响数据
ROLLBACK;

-- DROP TABLE 需要排他锁，若还有其它会话（常见：上一次被中断但未断开的连接、Odoo 里的长事务）
-- 持有这些表/子表的锁，DROP 会无限等待；这里设 10 秒超时，遇到锁冲突直接报错回滚，不硬卡
SET lock_timeout = '10s';

BEGIN;

-- 已下线模型清单（代码中已无定义，全仓 grep 无引用）；后续再下线模型时在此追加
DROP TABLE IF EXISTS retired_model;
CREATE TEMP TABLE retired_model (model text PRIMARY KEY);
INSERT INTO retired_model (model) VALUES
    ('xc.quotwise.product.draft'),            -- 方案草稿（state 静态选项，即报错的那个）
    ('xc.quotwise.product.profile'),          -- 已投产产品配置画像
    ('xc.quotwise.product.profile.detail'),   -- 画像明细
    ('xc.quotwise.requirement'),              -- 需求与方案映射
    ('xc.quotwise.category.spec.attribute');  -- 更早下线的二级分类规格属性映射

-- ---------------------------------------------------------------------------
-- 0. 执行前核对：看清将被清理的范围（只读）
-- ---------------------------------------------------------------------------
SELECT f.model, f.name AS field_name, count(s.id) AS selection_rows
FROM ir_model_fields f
LEFT JOIN ir_model_fields_selection s ON s.field_id = f.id
WHERE f.model IN (SELECT model FROM retired_model)
GROUP BY f.model, f.name
ORDER BY f.model, f.name;

-- ---------------------------------------------------------------------------
-- 1. 选择项残留（必须先删，否则升级抛 KeyError）
-- ---------------------------------------------------------------------------
DELETE FROM ir_model_data d
USING ir_model_fields_selection s, ir_model_fields f, retired_model r
WHERE d.model = 'ir.model.fields.selection' AND d.res_id = s.id
  AND s.field_id = f.id AND f.model = r.model;

DELETE FROM ir_model_fields_selection s
USING ir_model_fields f, retired_model r
WHERE s.field_id = f.id AND f.model = r.model;

-- ---------------------------------------------------------------------------
-- 2. 旧定时任务及其服务动作（必须在删 ir_model 之前）
--    product_profile_cron.xml 是 noupdate=1，_process_end 不会回收该 xmlid；
--    其 ir_act_server.model_id 指向已下线模型，而 ir_cron.ir_actions_server_id 是
--    ondelete='restrict'，若不先删 cron，删 ir_model 时的级联会被 FK 拦住报错。
-- ---------------------------------------------------------------------------
DELETE FROM ir_model_data d
USING ir_cron c, ir_act_server s, ir_model m, retired_model r
WHERE d.model = 'ir.cron' AND d.res_id = c.id
  AND c.ir_actions_server_id = s.id AND s.model_id = m.id AND m.model = r.model;

DELETE FROM ir_cron c
USING ir_act_server s, ir_model m, retired_model r
WHERE c.ir_actions_server_id = s.id AND s.model_id = m.id AND m.model = r.model;

-- 自动化规则对 server action 也是 ondelete='restrict'（该表可能未安装，做存在性判断）
DO $$
BEGIN
    IF to_regclass('base_automation') IS NOT NULL THEN
        DELETE FROM base_automation ba
        USING ir_act_server s, ir_model m, retired_model r
        WHERE ba.action_server_id = s.id AND s.model_id = m.id AND m.model = r.model;
    END IF;
END $$;

DELETE FROM ir_act_server s
USING ir_model m, retired_model r
WHERE s.model_id = m.id AND m.model = r.model;

-- ---------------------------------------------------------------------------
-- 3. 物理表（不可逆：表内历史方案草稿/产品画像/需求匹配数据一并丢失）
--    放在删元数据之前，是因为 M2M 关联表名只记录在 ir_model_fields/ir_model_relation 里
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS xc_quotwise_product_draft CASCADE;
DROP TABLE IF EXISTS xc_quotwise_product_profile CASCADE;
DROP TABLE IF EXISTS xc_quotwise_product_profile_detail CASCADE;
DROP TABLE IF EXISTS xc_quotwise_requirement CASCADE;
DROP TABLE IF EXISTS xc_quotwise_category_spec_attribute CASCADE;

-- M2M 关联表：仅删不再被其它字段/模型登记引用的，避免误删仍在用的表
DO $$
DECLARE rel_table text;
BEGIN
    FOR rel_table IN
        SELECT f.relation_table
        FROM ir_model_fields f
        JOIN retired_model r ON r.model = f.model
        WHERE f.relation_table IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM ir_model_fields o
              WHERE o.relation_table = f.relation_table
                AND o.model NOT IN (SELECT model FROM retired_model))
        UNION
        SELECT rel.name
        FROM ir_model_relation rel
        JOIN ir_model m ON m.id = rel.model
        JOIN retired_model r ON r.model = m.model
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', rel_table);
    END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- 4. 其余元数据（字段、约束、关联登记、ACL、记录规则、模型本身及其 xmlid）
--    注：ir_model_constraint.model / ir_model_relation.model 存的是 ir_model.id，需经 ir_model 关联
-- ---------------------------------------------------------------------------
DELETE FROM ir_model_data d
USING ir_model_fields f, retired_model r
WHERE d.model = 'ir.model.fields' AND d.res_id = f.id AND f.model = r.model;

-- 其它模型上指向已下线模型的字段行（M2o/O2m 的 relation 指向），代码中已不存在
DELETE FROM ir_model_data d
USING ir_model_fields f, retired_model r
WHERE d.model = 'ir.model.fields' AND d.res_id = f.id AND f.relation = r.model;

DELETE FROM ir_model_fields f USING retired_model r WHERE f.model = r.model;
DELETE FROM ir_model_fields f
WHERE f.relation IN (SELECT model FROM retired_model)
  AND f.model NOT IN (SELECT model FROM retired_model);

DELETE FROM ir_model_data d
USING ir_model_constraint c, ir_model m, retired_model r
WHERE d.model = 'ir.model.constraint' AND d.res_id = c.id AND c.model = m.id AND m.model = r.model;
DELETE FROM ir_model_constraint c USING ir_model m, retired_model r
WHERE c.model = m.id AND m.model = r.model;

DELETE FROM ir_model_data d
USING ir_model_relation rel, ir_model m, retired_model r
WHERE d.model = 'ir.model.relation' AND d.res_id = rel.id AND rel.model = m.id AND m.model = r.model;
DELETE FROM ir_model_relation rel USING ir_model m, retired_model r
WHERE rel.model = m.id AND m.model = r.model;

DELETE FROM ir_model_data d
USING ir_model_access a, ir_model m, retired_model r
WHERE d.model = 'ir.model.access' AND d.res_id = a.id AND a.model_id = m.id AND m.model = r.model;
DELETE FROM ir_model_access a USING ir_model m, retired_model r
WHERE a.model_id = m.id AND m.model = r.model;

DELETE FROM ir_model_data d
USING ir_rule ru, ir_model m, retired_model r
WHERE d.model = 'ir.rule' AND d.res_id = ru.id AND ru.model_id = m.id AND m.model = r.model;
DELETE FROM ir_rule ru USING ir_model m, retired_model r
WHERE ru.model_id = m.id AND m.model = r.model;

DELETE FROM ir_model_data d
USING ir_model m, retired_model r
WHERE d.model = 'ir.model' AND d.res_id = m.id AND m.model = r.model;
DELETE FROM ir_model m USING retired_model r WHERE m.model = r.model;

-- 已下线模型自身的业务数据记录 xmlid（表已删，xmlid 一并清掉）
DELETE FROM ir_model_data d WHERE d.model IN (SELECT model FROM retired_model);

-- ---------------------------------------------------------------------------
-- 5. 翻译残留（name 形如 '<model>,<field>'）
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('ir_translation') IS NOT NULL THEN
        DELETE FROM ir_translation t
        WHERE EXISTS (SELECT 1 FROM retired_model r WHERE t.name LIKE r.model || ',%');
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 6. 执行后复核：以下三个查询都应返回 0 行 / 0 值
-- ---------------------------------------------------------------------------
SELECT (SELECT count(*) FROM ir_model WHERE model IN (SELECT model FROM retired_model)) AS left_models,
       (SELECT count(*) FROM ir_model_fields WHERE model IN (SELECT model FROM retired_model)) AS left_fields,
       (SELECT count(*) FROM ir_model_fields_selection s
        JOIN ir_model_fields f ON f.id = s.field_id
        WHERE f.model IN (SELECT model FROM retired_model)) AS left_selections;

SELECT tablename FROM pg_tables
WHERE tablename IN ('xc_quotwise_product_draft', 'xc_quotwise_product_profile',
                    'xc_quotwise_product_profile_detail', 'xc_quotwise_requirement',
                    'xc_quotwise_category_spec_attribute');

COMMIT;

-- 执行完成后回到 Odoo 点“升级 xc_quotwise”：
-- 模块自带的其余旧 xmlid（如已删除的 ACL 行）会由 ir.model.data._process_end 自行回收，无需人工处理。
