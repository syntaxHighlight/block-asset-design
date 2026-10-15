# 问题驱动的能力索引

只读当前问题对应行；具体参数到本机版本文档核查。

| 触发问题 | 候选与关键区别 | 验证 |
| --- | --- | --- |
| 整理对象数量或连续外壳 | Collection/Parent 保留职责；Join 组织网格；Boolean 改形；不要用功能组直接决定融合 | 活动件独立、引用与属性保留 |
| 孔洞周围细条、过度减面 | Limited Dissolve、Decimate Planar 与局部重拓扑；保留曲率/开口边界 | 轮廓、孔洞、法线、UV；面数可增加 |
| 融合前后 UV 异常 | Mesh UV layers、attribute domains、Boolean 属性传递 | 层名、活动/渲染层、新面与语义迁移 |
| 大量 UV 碎片、侧壁不连续 | Seams、Unwrap、Pin、Live Unwrap；规则四边条带考虑 Follow Active Quads | 起始面形状、长度模式、拉伸与重叠 |
| 像素吸附或重打包 | 整岛变换、密度、Pack Islands、Round to Pixels；后者可能改变形态 | 指定图像尺寸、形态、密度、方向、生产层 |
| 接合后出现黑面或薄缝 | 法线/绕序、重叠、非平面面、真实几何开口分别判断 | 素模与多角度、源及求值结果 |
| 机构联动或行程 | Parent、Limit、Copy/Transformation、Track、Drivers | 空间和轴向、求值姿态；Limit 不检测外壳穿透 |
| 伸缩表面纹理拉伸 | 刚性套筒运动、变长几何、按不可变参考裁切 UV 分别选型 | 密度、端盖、最大长度和随机跳转 |
| 常规显隐或动作审阅 | Outliner、Local View、Viewport、原生控制器；确有缺口才增加面板 | 视图可恢复、播放器共用机构 |
| 实例/修改器后才出问题 | Evaluated depsgraph、object_instances、to_mesh | 真正显示范围、接触分类与统计口径 |
| 变形导出或烘焙色变 | 求值拓扑/重采样，颜色空间/视图变换/烘焙通道 | 跨帧对应、实际输出图像与使用它的目标软件或运行时 |

文档入口：[建模手册](https://docs.blender.org/manual/en/latest/modeling/index.html)、[UV 手册](https://docs.blender.org/manual/en/latest/modeling/meshes/uv/index.html)、[约束手册](https://docs.blender.org/manual/en/latest/animation/constraints/index.html)、[Python API](https://docs.blender.org/api/current/)。链接为发现入口，执行前选择本机版本。
