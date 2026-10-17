# 语义驱动的像素贴图

流程：整理几何与语义 → Blender 展开及检查 → 导出已有 UV/几何/语义 → 绘制并打包 → 指定生产 UV 层写回 → 明确连接材质 → 实际审阅。

先按[文件位置约定](../../machine-design/shared/references/workflow.md#文件位置)确定目标项目，并按[脚本适配约定](../../machine-design/shared/references/workflow.md#脚本适配)准备调用。以下示例中的 `MD_TEXTURE_DIR` 是项目脚本副本中的 `texture/`，`MD_PROJECT_DIR` 是目标项目；替换为实际绝对路径后，可从任意目录运行。项目内路径优先沿用已有约定。

## 原生数据与导出

`md_edge_role` 为 EDGE INT，0 不描边、1 形体边、2 装配缝；`md_material_role` 为 FACE INT，对象字符串属性 `md_role_names` 存 JSON 映射，如 `{"0":"steel","1":"paint"}`。缺少面属性时可显式提供 `--default-role steel`，不是推断语义；缺少边属性表示不自动加结构线。UV seam 不转为边角色。

```sh
MD_TEXTURE_DIR="/path/to/project/tools/machine-design/texture"
MD_PROJECT_DIR="/path/to/project"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/machines/example/source.blend" --python-exit-code 1 --python "$MD_TEXTURE_DIR/blender_atlas.py" -- export --objects Body --uv-layer Source --source-size 512 512 --density 16 --default-role steel --output "$MD_PROJECT_DIR/build/machine-design/example/charts.json"
python3 "$MD_TEXTURE_DIR/paint_uv_atlas.py" --input "$MD_PROJECT_DIR/build/machine-design/example/charts.json" --config "$MD_PROJECT_DIR/assets/machines/example/materials.json" --output "$MD_PROJECT_DIR/assets/machines/example/atlas"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/machines/example/source.blend" --python-exit-code 1 --python "$MD_TEXTURE_DIR/blender_atlas.py" -- apply --input "$MD_PROJECT_DIR/build/machine-design/example/charts.json" --layout "$MD_PROJECT_DIR/assets/machines/example/atlas/pixel-atlas-layout.json" --target-layer Production --output "$MD_PROJECT_DIR/assets/machines/example/production.blend"
```

导出操作读取源网格，要求对象处于 Object Mode，并指定已有的源 UV 层。所选对象若有启用视口显示的修改器，或多个对象共用同一网格数据，脚本会拒绝导出；需先准备符合要求的导出源，脚本不会自动应用修改器或拆分共享数据。`--source-size` 给源 UV 所在二维画布的宽高，避免非方图比例被忽略。根据各表面奇异值检查保形和一致密度，`--density-tolerance` 默认 .05；超出时返回诊断，不能自动拉伸到一致。每个对象等比换算至指定密度，连续 UV 边组成岛。保留原 UV，不重新展开几何。

写回校验源几何、源 UV、对象变换、材质分区、边角色与输入哈希；资产已变则需重新导出。目标层必须不同于源层；已有目标需显式 `--replace-target`。始终保存到新的 `.blend`，不覆盖源文件。写回只写 UV，**不修改材质节点**：写回后还需在材质中指定生产 UV 层（示例中名为 Production），用该层坐标采样生成的图像，再检查显示效果。完成 UV 写回不等于完成贴图。

## 材质配方

命令行入口将 `details_filename` 及其描述文件中的 `source` 都解析为相对于 `materials.json` 的路径，而非相对于技能目录或描述文件目录。模型引用的图像应保留在项目中。

`materials.json` 最小示例：

```json
{"version":1,"materials":{"steel":{"procedural":{"preset":"plate","seed":7,"noise_strength":0.6}}},"atlas_filename":"pixel_atlas.png"}
```

自制中性色板 `plate/structure/machined/painted` 为可调整起点，不含第三方采样色板。配方可指定递增亮度的 RGB `palette`、正数 `palette_weights`、`direction: x|y`、uint32 `seed` 和 0–1 `noise_strength`。重复生成使用同一配方、坐标与种子，结果不因画布大小变化。此版本不接收旧外部校准算法标识，避免静默改变既有配方效果。

图集生成器接收版本 1 的 `charts`、`meshes`、`pixels_per_unit`、`padding_px`；每岛的面含原环索引、模型位置、法线、角色、像素坐标及原三角划分。默认最多 1024×1024 图集；太大时报错，不通过缩小 UV 改变密度。整数像素平移打包，薄面保守覆盖，按岛向外扩色。细于像素的不同表面可能共享像素，输出会列出未独立覆盖的微小面。

结构线按真实边角色绘制，每像素只叠一次。原图可通过配方 `details_filename` 指定来源图、哈希、密度和模型空间 stamp；完整字段参见生成器的 `stamp_sample`/`generate`。投影后需核验像素覆盖是否完整，不能仅确认有像素命中。基础 Blender 导出入口不自动提取 artwork/glass 的原图/透明逻辑：这些面应保留在单独受保护材质/对象中，由明确的适配器处理后再合成，不能把占位灰色当作保留成功。

## 独立二维板件

`fill_regions.py` 适用于已有二维轮廓，支持凹多边形、孔洞、边带和可选铆钉：

```json
{"version":1,"pixels_per_unit":16,"padding_px":2,
 "materials":{"steel":{"procedural":{"preset":"plate","seed":7},"border_px":1,"edge_color":[62,64,66]}},
 "shapes":[{"id":"panel","material":"steel","outer":{"points":[[0,0],[2,0],[2,1],[0,1]],"edges":["outer","none","outer","none"]},"holes":[]}]}
```

运行 `python3 "$MD_TEXTURE_DIR/fill_regions.py" --input "$MD_PROJECT_DIR/assets/machines/example/regions.json" --output "$MD_PROJECT_DIR/assets/machines/example/panels" --preview`。配置中的 `tile` 路径相对于输入 JSON 所在目录。默认不覆盖已有产物；`--force` 仅替换本轮同名生成文件。它只输出独立 PNG，不执行三维展开或 UV 写回。

轮廓坐标 X 右、Y 下，顶点列表末尾不重复首顶点；孔洞严格在内部且不相交。每条边 `none/outer/seam` 分别表示不绘制边带、绘制完整边带、绘制半宽接缝。`tile` 与 `procedural` 二选一；tile 为调用者提供且有权使用的图。`padding_px` 是透明留白，不是防串色扩边。

`edge_profile` 可设 `light_direction`、逐像素 `bands[{light,shade}]` 和 `texture_strength`；颜色是美术明暗，不是物理烘焙。材质 `rivets` 支持 spacing_px、inset_px、gap_px、border_gap_px、sprite/colors；轮廓可限制 edges、alignment、placement。窄边或空间不足时省略，不能用铆钉填满空白。

工具限制为每图 1024²、最多 32 个板件；预览最多 8 张且每张 128²。复杂轮廓会按栅格预算拒绝。像素中心栅格化与图集的薄面保守覆盖不同，薄片需实际审阅。
