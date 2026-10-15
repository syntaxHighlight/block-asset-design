---
name: machine-model
description: 新建或调整机器的比例、布局、功能构件和主体形态，并验证机构可行性；适用于草稿及已有成品的设计修改。
---

# 建模

先读[工作约定](../machine-design/shared/references/workflow.md)；接手半成品时再读[接管规则](../machine-design/shared/references/takeover.md)。Minecraft 任务加载[模型与像素规则](../machine-design/shared/references/profiles/minecraft.md)。设计已确定、仅需改善拓扑、接缝或法线时，由[模型修饰](../machine-refine/SKILL.md)主导。

需要接口构件、既有模型或风格依据时按[资源查找与使用](../machine-design/shared/references/resources.md)先查项目资产；指定模组的检查与提取交给[模组资源提取](../mod-resource-extract/SKILL.md)。

1. 确认观看尺度、静态占位、接口和要表现的功能；不把未定玩法固化为外露机构。优先建立整体轮廓、主要分区、支承与通路，先解决空间冲突再细化。
2. 分别表达功能组、运动组、材质分区和可能的合并范围，定义见[术语](../machine-design/shared/references/glossary.md)。同步运动不代表可以合并；独立显隐、接触和后续职责也影响边界。
3. 用父子关系、原生约束和必要驱动器建立可预览机构，先定轴心、行程、联动、关键姿态和净空。能力选择查[Blender 索引](../blender-capabilities/SKILL.md)。约束控制运动，不自动保证几何无碰撞。此处验证机构是否可行；时序、节奏、循环和任意帧跳转由[动画](../machine-animate/SKILL.md)完善，沿用同一套控制器和机构。
4. 草稿可用构建脚本快速比较方案，说明重生成范围；用户手工修改过的区域先明确后续以脚本还是手工模型为准。进入模型修饰阶段的部分以当前可编辑模型为准，后续优先使用通用工具进行局部修改。
5. 用[审阅](../machine-review/SKILL.md)观察整体、接口、支承和运动；尺寸或造型网格对齐问题用[几何检查](../machine-geometry-check/SKILL.md)。

完成条件：比例和功能关系可判断，接口有依据，运动空间经过必要观察，源模型可继续编辑。草稿没有细节不是缺陷；整体设计方向尚未确定时，先调整比例与布局。
