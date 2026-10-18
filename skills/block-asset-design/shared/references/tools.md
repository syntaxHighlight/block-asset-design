# 场景盘点与几何／UV 检查

先按[文件位置约定](workflow.md#文件位置)确定目标项目，再按[脚本适配约定](workflow.md#脚本适配)核对项目副本的接口及适用条件。下列示例中的 `MD_CHECK_DIR` 是项目脚本副本中的 `checks/`，`MD_PROJECT_DIR` 是目标项目；替换为实际绝对路径后，可从任意目录运行。

Blender 脚本可使用当前连接提供的代码执行能力，或通过本机 `blender` 可执行程序运行。后台检查使用 `--disable-autoexec`，不加载工程内的自动运行脚本。依赖这些脚本的运动，须另在具备授权和所需运行条件的环境中验证。

## 场景盘点与检查

场景结构和引用问题按[场景盘点](../../inspect/SKILL.md)判断，网格和 UV 数据分别按[几何检查](../../geometry-check/SKILL.md)与[UV 检查](../../uv-check/SKILL.md)判断。各模式复用同一工具，按任务选择所需模式即可。

```sh
MD_CHECK_DIR="/path/to/project/tools/block-asset-design/checks"
MD_PROJECT_DIR="/path/to/project"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/models/example/source.blend" --python-exit-code 1 --python "$MD_CHECK_DIR/blender_audit.py" -- --mode inventory --collection Machine --output "$MD_PROJECT_DIR/build/block-asset-design/example/inventory.json"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/models/example/source.blend" --python-exit-code 1 --python "$MD_CHECK_DIR/blender_audit.py" -- --mode geometry --objects Body Door --evaluated --grid 0.0625 --origin 0 0 0 --output "$MD_PROJECT_DIR/build/block-asset-design/example/geometry.json"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/models/example/source.blend" --python-exit-code 1 --python "$MD_CHECK_DIR/blender_audit.py" -- --mode uv --objects Body Door --uv-layer Production --size 512 512 --density 16 --output "$MD_PROJECT_DIR/build/block-asset-design/example/uv.json"
```

`--objects` 与 `--collection` 二选一；两者均省略时使用当前选择，空选择报错。集合范围包含子集合中的对象。几何与 UV 检查要求处于 Object Mode。

`--evaluated` 检查修改器求值结果；`--instances` 必须与它一起使用，用于纳入选定来源对象或实例生成器的求值实例。`--frame` 临时切换帧并恢复，不保存工程。实例和求值结果的索引不保证对应源网格。

`--grid` 设置空间网格步长，对象属性 `md_grid_step` 可单独设置或覆盖该值。两者均未设置时，才跳过该对象的网格对齐检查。检查使用世界坐标，`--origin` 与步长使用同一单位；姿态变化导致顶点偏离网格时，不自动视为错误。

UV 模式必须声明 `--uv-layer`。图集域用于给 UV 重叠检查分组，只有同域的三角形相互比较；工具并未因此识别实际材质或图片。Blender 入口将所选对象归入同一域，调用者须按实际贴图分组，并提供真实图像尺寸。

一个对象含多种采样图像或 UV 层时，不能用单一尺寸解释全部表面。现有命令行按对象或集合选择；需通过只读数据提取或项目脚本适配，按表面实际使用的图像和 UV 层分组，再检查各组。材质节点中的坐标变换、平铺和子图范围另行核验，报告说明哪些表面与采样关系已覆盖。

`--density` 是每模型单位像素数；不指定就不判断目标密度偏差。Blender 入口的默认拉伸比阈值 1.05、密度相对误差 .05、像素角点误差 .01px 均为诊断起点，可分别用 `--stretch`、`--density-tolerance`、`--pixel-tolerance` 调整。下方纯 JSON 命令行入口未提供这三个选项，使用默认阈值；需要不同阈值时先适配项目副本。

几何距离容差为 `--epsilon`（默认 1e-6 世界单位）。共面与 UV 重叠采用 AABB 扫描和三角形正面积裁切，边接触不计重叠。`--max-pairs` 默认 200000；预算不足以继续检查时，相关检查标为 `incomplete`。

每类最多保留 100 个定位样例，候选数继续累计；仅省略样例不表示检查未完成。检查未完成时，数量只代表已检查部分。UV 候选按三角形计数，不代表独立缺陷数量。

几何检查覆盖退化面、非平面面、面的开放边界、连接超过两个面的边、相邻绕序冲突、共面重叠和空间网格对齐。它**不覆盖**未连接任何面的孤立边、一般非共面穿插、体积包含、连续运动扫掠或细分着色质量。盘点输出约束、驱动器和直接图片节点，不解析任意 Python 引用或嵌套节点组。

几何与 UV 检查输出包含以下 JSON 字段：`scope`、`settings`、`checks`、`budgets`、`skipped`、`limitations`。每类包含状态、总数和有限样例，候选需结合语义判断。无可读网格时报错，缺 UV 或跳过对象不能视为完整通过。这些检查工具拒绝覆盖已有报告。

场景盘点使用独立的 JSON 结构，以 `objects` 列出对象、约束、驱动器和图片信息。

加 `--snapshot-output "$MD_PROJECT_DIR/build/block-asset-design/example/snapshot.json"` 可保存纯数据快照；无需 Blender 的复查入口：

```sh
python3 "$MD_CHECK_DIR/mesh_checks.py" --input "$MD_PROJECT_DIR/build/block-asset-design/example/snapshot.json" --mode uv --size 512 512 --density 16 --output "$MD_PROJECT_DIR/build/block-asset-design/example/uv-recheck.json"
```

快照包含 `meshes`：每项有 `id`、世界坐标 `vertices`、`faces[{vertices}]`、`triangles[{vertices,face,uv?}]`，可选网格步长 `grid_step`。图集域依次读取三角形的 `uv_domain`、所在网格的 `uv_domain`；均省略时使用共同的 `selected-atlas`。不同域只隔离重叠比较，图像尺寸仍由本次调用统一指定，因此不同尺寸的图像须分开调用。诊断不修改输入。
