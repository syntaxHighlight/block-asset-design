---
name: machine-design
description: 协调机器资产的综合制作任务；用于需要选择工作入口、安排依赖或跨阶段推进的请求。明确的单项任务直接使用对应技能。
---

# 机器资产制作

读取[工作约定](shared/references/workflow.md)，识别用户目标、当前资产和已认可要求。综合任务按下表选择主导技能；明确的单项任务直接进入对应技能，无需经过本入口。接手既有模型时按[接管规则](shared/references/takeover.md)只补本轮必要信息。制作 Minecraft 资产时加载[Minecraft 规则](shared/references/profiles/minecraft.md)；用户要求 Immersive Engineering（IE）风格时再读[风格方向](shared/references/profiles/ie-style.md)。

## 选择入口

| 当前需要 | 读取并执行 |
| --- | --- |
| 关键设计选择尚不明确 | [需求澄清](../machine-brief/SKILL.md) |
| 新建或改变比例、布局、功能构件，验证机构可行性 | [建模](../machine-model/SKILL.md) |
| 改善已确定设计的拓扑、接合、法线与局部轮廓 | [模型修饰](../machine-refine/SKILL.md) |
| 展开、程序化贴图与图集 | [贴图](../machine-texture/SKILL.md) |
| 完善机构、时序与动作 | [动画](../machine-animate/SKILL.md) |

建模、模型修饰、贴图和动画可作为新建任务的参考顺序。按本次要解决的问题选择技能，不按资产的新旧或完成程度划分；已有成品改变比例或布局时仍属于建模。各部件需明确当前以哪个可编辑源为准。

需要查找美术素材或既有接口时，按[资源查找与使用](shared/references/resources.md)先复用项目内容；指定模组存在资源缺口时调用[模组资源提取](../mod-resource-extract/SKILL.md)。

## 制作与收敛

按[操作索引](references/operations.md)选择审阅、能力查询和检查；自主程度、修复边界与停止条件遵循工作约定。

完成后提供可编辑文件的位置、查看或播放方式，以及尚未验证的部分。只在产生新术语、共识或可复用发现时按[记录规则](shared/references/memory.md)更新已有文档。
