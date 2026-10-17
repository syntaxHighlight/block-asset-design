# 场景盘点与几何／UV 检查

先按[文件位置约定](workflow.md#文件位置)确定目标项目，并按[脚本适配约定](workflow.md#脚本适配)准备调用。下列示例中的 `MD_CHECK_DIR` 是项目脚本副本中的 `checks/`，`MD_PROJECT_DIR` 是目标项目；替换为实际绝对路径后，可从任意目录运行。Blender 脚本使用当前连接提供的代码执行能力，或通过本机 `blender` 可执行程序运行。后台检查使用 `--disable-autoexec`，不加载工程内任意自动脚本；因此依赖受禁脚本的运动必须另外在可信交互环境验证。

## 场景盘点与检查

场景结构和引用问题由[场景盘点](../../../machine-inspect/SKILL.md)解释；网格和 UV 数据分别按[几何检查](../../../machine-geometry-check/SKILL.md)与[UV 检查](../../../machine-uv-check/SKILL.md)判断。各模式复用同一工具，不代表需要全部运行。

```sh
MD_CHECK_DIR="/path/to/project/tools/machine-design/checks"
MD_PROJECT_DIR="/path/to/project"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/machines/example/source.blend" --python-exit-code 1 --python "$MD_CHECK_DIR/blender_audit.py" -- --mode inventory --collection Machine --output "$MD_PROJECT_DIR/build/machine-design/example/inventory.json"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/machines/example/source.blend" --python-exit-code 1 --python "$MD_CHECK_DIR/blender_audit.py" -- --mode geometry --objects Body Door --evaluated --grid 0.0625 --origin 0 0 0 --output "$MD_PROJECT_DIR/build/machine-design/example/geometry.json"
blender --background --factory-startup --disable-autoexec "$MD_PROJECT_DIR/assets/machines/example/source.blend" --python-exit-code 1 --python "$MD_CHECK_DIR/blender_audit.py" -- --mode uv --objects Body Door --uv-layer Production --size 512 512 --density 16 --output "$MD_PROJECT_DIR/build/machine-design/example/uv.json"
```

`--objects` 与 `--collection` 二选一；省略时用当前选择，空选择报错。`--evaluated` 检查修改器求值结果；额外 `--instances` 包含选定来源/实例生成器的求值实例。`--frame` 临时切换帧并恢复，不保存工程。实例和求值结果的索引不保证对应源网格。

`--grid` 设置空间网格步长，对象属性 `md_grid_step` 可单独设置或覆盖该值。两者均未设置时，才跳过该对象的网格对齐检查。检查使用世界坐标，`--origin` 与步长使用同一单位；姿态变化导致顶点偏离网格时，不自动视为错误。

UV 模式必须声明 `--uv-layer`；所选对象应属于同一图集域。不同贴图分开调用。尺寸必须是真实目标图像尺寸。`--density` 是每模型单位像素数；不指定就不判断目标密度偏差。默认拉伸比阈值 1.05、密度相对误差 .05、像素角点误差 .01px 均为诊断起点，可分别用 `--stretch`、`--density-tolerance`、`--pixel-tolerance` 调整。

几何距离容差为 `--epsilon`（默认 1e-6 世界单位）。共面与 UV 重叠采用 AABB 扫描和三角形正面积裁切，边接触不计重叠；`--max-pairs` 默认 200000，达到预算明确 `incomplete`。最多保留每类 100 个定位样例，总候选数量另计。UV 候选按三角形计数，不代表独立缺陷数量。

几何检查覆盖退化/非平面面、开放/非流形边、相邻绕序冲突、共面重叠和空间网格对齐。它**不覆盖**一般非共面穿插、体积包含、连续运动扫掠、细分着色质量。盘点输出约束/驱动和直接图片节点，不解析任意 Python 引用或嵌套节点组。

几何与 UV 检查输出包含以下 JSON 字段：`scope`、`settings`、`checks`、`budgets`、`skipped`、`limitations`。每类包含状态、总数和有限样例；候选需结合语义判断。无可读网格时报错，缺 UV 或跳过对象不能视为完整通过。这些检查工具拒绝覆盖已有报告。场景盘点使用独立的 JSON 结构，以 `objects` 列出对象、约束、驱动器和图片信息。

加 `--snapshot-output "$MD_PROJECT_DIR/build/machine-design/example/snapshot.json"` 可保存纯数据快照；无需 Blender 的复查入口：

```sh
python3 "$MD_CHECK_DIR/mesh_checks.py" --input "$MD_PROJECT_DIR/build/machine-design/example/snapshot.json" --mode uv --size 512 512 --density 16 --output "$MD_PROJECT_DIR/build/machine-design/example/uv-recheck.json"
```

快照包含 `meshes`：每项有 `id`、世界坐标 `vertices`、`faces[{vertices}]`、`triangles[{vertices,face,uv?}]`。可选 `grid_step`、`uv_domain`；默认一个选定图集域。诊断不修改输入。
