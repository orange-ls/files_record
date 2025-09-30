```python
@http.route('/inventory/import', type='http', auth='user')
def inventory_import(self, upload_file):
    try:
        # 解析excel
        if upload_file.filename.split(".")[-1] not in ['xlsx']:
            return AjaxResult.error(msg=f'导入失败：文件格式错误').str()

        work_book = load_workbook(upload_file, data_only=True)
        sheet = work_book.worksheets[0]  # 获取第一个工作表

        # 获取表头
        headers = [cell.value for cell in sheet[1]]  # 假设表头在第一行

        # 获取模型字段中文标签
        model = request.env['inventory.query']
        field_labels = {model.fields_get()[field]['string']: field for field in model._fields.keys()}

        # 用于批量更新和创建的字典
        excel_records = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            val = {
                field_labels.get(header.strip()): cell
                for header, cell in zip(headers, row)
                if header.strip() in field_labels
            }
            material_code = val.get('material_code').strip() if val.get('material_code') else None
            apply_factory = val.get('apply_factory').strip() if val.get('apply_factory') else None
            apply_location = val.get('apply_location').strip() if val.get('apply_location') else None
            if apply_factory and apply_location:
                import_flag = 1
            else:
                import_flag = None
            vals = {
                'material_code': material_code,
                'apply_num': val.get('apply_num') if val.get('apply_num') else 0,
                'apply_factory': apply_factory,
                'apply_location': apply_location,
                'import_flag': import_flag,
            }
            excel_records.append(vals)
        if excel_records:
            seen = {}
            for rec in excel_records:
                code = rec['material_code']
                if code not in seen:
                    seen[code] = rec
            # 更新为去重后的列表
            excel_records = list(seen.values())
            update_sql = '''
            insert into inventory_query(material_code,apply_num,apply_factory,apply_location,import_flag) values %s on conflict (material_code) do update set apply_num=EXCLUDED.apply_num,apply_factory=EXCLUDED.apply_factory,apply_location=EXCLUDED.apply_location,import_flag=EXCLUDED.import_flag
            '''
            execute_values(request._cr, update_sql, [tuple(record.values()) for record in excel_records])
            request._cr.commit()
        return AjaxResult.success(msg='导入成功').str()
    except Exception as e:
        logging.error('导入失败：原因：%s' % (str(e),))
        request.env.cr.rollback()
        return AjaxResult.error(msg='导入失败').str()
```

