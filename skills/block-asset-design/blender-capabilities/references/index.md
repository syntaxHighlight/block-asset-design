# 问题驱动的能力索引

只需读取当前问题对应的行，再到本机版本文档中核查具体参数。

| 触发问题 | 候选与关键区别 | 验证 |
| --- | --- | --- |
| 整理对象数量或形成连续外壳 | Collection 分组、Parent 建立父子关系，均保留独立对象；Join 合并为一个对象；Boolean 改变几何形状。几何融合范围需另行确定 | 确认活动件仍独立，引用和属性已保留 |
| 孔洞周围出现细条或减面过度 | 比较 Limited Dissolve、Decimate Planar 与局部重拓扑，保留曲率和开口边界 | 检查轮廓、孔洞、法线和 UV；允许为保形增加面数 |
| 融合前后 UV 异常 | 检查 Mesh UV layers、attribute domains 与 Boolean 属性传递 | 核对层名、活动层及渲染层，检查新面的 UV 和语义迁移 |
| 大量 UV 碎片或侧壁不连续 | 比较 Seams、Unwrap、Pin、Live Unwrap；规则四边条带可考虑 Follow Active Quads | 核对起始面形状与长度模式，检查拉伸和重叠 |
| 像素吸附或重打包 | 比较整岛变换、Pack Islands 与 Round to Pixels；逐顶点取整可能改变岛形状 | 按目标图像尺寸检查形状、密度和方向，确认写入生产 UV 层 |
| 接合后出现黑面或薄缝 | 分别排查法线与绕序、重叠、非平面面和实际几何开口 | 从多个角度检查素模，对比源网格与求值结果 |
| 机构联动或行程控制 | 比较 Parent、Limit、Copy/Transformation、Track 与 Drivers | 核对空间、轴向及求值姿态；Limit 不检测外壳穿透 |
| 伸缩表面纹理拉伸 | 根据机构选择刚性套筒运动、变长几何，或按不可变参考裁切 UV | 检查纹素密度、端盖及最大长度状态，前后跳转抽查映射是否稳定 |
| 常规显隐或动作审阅 | 优先使用 Outliner、Local View、Viewport 与原生控制器；确有缺口才增加面板 | 确认视图可恢复，播放器使用同一套机构控制 |
| 实例或修改器求值后才出问题 | 用 Evaluated depsgraph、object_instances、to_mesh 获取求值对象或网格 | 确认实际检查了哪些对象和实例，并说明接触判断及计数依据 |
| 变形动画导出或烘焙后色变 | 导出时核查求值拓扑与重采样；色变时核查颜色空间、视图变换与烘焙通道 | 核对跨帧对应关系，并在目标软件或运行时检查实际输出 |

文档入口：[建模手册](https://docs.blender.org/manual/en/latest/modeling/index.html)、[UV 手册](https://docs.blender.org/manual/en/latest/modeling/meshes/uv/index.html)、[约束手册](https://docs.blender.org/manual/en/latest/animation/constraints/index.html)、[Python API](https://docs.blender.org/api/current/)。这些链接用于查找文档，执行前需切换到本机版本。
