  SELECT
      name AS "CRM工单号",
      create_time AS "报修时间",
      hjdh AS "换件单号",
      gdzt AS "工单状态",
      gzjwlh AS "报修物料代码",
      bjmc AS "备件大类",
      bjwlh AS "备件物料号",
      bjsn AS "备件SN",
      bjpjsj AS "备件派件时间",
      bjqssj AS "备件签收时间",
      pjfs AS "派件方式",
      sfcs AS "是否超时",
      pjfy AS "派件费用",
      bjckd AS "备件出库地",
      CASE exceptional_services
          WHEN '0' THEN '否'
          WHEN '1' THEN '是'
          ELSE exceptional_services
      END AS "例外服务",
      description AS "故障现象（客户报）",
      fhjlx AS "返回件类型",
      fhjwlh AS "返回件物料号",
      gzjsn AS "返回件sn",
      jjfhkd AS "旧件返回快递",
      jjsjsj AS "旧件收件时间",
      gzjjjcssj AS "故障件交接测试时间",
      gzxxsc AS "故障现象（实测）",
      csjl AS "测试结论",
      fcclwcsj AS "复测处理完成时间",
      gys AS "供应商",
      fckd AS "返厂快递",
      fcsj AS "返厂时间",
      tat AS "TAT",
      xfjfhkd AS "修复件返回快递",
      xfjsjsj AS "修复件收件时间",
      xfjwlh AS "修复件物料号",
      xfjsn AS "修复件SN",
      xfjrksj AS "修复件入库时间",
      CASE field_7v131__c
          WHEN 'fqR7y7774' THEN '交换产品'
          WHEN '2nqbGT8wc' THEN '无线产品'
          WHEN 'g0vu14dyO' THEN '增值产品'
          WHEN '1F7fCjy4W' THEN '实验室产品'
          WHEN '9j7W7ewao' THEN '云产品'
          WHEN '5rguxPdg3' THEN '服务器'
          WHEN 'nbsAYOeuT' THEN 'PC'
          WHEN 'GUf1QEdn1' THEN '鲲泰存储产品'
          ELSE field_7v131__c
      END AS "类别",
      "field_Ak0t8__c" AS "机型",
      "field_rV3o1__c" AS "SLA",
      field_131ea__c AS "服务开始时间",
      deliver_time AS "产品交付时间",
      "field_G59Xd__c" AS "整机SN",
      field_ga1xx__c AS "项目名称",
      "field_wWIl1__c" AS "CRM立项编号",
      field_7gu26__c AS "客户信息",
      fzr AS "负责人",
      jjfhdjr AS "旧件返回对接人",
      bz AS "备注",
      wxdh AS "维修单号",
      csdh AS "测试单号",
      fcdh AS "返厂单号",
      tszt AS "特殊状态",
      hand_method AS "处理方式",
      work_days AS "产品使用天数",
      stock_location AS "库存地是否符合",
      bundling_number AS "捆绑料号",
      bjxqdssj AS "备件需求送达时间",
      crm_fwsh AS "crm服务市",
      sfbjmz AS "是否备件命中",
      real_sfbjmz AS "真实是否命中",
      hit_remark AS "命中备注"
  FROM compute_product_report
  WHERE name in ()