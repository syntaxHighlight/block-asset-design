---
name: machine-texture
description: 为机器模型展开 UV、利用边和材质语义生成贴图、整理图集及保留接口原图；支持已有 UV 的局部修改。
---

# 贴图

读[工作约定](../machine-design/shared/references/workflow.md)，检查实际使用的 UV 层、材质连接、目标密度与采样方式；缺少场景信息或发现资源引用异常时，按需使用[场景盘点](../machine-inspect/SKILL.md)。Minecraft 任务读[像素规则](../machine-design/shared/references/profiles/minecraft.md)，缺少美术素材或接口来源时按[资源查找与使用](../machine-design/shared/references/resources.md)复用已有内容，需要检查指定模组时调用[模组资源提取](../mod-resource-extract/SKILL.md)。

1. 明确源展开、生产 UV、受保护图案、材质用途及结构边。拓扑刚修改时先按[几何契约](../machine-design/shared/references/geometry.md)确认语义仍有效。
2. 选择展开方法前读[能力索引](../blender-capabilities/SKILL.md)：接缝、固定点、Live Unwrap、Follow Active Quads 等按表面选择。保形与密度优先；避免逐顶点吸附破坏 UV 面形状。已有良好 UV 时只做本轮所需调整。
3. 需要生成或重建图集时，按[图集工具](references/texture-pipeline.md)将现有 UV、几何和边语义交给生成器。UV 切口、材质边界、三角划分不自动成为装配线；窄面避免重复描边。先做代表性表面再扩展。
4. 生成底纹时，由配方、共享坐标与种子决定结果，不依赖画布尺寸。接口原图、方向、安装位置和覆盖范围单独验证；部分命中不能视为完整保留。
5. 需要调整图集布局时，只做整岛变换，保持密度及方向要求；写回时使用显式指定的生产 UV 层并连接材质，保留源展开。输出扩边不能宣称适用任意 mipmap。变长构件检查密度和随机跳转，不只看静止状态。
6. 用[UV 检查](../machine-uv-check/SKILL.md)检查重叠、越界、密度及拉伸；用[审阅](../machine-review/SKILL.md)检查棋盘格、原尺寸像素、整体材质与内部可见性。修正生成脚本、配置或操作步骤，避免重建时再次出现同一问题。

完成条件：目标表面与实际映射正确，受保护区域保留，结果可重建且可继续编辑；说明未验证的采样或运行时条件。
