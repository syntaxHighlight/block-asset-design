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

也可以只做单步操作，模型操作需要 Blender与 [Blender MCP](https://github.com/ahujasid/mcp-for-blender)；独立脚本需要 Python 3.10+，图像处理还需要 Pillow。

## 文档

- [制作入口](skills/machine-design/SKILL.md)
- [场景盘点](skills/machine-inspect/SKILL.md)
- [几何与 UV 检查工具](skills/machine-design/shared/references/tools.md)
- [贴图工具](skills/machine-texture/references/texture-pipeline.md)
- [模组资源提取](skills/mod-resource-extract/SKILL.md)
- [开发与测试](tests/README.md)
