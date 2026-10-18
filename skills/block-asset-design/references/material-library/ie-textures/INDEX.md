# IE 素材目录（仅元数据）

版本 `1.21.1-12.4.2-194`；50 个稳定 ID、45 个原图来源、9 类，其中 5 个条目记录裁切矩形及模型路径／哈希证据。先读[来源与使用边界](NOTICE.md)；本目录未携带原图、裁切图或模型。

按下表的分类、ID 或中文名称检索，在 [catalog.json](catalog.json) 中读取 `tags`、`sources`、`rect`、`evidence` 和 `model_evidence`。`sources.*.path` 与模型路径都是原包内部路径；`rect` 为以左上角为原点的 `[x0,y0,x1,y1]`，不包含右下边界，`null` 表示整图。模型证据用于定位映射，完整依赖仍需从固定来源检查。

实际使用先读[素材用途与授权确认](../../../shared/references/material-permissions.md)，再按 [mod-resource-extract](../../../mod-resource-extract/SKILL.md) 核查许可并形成版本 1 提取清单；`catalog.json` 是检索目录，不能直接作为提取脚本的输入清单。固定 JAR 哈希见 [provenance.json](provenance.json)，原许可证见 [LICENSE.IE.txt](LICENSE.IE.txt)。

## power · 电力（9）

| 稳定 ID | 名称 |
| --- | --- |
| `capacitor_lv_side_in` | 低压电容器侧面／输入 |
| `capacitor_lv_side_out` | 低压电容器侧面／输出 |
| `capacitor_lv_side_none` | 低压电容器侧面／未配置 |
| `capacitor_mv_side_in` | 中压电容器侧面／输入 |
| `capacitor_mv_side_out` | 中压电容器侧面／输出 |
| `capacitor_mv_side_none` | 中压电容器侧面／未配置 |
| `capacitor_hv_side_in` | 高压电容器侧面／输入 |
| `capacitor_hv_side_out` | 高压电容器侧面／输出 |
| `capacitor_hv_side_none` | 高压电容器侧面／未配置 |

## fluid · 流体（11）

| 稳定 ID | 名称 |
| --- | --- |
| `fluid_pump_side_in` | 流体泵侧面／输入 |
| `barrel_top_in` | 金属桶顶面／输入 |
| `fluid_pump_side_out` | 流体泵侧面／输出 |
| `barrel_top_out` | 金属桶顶面／输出 |
| `fluid_pump_side_none` | 流体泵侧面／未配置 |
| `barrel_top_none` | 金属桶顶面／未配置 |
| `pipe_valve_connector` | 阀门连接面 |
| `pipe_valve_end` | 阀门端面 |
| `pipe_valve_side` | 阀门侧面 |
| `fluid_pipe` | 流体管道 UV 图集 |
| `hatch_front` | 舱门正面 |

## panels · 面板（4）

| 稳定 ID | 名称 |
| --- | --- |
| `sheetmetal_steel` | 钢板 |
| `sheetmetal_iron` | 铁板 |
| `sheetmetal_aluminum` | 铝板 |
| `sheetmetal_copper` | 铜板 |

## structure · 结构（7）

| 稳定 ID | 名称 |
| --- | --- |
| `light_engineering` | 轻型工程块 |
| `heavy_engineering` | 重型工程块 |
| `redstone_engineering` | 红石工程块 |
| `radiator` | 散热片 |
| `steel_scaffolding_top_standard` | 钢脚手架标准顶面 |
| `steel_scaffolding_top_grate_top` | 钢格栅顶面 |
| `aluminum_scaffolding_top_grate_top` | 铝格栅顶面 |

## connectors · 电线连接器（4）

| 稳定 ID | 名称 |
| --- | --- |
| `connector_lv` | 低压电线连接器 UV 图集 |
| `connector_mv` | 中压电线连接器 UV 图集 |
| `connector_hv` | 高压电线连接器 UV 图集 |
| `connector_redstone` | 红石连接器 UV 图集 |

## conveyor · 输送带（4）

| 稳定 ID | 名称 |
| --- | --- |
| `conveyor_running` | 运行输送带帧条 |
| `conveyor_stopped` | 静止输送带 |
| `conveyor_casing_side` | 输送带外壳侧面 |
| `conveyor_casing_top` | 输送带外壳顶面 |

## signs · 标识（5）

| 稳定 ID | 名称 |
| --- | --- |
| `icon_electric` | 电气危险标识 |
| `icon_hot` | 高温标识 |
| `icon_attention` | 注意标识 |
| `icon_arrow_left` | 左箭头 |
| `icon_arrow_right` | 右箭头 |

## reference · 参考图集（1）

| 稳定 ID | 名称 |
| --- | --- |
| `multiblock_components_atlas` | 多方块机器公共部件图集 |

## interfaces · 机器接口（5）

| 稳定 ID | 名称 |
| --- | --- |
| `machine_power_socket` | 机器电力插口／黑框橙芯 |
| `machine_red_indicator` | 红色指示灯方板 |
| `machine_orange_control` | 橙色指示与黑色槽口面板 |
| `machine_grille_panel` | 横向格栅面板 |
| `machine_grille_indicator` | 带橙色小槽的格栅面板 |
