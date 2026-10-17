# Machine Design

一套供 AI 助手使用的 Blender 机器制作技能，涵盖需求讨论、建模、模型修饰、贴图、动画和检查。支持继续修改已有模型，并提供 Minecraft 资产规则与 Immersive Engineering（IE）风格参考。

## 安装

在项目目录运行（需要 Node.js）：

```sh
npx skills add syntaxHighlight/machine-design --skill '*'
```

技能之间有相互引用，请整套安装。

## 使用

向助手说明目标，并提供模型路径和参考资料，例如：

> 用 machine-design 修改这台机器的外壳，保留现有动画和接口贴图。

完整制作可从机器需求讨论开始：确认方案并开始制作后，助手自动推进建模、基本材质和必要的简单动画，分阶段审阅、修复并自主判断何时达标。遇到需要改变设计共识或无法收敛的关键问题时再讨论取舍。

也可用 `machine-iterate` 继续打磨已有外观或运动。需要方便查看成果时，`machine-review-panel` 为目标资产制作侧栏脚本，交付手动运行说明；面板不会自动启动，也不要求逐轮点击确认。

也可以只做单步操作，模型操作需要 Blender与 [Blender MCP](https://github.com/ahujasid/mcp-for-blender)；独立脚本需要 Python 3.10+，图像处理还需要 Pillow。

## 文档

- [制作入口](skills/machine-design/SKILL.md)
- [局部迭代](skills/machine-iterate/SKILL.md)
- [审阅面板制作](skills/machine-review-panel/SKILL.md)
- [场景盘点](skills/machine-inspect/SKILL.md)
- [几何与 UV 检查工具](skills/machine-design/shared/references/tools.md)
- [贴图工具](skills/machine-texture/references/texture-pipeline.md)
- [模组资源提取](skills/mod-resource-extract/SKILL.md)
- [开发与测试](tests/README.md)
