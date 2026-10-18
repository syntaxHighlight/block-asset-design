# 脚本测试

测试会生成模型和图片样例，将输出写入临时目录，不使用项目中的机器资产。所有命令均在本仓库根目录运行。

## 运行测试

先创建 Python 环境并安装测试依赖：

```sh
python3 -m venv /tmp/machine-design-tests
/tmp/machine-design-tests/bin/pip install -r tests/requirements.txt
```

运行几何、UV、图像、资源提取和工具分发测试：

```sh
/tmp/machine-design-tests/bin/python -m unittest discover -s tests -v
```

这条命令会跳过需要 Blender 的用例。安装 Blender，确认可以调用 `blender` 命令后，再运行集成测试：

```sh
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python tests/run_blender.py
```

集成测试失败时返回非零退出码。

## 测试范围

| 范围 | 检查内容 |
| --- | --- |
| 几何与 UV | 开放边、退化面、非平面面、绕序、共面重叠、网格对齐、图集范围、密度与拉伸，以及检查预算耗尽时的状态 |
| 贴图 | 像素覆盖、孔洞与透明边、轮廓方向、小于单个像素的面、结构边重复染色、原图坐标方向、图集映射与哈希 |
| 资源提取 | 精确裁切、许可记录、哈希、包外声明文件、路径与输出保护，以及失败后是否残留输出 |
| 素材目录 | IE 发布目录仅含明确列出的元数据文件，固定来源与许可哈希未变，安装后素材与授权入口的相对链接有效；新增原图、预览或其他文件前，须核实分发依据，再调整白名单 |
| 工具分发 | 构建并解压 release 脚本包，从第三个目录运行检查、图集、板件和资源提取工具；在隔离进程中确认 Blender 工具的跨目录依赖来自包内；检查包布局、依赖清单、校验和、打包结果是否可重复，以及产物路径和输入文件保留情况 |
| Blender | 对象选择范围、世界坐标、求值网格、场景盘点、UV 导出与写回、保存后重新打开、源文件与源 UV 保留、失败回滚、帧和视图状态恢复 |

样例使用可手算结果的几何体和微型图片。重复运行结果一致、导入导出相互吻合，都不能单独证明结果正确。

后台视图测试只检查状态能否恢复，不验证视觉效果。复杂实例、完整材质图案的保留、连续运动及不同 Blender 版本的兼容性，仍需另行验证。

## 构建 release 脚本包

打包仅使用 Python 标准库，不运行 Blender 或检查脚本：

```sh
python3 scripts/package-machine-tools.py --output /tmp/machine-design-scripts.tar.gz
```

命令同时生成 `machine-design-scripts.tar.gz.sha256`。包根直接包含 `checks/`、`texture/`、`review/`、`resources/`，各工具所需的依赖清单放在对应目录。已有的适用许可和声明文件一并保留。解压后的工具不依赖技能安装位置或源码仓库。
