---
name: asset-texture
description: 为资产模型展开 UV、利用边和材质语义生成贴图、整理图集及保留接口原图；支持已有 UV 的局部修改。
---

# 贴图

读取[工作约定](../shared/references/workflow.md)，检查实际使用的 UV 层、材质连接、目标密度与采样方式。缺少场景信息或发现资源引用异常时，按需使用[场景盘点](../inspect/SKILL.md)。

Minecraft 任务读取[Minecraft 制作规则](../shared/references/profiles/minecraft.md)。缺少美术素材或接口来源时，按[资源查找与使用](../shared/references/resources.md)复用已有内容；需要检查指定模组时，调用[模组资源提取](../mod-resource-extract/SKILL.md)。

1. 明确[源展开与生产 UV](../shared/references/glossary.md)、受保护图案、材质用途及结构边。拓扑刚修改时先按[几何契约](../shared/references/geometry.md)确认语义仍有效。
2. 选择展开方法前，使用[Blender 能力查询](../blender-capabilities/SKILL.md)，按表面选择接缝、固定点、Live Unwrap、Follow Active Quads 等方法。优先保持形状与密度，避免逐顶点吸附破坏 UV 面形状。已有良好 UV 时，只做本轮所需调整。
3. 需要生成或重建图集时，按[图集工具](references/texture-pipeline.md)将现有 UV、几何和边语义交给生成器。不能直接将 UV 切口、材质边界、三角划分当作装配线；窄面避免重复描边。先在代表性表面验证形状、密度及真实贴图效果，再扩展到其余表面。
4. 生成底纹时，保持配方、共享坐标、种子及参与种子计算的对象标识稳定；对象重命名或拆合后的影响按[图集工具](references/texture-pipeline.md)核验。接口原图、方向、安装位置和覆盖范围单独验证；部分命中不能视为完整保留。
5. 需要调整图集布局时，只做整岛变换，保持密度及方向要求；写回时使用显式指定的生产 UV 层并连接材质，保留源展开。不能宣称输出的扩边适用于任意 mipmap。变长构件需检查运动中的纹素密度，并通过前后跳转抽查映射是否稳定。
6. 按各材质实际使用的图像尺寸和 UV 层，用[UV 检查](../uv-check/SKILL.md)核查重叠、越界、密度及拉伸，并另行核验材质节点中的采样变换。同一对象使用不同图像时，分别核对各表面对应的图像尺寸。用[审阅](../review/SKILL.md)检查棋盘格、原尺寸像素、整体材质与内部可见性。修正生成脚本、配置或操作步骤；发现生成方法的缺陷时，复查使用同一方法的其他表面。

完成条件：目标表面与实际映射正确，受保护区域保留，结果可重建且可继续编辑；说明未验证的采样或运行时条件。
