# Machine Design

这套技能供 AI 助手在 Blender 中制作机器，涵盖需求讨论、建模、模型修饰、贴图、动画和检查。也可继续修改已有模型，并查阅 Minecraft 资产规则与 Immersive Engineering（IE）风格参考。

## 安装

在项目目录运行（需要 Node.js）：

```sh
npx skills add syntaxHighlight/machine-design --skill '*'
```

技能之间相互引用，请整套安装。

## 素材与许可

[素材库入口](skills/machine-design/references/material-sources.md)随技能安装，可检索 IE 常用素材目录并查阅固定来源映射。当前仅分发目录与许可文本，不附带 IE 或 Minecraft 原图、裁切图、模型及其预览；工具 release 附件也只提供脚本。获准用途所需的素材按需从本地来源提取到目标项目。

调用用途受限的素材前，助手会按[用途与授权确认](skills/machine-design/shared/references/material-permissions.md)说明限制，并询问尚未明确的用途。仅要求“调用 IE 素材”并不代表确认用于 IE 附属模组；同一用途在当前会话中已明确时，不重复询问。用户的用途确认不能代替权利人的许可。

第三方素材仍适用各自的许可，技能或工具代码的许可不能覆盖它们。新增随包素材须有允许独立分发的依据，并携带来源、署名、许可与修改记录。当前仓库未指定统一的文档／代码开源许可证；公开可读取不代表获得任意再分发授权。

## 使用

首次需要配套脚本时，[machine-setup](skills/machine-setup/SKILL.md) 会从该技能指定的 release 附件获取脚本，放入目标项目。后续任务可按需修改这份副本，重复 setup 会保留已有修改。setup 只准备文件；脚本审阅、适配和必要验证随实际任务进行。

向助手说明目标，并提供模型路径和参考资料，例如：

> 用 machine-design 修改这台机器的外壳，保留现有动画和接口贴图。

完整制作可从讨论机器需求开始。确认方案并开始制作后，助手会继续推进建模、基本材质和必要的简单动画，分阶段审阅、修复，并自主判断何时达标。遇到需要改变设计共识或无法收敛的关键问题时，再讨论取舍。

用 `machine-iterate` 可继续打磨已有外观或运动。需要方便查看成果时，`machine-review-panel` 会为目标资产制作侧栏脚本，并提供手动运行说明。面板不会自动启动，也不要求逐轮点击确认。

也可以只做单步操作。模型操作需要 Blender 与 [Blender MCP](https://github.com/ahujasid/mcp-for-blender)；独立脚本需要 Python 3.10+，图像处理还需要 Pillow。

## 文档

- [制作入口](skills/machine-design/SKILL.md)
- [局部迭代](skills/machine-iterate/SKILL.md)
- [审阅面板制作](skills/machine-review-panel/SKILL.md)
- [场景盘点](skills/machine-inspect/SKILL.md)
- [几何与 UV 检查工具](skills/machine-design/shared/references/tools.md)
- [贴图工具](skills/machine-texture/references/texture-pipeline.md)
- [模组资源提取](skills/mod-resource-extract/SKILL.md)
- [开发与测试](tests/README.md)
