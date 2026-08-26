# 产品配置规格参考文档（Agent 用）

> 本文档是**纯语义翻译参考**：把用户口语说法/行业术语/英文缩写翻译成 specs 属性 key。
> **能配什么（分类 + 属性 key + 可选值）一律以 `specs` 接口**（`/api/ai/recommend/specs`，`recommend_api.py --action specs --mat-name {mat_name}`）**按机型实时返回为准**——本文件不再固化任何「可选值」，因为同一属性在不同机型可选值不同，静态值会误导。
> **用法**：先用本文件的「说明」列理解用户的话 → 映射到候选属性 key → 再用 `specs` 接口确认该 key 与该值在该机型真实存在 → 写入 specs。二者互补，接口是最终裁决。

> **🔴 CPU 归属取决机型（重点，结构化 CPU 需求前必读）**：
> CPU **不一定全部直接集成在主板里，也有独立 CPU 配件**（如海光 Hygon 平台），**具体视机型而定**，且不同机型承载 CPU 型号的分类也不同（可能在「主板」「整机」「典配主物料」之一，属性 key 也各异）。
> - **如何判定**：以 `specs` 接口返回为准——返回里有独立 `category="CPU"` 则该机型 CPU 独立；否则 CPU 规格散落在「主板」/「整机」/「典配主物料」等分类的 `cpu_*` 属性里。例如 R522 的「主板」分类**没有** `cpu_model`，CPU 型号落在「典配主物料」「整机」分类。
> - **拿不准时**：先调 `specs` 接口看该机型把 CPU 放在哪个分类、用哪个 key，不要凭记忆套用本文件示例。
> - 本文件同时保留「CPU」独立分类章节和各分类的 `cpu_*` 属性章节，正是为了覆盖不同机型，二者并存、按机型取舍。

---

## 一、二级分类 → product_profile 字段映射（56项）

> 结构化 specs 的分类 key 必须是下方"二级分类"之一（且该机型 `specs` 接口确实返回了它）。

| 二级分类 | product_profile 字段 | 常见用户需求 |
|---------|---------------------|------------|
| CPU | spec_cpu | CPU型号、核数、频率（⚠️仅独立CPU机型使用，嵌入式机型CPU归「主板」/「整机」/「典配主物料」） |
| GPU | spec_gpu | GPU型号、显存 |
| 内存 | spec_memory | 内存容量、代际(DDR4/DDR5)、频率 |
| 2.5寸硬盘 | spec_disk_2_5 | 硬盘容量、类型(SSD) |
| 3.5寸硬盘 | spec_disk_3_5 | 硬盘容量、类型(HDD) |
| M.2硬盘 | spec_m2_disk | M.2 SSD容量 |
| NVME SSD | spec_nvme_ssd | NVMe硬盘容量 |
| RAID卡 | spec_raid_card | RAID型号、缓存、端口数 |
| SAS HBA卡 | spec_sas_hba | HBA卡型号 |
| PCIe卡 | spec_pcie_card | PCIe卡型号、端口数 |
| RISER卡 | spec_riser_card | Riser卡槽数 |
| 灵活网卡 | spec_flexible_nic | 网卡端口数、速率 |
| 电源和电源线 | spec_power_supply_cable | 电源功率、数量 |
| 服务器机箱 | spec_server_chassis | 机箱规格(1U/2U)、盘位数 |
| 主板 | spec_motherboard | CPU型号、CPU核数、内存槽位 |
| 主板-基础板 | spec_motherboard_baseboard | 基础板型号 |
| 硬盘背板 | spec_disk_backplane | 背板盘位数、接口 |
| 硬盘托架套件 | spec_disk_tray_kit | 托架规格 |
| 滑轨和面板 | spec_rail_panel | 滑轨类型、机箱规格 |
| 风扇 | spec_fan | 风扇规格 |
| BMC BIOS | spec_bmc_bios | 固件组件 |
| 标签包装 | spec_label_packaging | - |
| 整机 | spec_complete_machine | 整机型号 |
| 典配主物料 | spec_standard_config_material | 产品型号 |
| 定制型号 | spec_custom_model | 定制型号 |
| 定制开发费 | spec_custom_development_fee | - |
| 客供部件 | spec_customer_supplied_part | - |
| 改制费 | spec_modification_fee | - |
| 组件 | spec_component | - |
| 结构件 | spec_structural_part | - |
| 备件 | spec_spare_part | - |
| 安装服务 | spec_installation_service | - |
| 专业服务 | spec_professional_service | - |
| 产品使能包 | spec_product_enablement_package | - |
| 产品授权 | spec_product_license | - |
| 光模块和线缆 | spec_optical_module_cable | 光模块速率、距离 |
| 其它 | spec_other | - |
| 昇腾边缘硬件 | spec_ascend_edge_hardware | 加速卡型号 |
| 显示器 | spec_monitor | 屏幕尺寸、分辨率 |
| 虚拟整机内存 | spec_virtual_machine_memory | 内存容量 |
| 超节点卡数档位 | spec_supernode_card_tier | - |
| 项目专用 | spec_project_specific | - |
| AI服务器基础服务 | spec_ai_server_basic_service | - |
| 散件基础服务 | spec_spare_part_basic_service | - |
| 鲲泰服务器基础服务 | spec_kuntai_server_basic_service | - |
| 鲲泰服务器基础服务续保 | spec_kuntai_server_basic_service_renewal | - |
| PC-台式机主机 | spec_pc_desktop_host | - |
| PC-台式机基础维保服务 | spec_pc_desktop_basic_warranty | - |
| PC-笔记本 | spec_pc_laptop | - |
| PC-笔记本基础维保服务 | spec_pc_laptop_basic_warranty | - |
| PC-硬盘 | spec_pc_disk | - |
| PC-光驱 | spec_pc_optical_drive | - |
| PC-包材 | spec_pc_packaging | - |
| PC-固件 | spec_pc_firmware | - |
| PC-操作系统 | spec_pc_os | - |
| PC-键鼠 | spec_pc_keyboard_mouse | - |

---

## 二、各分类属性说明（口语说法 → 属性 key 翻译参考）

> 表格两列：**说明**（含用户口语说法、英文缩写与行业术语同义词，用于把用户表述精准匹配到属性 key）+ **属性 key**。
> **可选值一律查 `specs` 接口**，本文件不再列出（同一属性在不同机型可选值不同，静态值会误导）。
> 匹配时以属性 key 为准，说明仅辅助识别。

### 服务器机箱（spec_server_chassis）
| 说明 | 属性 key |
|------|---------|
| 机箱规格/形态；机架式高度单位 U（1U≈44.45mm）；用户说法：2U机架、4U机箱、机箱高度、机架式、form factor | form_factor |
| CPU路数；插槽数 socket；单路/双路/四路；用户说法：单路、双路、2路、四路、几路CPU、几路服务器 | cpu_socket_count |
| 硬盘盘位数；可容纳硬盘数量（bay/slot）；用户说法：几个盘位、支持几块盘、硬盘槽位、盘位 | drive_bay_count |
| 硬盘尺寸；2.5寸即 SFF（Small Form Factor）、3.5寸即 LFF（Large Form Factor）；用户说法：小盘、大盘、2.5寸盘位 | drive_size |
| 硬盘接口组合；背板支持的硬盘协议；用户说法：支持NVMe、SAS盘、SATA盘、混合接口 | drive_interface |
| 背板模式；硬盘背板连线方式；直通即直连控制器（direct attach）、级联扩展即 expander 级联扩容；用户说法：直通、级联 | backplane_mode |

### 主板（spec_motherboard）
> **⚠️ 本分类的 `cpu_*` 属性仅在该机型 `specs` 接口返回「主板」分类带这些 key 时才使用**。多数机型 CPU 型号并不在「主板」分类（如 R522 的 CPU 型号在「典配主物料」「整机」）。结构化 CPU 需求前先看接口把 CPU 放在哪。
| 说明 | 属性 key |
|------|---------|
| 板卡型号；主板/系统板型号；用户说法：S920主板、S1620板卡、指定板型 | board_model |
| CPU数量；板载CPU颗数（socket 数）；用户说法：单路、双路、2颗CPU、双处理器 | cpu_count |
| 单颗CPU核数；每颗物理核心数（core per socket）；用户说法：32核、单颗64核、每颗多少核；总核数 = 颗数 × 单颗核数 | cpu_cores_per_socket |
| CPU主频；基础频率（base clock）；用户说法：2.6GHz、主频、频率 | cpu_frequency |
| DIMM槽位数；内存插槽数量；用户说法：内存槽位、支持几条内存、DIMM slot | dimm_slots |

### CPU（spec_cpu）
> **⚠️ 本章节仅用于 `specs` 接口返回独立 `category="CPU"` 的机型**（如海光 Hygon）。多数机型无独立 CPU 分类，CPU 需求写入「主板」/「整机」/「典配主物料」等分类的 `cpu_*` 属性，**不要**套用本章节。
| 说明 | 属性 key |
|------|---------|
| CPU型号；处理器具体型号；用户说法：海光CPU、Hygon 7360 | model |
| CPU核数；物理核心数（core）；用户说法：24核、核心数、几核 | cores |
| CPU主频；基础频率（base frequency）；用户说法：2.0GHz、主频 | frequency |

### GPU（spec_gpu）
| 说明 | 属性 key |
|------|---------|
| 部件类型；GPU 相关物料形态（显卡/加速卡/线缆等） | component_type |
| GPU型号；显卡/AI加速卡型号；用户说法：910B、GPU卡、N卡 | model |
| 显存容量；视频内存 VRAM；用户说法：32G显存、显存多大 | memory |
| 功耗；最大热设计功耗 TDP；用户说法：300W的卡、功耗 | power |
| PCIe代际；总线版本（Gen3/Gen4/Gen5）；用户说法：PCIe4、4.0的卡 | pcie_generation |
| PCIe通道数；总线宽度 lane（x8/x16）；用户说法：x16、全高全宽 | pcie_lanes |
| 端口数量；外部接口个数；用户说法：几个口、双口 | port_count |
| 单端口速率；每个端口的带宽；用户说法：100G口、单口速率 | per_port_speed |
| 接口；物理接口/连接器形态；用户说法：QSFP口、什么接口 | connector |

### 内存（spec_memory）
| 说明 | 属性 key |
|------|---------|
| 容量；单条内存容量；用户说法：32G内存、64GB一条、内存多大 | capacity |
| 频率；内存时钟频率/传输速率；用户说法：3200MHz、DDR4-3200、3200、频率 | frequency |
| 内存代际；DDR 世代；用户说法：DDR4、四代条、DDR5 | memory_type |
| DIMM类型；寄存器/缓冲类型；RDIMM=带寄存器的双列直插内存；用户说法：REG内存、RDIMM | dimm_type |
| 内存Rank；内存条 rank 位宽结构（Rx4/Rx8 为位宽组织）；用户说法：1Rx4、双rank、2Rx8 | rank |
| 是否支持ECC；ECC 内存可检测并纠正内存位错误；用户说法：ECC内存、带校验内存 | ecc |
| 颜色；内存条外观颜色（含散热马甲颜色） | color |
| 密度类型；颗粒密度规格；用户说法：高密内存 | density_type |
| 部件类型；内存相关物料形态（内存条/内存挡条等） | component_type |

### 2.5寸硬盘（spec_disk_2_5）
| 说明 | 属性 key |
|------|---------|
| 容量；单盘存储容量；用户说法：1.92T盘、480G SSD、多大容量 | capacity |
| 硬盘类型；SSD 固态硬盘 / HDD 机械硬盘；用户说法：固态、机械盘、SSD | drive_type |
| 协议/接口；盘接口协议；SAS 多为企业级高速串行、SATA 为通用串行；用户说法：SAS盘、NVMe盘、接口 | interface |
| 规格/形态；2.5寸即 SFF 小尺寸盘规格；用户说法：小盘、2.5英寸 | form_factor |
| 硬盘尺寸；盘体物理尺寸；用户说法：2寸半的盘 | drive_size |
| PCIe代际；NVMe 盘所用 PCIe 总线世代；用户说法：PCIe4的盘、pcie4 | pcie_generation |
| 部件类型；2.5寸硬盘相关物料形态（盘体/托架等） | component_type |
| 是否为占位件；dummy 假盘/填充件，用于占位配平、不可存储；用户说法：假盘、占位盘、填充件 | is_dummy |
| 尺寸转换；盘框转换件；3.5寸_to_2.5寸表示3.5寸盘位装2.5寸盘的转接支架；用户说法：转换支架、转接框 | conversion |

### 3.5寸硬盘（spec_disk_3_5）
| 说明 | 属性 key |
|------|---------|
| 容量；单盘存储容量；用户说法：4T盘、10TB硬盘 | capacity |
| 硬盘类型；3.5寸盘多为 HDD 机械硬盘；用户说法：机械盘、大盘 | drive_type |
| 协议/接口；盘接口协议；用户说法：SAS盘、SATA盘 | interface |
| 硬盘尺寸；3.5寸即 LFF 大尺寸盘规格；用户说法：大盘、3寸半盘 | drive_size |
| 部件类型；3.5寸硬盘相关物料形态（盘体/托架等） | component_type |
| 是否为占位件；dummy 假盘/填充件，占位配平用；用户说法：假盘、占位件 | is_dummy |
| 尺寸转换；盘框转换件；2.5寸_to_3.5寸表示2.5寸盘位装3.5寸盘的转接支架；用户说法：转接支架 | conversion |

### NVME SSD（spec_nvme_ssd）
| 说明 | 属性 key |
|------|---------|
| 容量；NVMe SSD 单盘容量；用户说法：3.84T NVMe、1.6T盘 | capacity |
| 硬盘类型；NVMe SSD 均为固态硬盘；用户说法：固态、SSD | drive_type |
| 协议/接口；NVMe = Non-Volatile Memory Express，基于 PCIe 总线的高速存储协议；用户说法：NVMe盘、走PCIe的盘 | interface |
| 规格/形态；U.2 形态 2.5寸 NVMe 盘；用户说法：U.2、2.5寸NVMe | form_factor |
| PCIe代际；NVMe 盘所用 PCIe 总线世代（Gen3/Gen4/Gen5）；用户说法：pcie4、PCIe5.0的盘 | pcie_generation |

### RAID卡（spec_raid_card）
| 说明 | 属性 key |
|------|---------|
| 控制器型号；RAID 控制器具体型号；用户说法：9460-8i阵列卡、LSI卡、阵列卡型号 | controller_model |
| 型号；RAID 卡系列型号（不含端口后缀的系列名）；用户说法：SP686C | model |
| 缓存容量；阵列卡板载 cache 大小（常配超级电容做掉电保护）；用户说法：带2G缓存、cache | cache |
| 端口数量；内部 SAS 端口数（8i=8 内部端口）；用户说法：8口阵列卡、16i | port_count |
| 协议/接口；外部/内部线缆连接器标准；Mini SAS HD = SFF-8643 高密度接口；用户说法：Mini SAS接口 | interface |
| PCIe通道数；板卡占用 PCIe lane 数；用户说法：x8的卡 | pcie_lanes |
| PCIe代际；板卡 PCIe 总线世代；用户说法：PCIe4阵列卡 | pcie_generation |
| 规格/形态；板卡物理尺寸；FHHL = Full Height Half Length（全高半长）；用户说法：半长卡、全高卡 | form_factor |
| 线缆分支数量；SAS 线缆一分几（fan-out/breakout）；用户说法：一分二线缆、2路分支线 | split_count |
| 线缆长度列表；SAS/背板线缆长度；用户说法：多长的线、0.8米线 | cable_lengths |
| 部件类型；RAID 相关物料形态（控制器卡/SAS线缆/超级电容 BBU）；用户说法：阵列卡、SAS线、电池 | component_type |
| 兼容控制器型号；配件（如超级电容/线缆）适配的控制器型号 | compatible_controller_models |

### 灵活网卡（spec_flexible_nic）
| 说明 | 属性 key |
|------|---------|
| 型号；网卡具体型号；用户说法：SF216D网卡、指定网卡型号 | model |
| 端口数量；网口个数；用户说法：双口网卡、4口、几口 | port_count |
| 单端口速率；单口带宽；用户说法：25G网卡、万兆、百G口、千兆、GE网卡、10GE网卡（GE=1Gbps千兆、10GE=10Gbps万兆、25GE=25Gbps、100GE=100Gbps） | per_port_speed |
| 接口；网口连接器形态；OCP3.0=OCP标准网卡、QSFP/SFP 为光口、RJ45 为电口；用户说法：光口、电口、OCP卡 | connector |
| 部件类型；网卡相关物料形态（网卡/线缆等） | component_type |
| 适配器位置；网卡插装的槽位编号；用户说法：1号位、插在2号位 | adapter_position |
| 板载内存容量；智能网卡/DPU 板载内存 | memory |
| 线缆长度列表；网卡配套线缆长度 | cable_lengths |
| 线缆A端形态；线缆A端接头形式（弯式/直式） | end_1 |
| 线缆B端形态；线缆B端接头形式 | end_2 |

### 电源和电源线（spec_power_supply_cable）
| 说明 | 属性 key |
|------|---------|
| 电源额定功率；PSU 额定输出功率；用户说法：1200W电源、电源多大功率 | power_rating |
| 电源类型；交流 AC / 直流 DC 供电；用户说法：直流电源、AC电源 | power_type |
| 电压；供电电压；220V为市电、-48V(336V类)为机房直流；用户说法：220V、12V | voltage |
| 电流；额定电流；用户说法：10A、16A | current |
| 接口/连接器；电源线连接器规格；C13/C14=IEC 60320 10A、C19/C20=16A；用户说法：C13线、C19插头 | connector |
| 线缆长度；电源线长度；用户说法：1.5米线、多长的电源线 | cable_length |
| 能效认证；电源转换效率认证；80PLUS Titanium=钛金级（最高档）；用户说法：钛金电源、白金电源 | efficiency_certification |

### RISER卡（spec_riser_card）
| 说明 | 属性 key |
|------|---------|
| 插槽数量；RISER 转接卡上的 PCIe 插槽个数；用户说法：几槽riser、双槽转接卡 | slot_count |
| 插槽布局；各插槽的通道宽度组合（x16/x8）；用户说法：一个x16一个x8、插槽组合 | slot_layout |
| PCIe通道数；RISER 卡的总线宽度 lane；用户说法：x16、x8的riser | pcie_lanes |
| 安装位置；RISER 卡插装的机箱槽位编号；用户说法：RISER1、IO1和IO2 | position |
| 部件类型；RISER 相关物料形态（转接卡/硬盘背板等） | component_type |
| PCIe代际；总线世代；用户说法：PCIe5的riser | pcie_generation |

### 主板-基础板（spec_motherboard_baseboard）
| 说明 | 属性 key |
|------|---------|
| 板卡型号；基础板/baseboard 具体型号；用户说法：S920X10基础板 | board_model |
| CPU型号；处理器型号/系列；用户说法：鲲鹏920、920X | cpu_model |
| CPU数量；板载CPU颗数（socket 数）；用户说法：双路、2颗CPU | cpu_count |
| 单颗CPU核数；每颗物理核心数；用户说法：32核、单颗64核；总核数 = 颗数 × 单颗核数 | cpu_cores_per_socket |
| CPU主频；基础频率（base clock）；用户说法：2.6GHz、主频 | cpu_frequency |
| DIMM槽位数；内存插槽数量；用户说法：内存槽位、DIMM slot | dimm_slots |
| BMC型号；基板管理控制器芯片型号；用户说法：Hi1711、带外管理芯片 | bmc_model |
| 部件类型；基础板相关物料形态（基础板/BMC插卡等） | component_type |

### 整机（spec_complete_machine）
| 说明 | 属性 key |
|------|---------|
| 产品型号；服务器整机型号；用户说法：R724整机、A989 | product_model |
| 规格/形态；机架式高度（U）；用户说法：4U整机、机箱高度 | form_factor |
| CPU数量；整机 CPU 颗数；用户说法：双路、2颗CPU、四路 | cpu_count |
| CPU型号；处理器型号；用户说法：7280Z、鲲鹏920整机 | cpu_model |
| 单颗CPU核数；每颗物理核心数；用户说法：64核、80核 | cpu_cores_per_socket |
| CPU主频；基础频率；用户说法：2.6GHz、主频 | cpu_frequency |
| 加速卡数量；AI 加速卡（如昇腾 NPU）张数；用户说法：8张910、几张加速卡 | accelerator_count |
| 加速卡型号；AI 加速卡/NPU 型号；用户说法：910B、昇腾910 | accelerator_model |
| HBM显存容量；加速卡高带宽内存（High Bandwidth Memory）总容量；用户说法：64G显存、HBM多大 | hbm_capacity |
| 内存条数量；整机内存条根数；用户说法：32条内存、插满内存 | memory_module_count |
| 内存条容量；单条内存容量；用户说法：每条32G、64G一条 | memory_module_capacity |
| 硬盘配置；盘位数量与接口组合；用户说法：4块NVMe、几个SATA几个NVMe | drive_layout |

### 典配主物料（spec_standard_config_material）
| 说明 | 属性 key |
|------|---------|
| 产品型号；标准配置整机产品型号；用户说法：R722、A222 | product_model |
| 规格/形态；机架式高度（U）；用户说法：2U、4U | form_factor |
| CPU数量；整机 CPU 颗数；用户说法：单路、双路、四路 | cpu_count |
| CPU型号；处理器型号；用户说法：7280Z、鲲鹏920 | cpu_model |
| 单颗CPU核数；每颗物理核心数；用户说法：32核、64核 | cpu_cores_per_socket |
| CPU主频；基础频率；用户说法：2.6GHz、主频 | cpu_frequency |
| 加速卡数量；AI 加速卡张数（超节点/整柜场景）；用户说法：32张910、48卡 | accelerator_count |
| 加速卡型号；AI 加速卡/NPU 型号；用户说法：910、昇腾 | accelerator_model |
| 内存条数量；整机内存条根数；用户说法：128条内存、插满 | memory_module_count |
| 内存条容量；单条内存容量；用户说法：64G一条 | memory_module_capacity |
| 硬盘配置；盘位数量与接口组合；用户说法：4块NVMe、5块SAS | drive_layout |

### PCIe卡（spec_pcie_card）
| 说明 | 属性 key |
|------|---------|
| 型号；PCIe 扩展卡具体型号；用户说法：MCX512A网卡、SP382卡 | model |
| 部件类型；PCIe 卡的功能类别；用户说法：网卡、接口卡、扩展卡（"接口卡"在本语境多指网络接口卡 NIC） | component_type |
| 端口数量；网口个数；用户说法：双口、4口卡 | port_count |
| 单端口速率；单口带宽；FC 卡可为 32Gbps/64Gbps（FC32/FC64）；用户说法：25G、双口25G、32G光纤卡、GE/10GE口（GE=1Gbps、10GE=10Gbps、25GE=25Gbps） | per_port_speed |
| 接口；端口连接器形态；SFP+/SFP28/QSFP 为光口、RJ45 为电口；用户说法：光口、电口 | connector |
| 板载内存容量；智能网卡/DPU 板载内存 | memory |
| 功耗；板卡最大功耗 TDP；用户说法：70W的卡、功耗 | power |
| PCIe通道数；板卡总线宽度 lane；用户说法：x16、x8的卡 | pcie_lanes |
| PCIe代际；总线世代；用户说法：PCIe4、3.0的卡 | pcie_generation |

### SAS HBA卡（spec_sas_hba）
| 说明 | 属性 key |
|------|---------|
| 控制器型号；HBA 控制器具体型号；用户说法：9500-16i、LSI HBA | controller_model |
| 部件类型；HBA 卡物料形态 | component_type |
| 端口数量；内部 SAS 端口数（16i=16 内部端口）；用户说法：16口HBA | port_count |
| 工作模式；直通/透传模式（IT mode，不做 RAID，硬盘直接透传给系统）；用户说法：直通卡、透传、HBA模式、IT模式 | mode |
| PCIe通道数；总线宽度 lane；用户说法：x8 | pcie_lanes |
| PCIe代际；总线世代；用户说法：PCIe4 | pcie_generation |

### BMC BIOS（spec_bmc_bios）
| 说明 | 属性 key |
|------|---------|
| BMC型号；基板管理控制器芯片型号（Baseboard Management Controller，带外管理）；用户说法：1711、Hi1711、带外管理芯片 | bmc_model |
| 固件组件；固件类型；BIOS=基本输入输出系统、BMC=带外管理固件、CPLD=复杂可编程逻辑器件；用户说法：升级BIOS、BMC固件、CPLD | firmware_components |

### 硬盘背板（spec_disk_backplane）
| 说明 | 属性 key |
|------|---------|
| 部件类型；背板物料形态 | component_type |
| 硬盘盘位数；背板可接硬盘数量；用户说法：12盘位背板、几盘位 | drive_bay_count |
| 硬盘尺寸；背板支持盘体尺寸；2.5寸即 SFF、3.5寸即 LFF；用户说法：小盘背板、大盘背板 | drive_size |
| 硬盘接口组合；背板支持的盘接口协议；用户说法：支持NVMe的背板、SAS背板 | drive_interface |
| 背板模式；直通即直连控制器、级联扩展即 expander 级联；用户说法：直通、级联 | backplane_mode |
| PCIe通道数；NVMe 背板上行 PCIe 通道宽度；用户说法：x8背板 | pcie_lanes |

### 硬盘托架套件（spec_disk_tray_kit）
| 说明 | 属性 key |
|------|---------|
| 部件类型；托架物料形态；硬盘托架 = drive caddy/carrier | component_type |
| 硬盘尺寸；托架适配盘体尺寸；2.5寸即 SFF、3.5寸即 LFF；用户说法：2.5寸托架、大盘托架 | drive_size |
| 是否为占位件；dummy 假盘托架/填充件，占位配平用；用户说法：假盘托架、占位托架、填充件 | is_dummy |
| 尺寸转换；托架尺寸转换方向；2.5寸_to_3.5寸表示托架将2.5寸盘装入3.5寸盘位，反之亦然；用户说法：转接托架 | conversion |

### 滑轨和面板（spec_rail_panel）
| 说明 | 属性 key |
|------|---------|
| 滑轨类型；机柜滑轨形式；滚珠滑轨可抽拉维护、静态滑轨固定支撑；用户说法：抽拉滑轨、固定滑轨、ball bearing rail | rail_type |
| 部件类型；滑轨面板类物料形态；用户说法：前面板、挡板 | component_type |
| 适配机箱规格；滑轨/面板兼容的机箱 U 数；用户说法：2U滑轨、适配4U机箱 | compatible_form_factor |

### 光模块和线缆（spec_optical_module_cable）
| 说明 | 属性 key |
|------|---------|
| 速率；光模块/线缆传输带宽；用户说法：25G光模块、100G模块、400G、10GE光模块、GE光模块（GE=1Gbps、10GE=10Gbps、25GE=25Gbps、100GE=100Gbps、400GE=400Gbps） | speed |
| 接口/连接器；模块封装/接口形态；SFP+/SFP28/QSFP28/QSFP56 为可插拔模块封装、MPO 为多芯并行接口；用户说法：SFP28模块、QSFP56 | connector |
| 光纤模式；单模 SMF 适合长距离、多模 MMF 适合短距离；用户说法：单模、多模、SMF、MMF | fiber_mode |
| 波长；光信号波长；850nm 多用于多模、1310nm 多用于单模；用户说法：850的模块、1310 | wavelength |
| 传输距离；光模块最大传输距离；用户说法：10公里、百米、传输多远 | distance |
| 线缆长度；光纤/铜缆物理长度；用户说法：10米光纤、3米线 | cable_length |
| 光纤连接器；线缆端头连接器类型；LC 为双芯小方头、MPO/MPO12/MPO16 为多芯并行连接器；用户说法：LC头、MPO12 | fiber_connector |

### 昇腾边缘硬件（spec_ascend_edge_hardware）
| 说明 | 属性 key |
|------|---------|
| 容量；边缘硬件显存/内存容量；用户说法：12G的边缘卡 | capacity |

### PC-硬盘（spec_pc_disk）
| 说明 | 属性 key |
|------|---------|
| 容量；PC 硬盘存储容量；用户说法：1T硬盘、1TB | capacity |
| 硬盘类型；HDD 机械硬盘 / SSD 固态硬盘；用户说法：机械盘 | drive_type |
| 协议/接口；盘接口协议；用户说法：SATA盘 | interface |
| 规格/形态；盘体尺寸；3.5寸即 LFF；用户说法：大盘 | form_factor |

### 显示器（spec_monitor）
| 说明 | 属性 key |
|------|---------|
| 屏幕尺寸；显示器面板对角线尺寸；用户说法：24寸显示器、23.8寸屏 | screen_size |

---

## 三、用户需求 → 结构化映射示例

> 以下为口语说法 → 属性 key 的**语义映射**示例；具体归入哪个分类、该机型是否有该属性/该值，**一律以 `specs` 接口返回为准**（如 R522 的 CPU 型号在「典配主物料」「整机」而非「主板」）。

| 用户说法 | 二级分类 | spec 属性 | 结构化结果 |
|---------|---------|----------|-----------|
| "内存128G" | 内存 | capacity | {"内存": {"capacity": "128GB"}} |
| "DDR4 32G内存" | 内存 | capacity, memory_type | {"内存": {"capacity": "32GB", "memory_type": "DDR4"}} |
| "4T硬盘" | 3.5寸硬盘 | capacity, drive_type | {"3.5寸硬盘": {"capacity": "4TB", "drive_type": "机械硬盘"}} |
| "鲲鹏920 CPU" | 主板/整机/典配主物料（视机型） | cpu_model | {"{该机型CPU所在分类}": {"cpu_model": "鲲鹏920"}} |
| "32核CPU" | 主板/整机/典配主物料（视机型） | cpu_cores_per_socket | {"{该机型CPU所在分类}": {"cpu_cores_per_socket": "32核"}} |
| "2颗CPU" | 主板/整机/典配主物料（视机型） | cpu_count | {"{该机型CPU所在分类}": {"cpu_count": "2颗"}} |
| "海光Hygon 7360"（独立CPU机型） | CPU | model | {"CPU": {"model": "Hygon 7360"}} |
| "不需要GPU" | GPU | (不出现) | specs 中不包含 GPU |
| "4口千兆网卡" | 灵活网卡 | port_count, per_port_speed | {"灵活网卡": {"port_count": "4口", "per_port_speed": "1Gbps"}} |
| "900W电源" | 电源和电源线 | power_rating | {"电源和电源线": {"power_rating": "900W"}} |
| "9460-8i RAID" | RAID卡 | controller_model | {"RAID卡": {"controller_model": "9460-8i"}} |
| "16盘位机箱" | 服务器机箱 | drive_bay_count | {"服务器机箱": {"drive_bay_count": "16盘位"}} |
| "2U机箱" | 服务器机箱 | form_factor | {"服务器机箱": {"form_factor": "2U"}} |
| "≥4*GE 接口卡"（4 个千兆网口） | 灵活网卡 | port_count, per_port_speed | {"灵活网卡": {"port_count": "4口", "per_port_speed": "1Gbps"}} |
| "≥4*10GE 接口卡"（4 个万兆网口） | 灵活网卡 | port_count, per_port_speed | {"灵活网卡": {"port_count": "4口", "per_port_speed": "10Gbps"}} |
| "10GE 光模块" | 光模块和线缆 | speed | {"光模块和线缆": {"speed": "10Gbps"}} |

> **GE/10GE 速率换算与"接口卡"语义（结构化网络/光模块需求前必读）**：
> - **速率换算**：用户常以 `GE`/`10GE`/`25GE`/`100GE` 表述网口速率，与 spec 值对应关系为 `GE=1Gbps`、`10GE=10Gbps`、`25GE=25Gbps`、`100GE=100Gbps`、`400GE=400Gbps`。结构化时统一映射到 `per_port_speed`（网卡）或 `speed`（光模块）的 Gbps 值；具体可用值以 `specs` 接口返回为准。
> - **"接口卡"= 网卡**：采购需求中的"接口卡"在本语境通常指**网络接口卡（NIC）**，结构化时归入「灵活网卡」（`spec_flexible_nic`）；若是插 PCIe 槽的独立网卡则归「PCIe卡」（`spec_pcie_card`，`component_type`="网卡"）。二者区别：灵活网卡多为 OCP 子卡形态、跟随机型走；PCIe 网卡为通用扩展卡。拿不准时优先归「灵活网卡」，并在清单标注 `[推理映射]`。
> - **数量表述 `N*M`**：形如 `4*GE`/`4*10GE` 中，`4` 是端口/模块**数量**、`GE`/`10GE` 是单口**速率**。结构化时数量写入 `port_count`（如"4口"），速率写入 `per_port_speed`/`speed`。
> - **网卡"同时配两种速率"的歧义**：当同一行需求要求"≥4*GE 且 ≥4*10GE"（两种不同速率的网卡）时，单个 `灵活网卡` key 只能承载一组规格，**无法在一个 key 下同时表达 1Gbps+10Gbps 两张卡**。这通常意味着两张独立卡（GE 卡行 + 10GE 卡行），但也可能是单张 4GE+4*10GE 复合卡。**处理方式**：agent 按最可能方案（默认拆为两张独立网卡行）归入 specs 并在清单"语义匹配"列标注 `[推理映射]`，**不阻塞派发**；用户后续可在左侧方案卡片调整为复合卡方案。不向用户征询澄清（与路由层 AGENTS.md「不澄清、直接派发」一致）。
> - **光模块数量走 quantity**：「光模块和线缆」分类**没有** `port_count`/数量属性，光模块个数（如"4 个 10G 模块"中的 4）体现在该物料行的 `quantity` 上，不写入 `specs`。

---

## 四、结构化需求 JSON 示例

> 以下为 R522 的结构示例，**实际 specs 的分类/属性/值必须以 `specs` 接口返回为准**（R522 的 CPU 型号在「典配主物料」「整机」而非「主板」）。

```json
{
  "mat_name": "R522",
  "quantity": 10,
  "specs": {
    "典配主物料": {
      "cpu_model": "鲲鹏920",
      "cpu_count": "2颗"
    },
    "内存": {
      "capacity": "32GB",
      "frequency": "2933MHz",
      "memory_type": "DDR4"
    },
    "3.5寸硬盘": {
      "capacity": "4TB",
      "drive_type": "机械硬盘",
      "interface": "SATA"
    },
    "RAID卡": {
      "controller_model": "9460-8i",
      "cache": "2GB"
    },
    "灵活网卡": {
      "port_count": "4口",
      "per_port_speed": "1Gbps"
    }
  },
  "business": {
    "customer": null,
    "customer_type": null
  },
  "preferences": {
    "budget": 50000
  }
}
```

**关键规则**：
1. `specs` 下的 key 必须是上方 56 个二级分类之一，且该机型 `specs` 接口确实返回了该分类
2. 每个分类下的属性 key 必须是该机型 `specs` 接口返回的属性，值从接口返回的 `values` 中取——**严禁凭记忆或猜测**，未收录的规格不写入（见 AGENTS.md §4.2 规则 9）
3. 用户未提及的分类**不出现**在 specs 中（不要填 null 占位）
4. `business` 和 `preferences` 不参与 hash 计算
5. hash = MD5(json.dumps(specs, sort_keys=True))，元素顺序不影响结果
6. **歧义/多解需求不阻塞派发**：当需求存在歧义、多解或无法用单一规格值表达时（如"≥4*GE 且 ≥4*10GE"既可拆两张独立网卡也可是一张复合卡；"接口卡"未指明是 OCP 灵活网卡还是 PCIe 独立网卡等），agent 按**最可能**的归属写入 specs 并在清单"语义匹配"列标注 `[推理映射]`，**不向用户征询澄清、不阻塞派发**；用户后续可在左侧方案卡片微调。与路由层 AGENTS.md「不澄清、直接派发」政策一致。
