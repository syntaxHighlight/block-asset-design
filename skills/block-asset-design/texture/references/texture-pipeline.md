# 语义驱动的像素贴图

先整理几何与语义，在 Blender 中展开并检查，再导出已有 UV/几何/语义。绘制、打包后，指定生产 UV 层写回，连接材质并实际审阅。

先按[文件位置约定](../../shared/references/workflow.md#文件位置)确定目标项目，再按[脚本适配约定](../../shared/references/workflow.md#脚本适配)准备调用。下述参数和限制以配套源码为依据，实际执行前需核对项目脚本副本的版本与接口。

以下示例中的 `MD_TEXTURE_DIR` 是项目脚本副本中的 `texture/`，`MD_PROJECT_DIR` 是目标项目；替换为实际绝对路径后，可从任意目录运行。项目内路径优先沿用已有约定。

## 原生数据与导出

`md_edge_role` 为 EDGE INT，0 不描边、1 形体边、2 装配缝；`md_material_role` 为 FACE INT，对象字符串属性 `md_role_names` 存 JSON 映射，如 `{"0":"steel","1":"paint"}`。缺少面属性时，可用 `--default-role steel` 显式指定默认角色，工具不会推断语义；缺少边属性时，不自动加结构线。UV seam 不转为边角色。

```sh
MD_TEXTURE_DIR="/path/to/project/tools/block-asset-design/texture"
MD_PROJECT_DIR="/path/to/project"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/models/example/source.blend" --python-exit-code 1 --python "$MD_TEXTURE_DIR/blender_atlas.py" -- export --objects Body --uv-layer Source --source-size 512 512 --density 16 --default-role steel --output "$MD_PROJECT_DIR/build/block-asset-design/example/charts.json"
python3 "$MD_TEXTURE_DIR/paint_uv_atlas.py" --input "$MD_PROJECT_DIR/build/block-asset-design/example/charts.json" --config "$MD_PROJECT_DIR/assets/models/example/materials.json" --output "$MD_PROJECT_DIR/assets/models/example/atlas"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/models/example/source.blend" --python-exit-code 1 --python "$MD_TEXTURE_DIR/blender_atlas.py" -- apply --input "$MD_PROJECT_DIR/build/block-asset-design/example/charts.json" --layout "$MD_PROJECT_DIR/assets/models/example/atlas/pixel-atlas-layout.json" --target-layer Production --output "$MD_PROJECT_DIR/assets/models/example/production.blend"
```

导出操作读取源网格，要求对象处于 Object Mode，并指定已有的源 UV 层。所选对象若有启用视口显示的修改器，或多个对象共用同一网格数据，脚本会拒绝导出。需先准备符合要求的导出源，脚本不会自动应用修改器或拆分共享数据。

`--source-size` 指定源 UV 所在二维画布的宽高，避免忽略非方图比例。工具根据各表面的奇异值检查保形和密度一致性，`--density-tolerance` 默认 .05；超出时返回诊断，不会自动拉伸至一致。每个对象等比换算至指定密度，连续 UV 边组成岛。导出保留原 UV，不重新展开几何。

写回时校验源几何、源 UV、对象变换、各面的材质索引与角色、边角色及输入哈希；资产已变则需重新导出。目标层必须不同于源层；目标层已存在时，需显式指定 `--replace-target`。始终保存到新的 `.blend`，不覆盖源文件。

写回只写 UV，**不修改材质节点**。写回后，还需在材质中指定生产 UV 层（示例中名为 Production），用该层坐标采样生成的图像，再检查显示效果。

## 材质配方

命令行入口将 `details_filename` 及其描述文件中的 `source` 都解析为相对于 `--config` 所指定文件的目录，而非技能目录或描述文件目录；下例配置文件名为 `materials.json`。模型引用的图像应保留在项目中。

`materials.json` 最小示例：

```json
{"version":1,"materials":{"steel":{"procedural":{"preset":"plate","seed":7,"noise_strength":0.6}}},"atlas_filename":"pixel_atlas.png"}
```

`preset` 必填，可选 `plate/structure/machined/painted`，分别提供默认色板与噪声尺度；这些程序化材质预设不含第三方采样色板。可用亮度递增的 RGB `palette` 和对应的正数 `palette_weights` 替换色板及权重，噪声尺度仍由预设决定。

其他参数为 `direction: x|y`（默认 `x`）、uint32 `seed`（默认 `0`）和 0 到 1 的 `noise_strength`（默认 `0.75`）。`algorithm` 仅接受 `jittered-clusters-v1`，省略时也使用该值。

重复生成需保持配方、坐标、种子和 `chart.mesh` 一致，结果不随画布大小变化。生成器将 `chart.mesh` 的 CRC32 与配方种子异或；Blender 导出器将对象名写入该字段，因此重命名或拆合对象可能改变底纹。需要跨对象连续底纹或重命名后保持结果时，应在项目适配器中明确稳定的种子分组，并验证连续性。

图集生成器接收版本 1 格式的输入，其中包含 `charts`、`meshes`、`pixels_per_unit` 和 `padding_px`；每个岛的面数据包含原环索引、模型位置、法线、角色、像素坐标及原三角划分。

图集宽高各不超过 1024 像素，超出时报错，不通过缩小 UV 改变密度。打包时仅做整数像素平移，对薄面采用保守覆盖，并按岛向外扩色。细于像素的不同表面可能共享像素，输出会列出未独立覆盖的微小面。

结构线按真实边角色绘制，每像素只叠一次。通过配方 `details_filename` 指定原图描述文件，在其中记录来源图、哈希、密度和模型空间 stamp；完整字段参见生成器的 `stamp_sample`/`generate`。投影后需核验像素覆盖是否完整，不能仅确认有像素命中。

通用 Blender 导出入口无法重建原材质，会拒绝 `artwork` 和 `glass` 面角色。将这些表面保留在单独受保护的材质或对象中，由专门的适配器处理原图和透明效果后再合成；占位灰色不代表原材质已保留。

## 独立二维板件

`fill_regions.py` 适用于已有二维轮廓，支持凹多边形、孔洞、边带和可选铆钉：

```json
{"version":1,"pixels_per_unit":16,"padding_px":2,
 "materials":{"steel":{"procedural":{"preset":"plate","seed":7},"border_px":1,"edge_color":[62,64,66]}},
 "shapes":[{"id":"panel","material":"steel","outer":{"points":[[0,0],[2,0],[2,1],[0,1]],"edges":["outer","none","outer","none"]},"holes":[]}]}
```

运行 `python3 "$MD_TEXTURE_DIR/fill_regions.py" --input "$MD_PROJECT_DIR/assets/models/example/regions.json" --output "$MD_PROJECT_DIR/assets/models/example/panels" --preview`。配置中的 `tile` 路径相对于输入 JSON 所在目录。默认不覆盖已有产物；`--force` 仅替换本轮同名生成文件。它只输出独立 PNG，不执行三维展开或 UV 写回。

轮廓坐标 X 向右、Y 向下，顶点列表末尾不重复首顶点；孔洞须严格位于内部且不相交。每条边 `none/outer/seam` 分别表示不绘制边带、绘制完整边带、绘制半宽接缝。`tile` 与 `procedural` 二选一；tile 为调用者提供且有权使用的图。`padding_px` 是透明留白，不是防串色扩边。

`edge_profile` 可设 `light_direction`、逐像素 `bands[{light,shade}]` 和 `texture_strength`；这些颜色用于表现美术明暗，不代表物理烘焙结果。材质 `rivets` 支持 spacing_px、inset_px、gap_px、border_gap_px、sprite/colors；轮廓可限制 edges、alignment、placement。边缘过窄或空间不足时省略铆钉，不能用铆钉填满空白。

每次最多生成 32 个板件，每个输出图像的宽高各不超过 1024 像素，全部板件图像合计不超过 4,000,000 像素。

`--preview` 要求本次板件不超过 8 个，且每个图像的宽高各不超过 128 像素；输出一张 `specimens.png` 拼图，包含原尺寸和四倍最近邻放大视图。复杂轮廓还受栅格计算预算限制。像素中心栅格化与图集的薄面保守覆盖不同，薄片需实际审阅。
