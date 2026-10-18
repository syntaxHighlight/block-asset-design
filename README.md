# Block Asset Design

这套技能供 AI 助手在 Blender 中制作或修改方块、道具、装饰及机械资产，涵盖需求讨论、建模、模型修饰、贴图、简单动画和审阅。Minecraft 任务可按需进行游戏内验收；机械机构与 Immersive Engineering（IE）风格规则按任务加载。

## 安装

在项目目录运行（需要 Node.js）：

```sh
npx skills add syntaxHighlight/block-asset-design --skill block-asset-design
```

`block-asset-design` 包含完整制作流程、可单独调用的专项技能和共享资源。外层 `SKILL.md` 是制作入口，子目录保存专项技能。安装时请保留整个集合的目录结构，不要用 `--full-depth` 将子技能拆开平铺安装。客户端可能以不同方式显示目录分组。

本地开发可在目标项目中运行 `npx skills add /absolute/path/to/this-repo --skill block-asset-design`。

从 `v2.0` 之前的平铺安装升级时，请先确认集合中的技能入口和引用可用，再移除旧的 `machine-*` 安装，避免重复。项目中的旧工具目录与 Blender `md_*` 属性仍然兼容，无需改写已有资产。

## 素材与许可

[素材库入口](skills/block-asset-design/references/material-sources.md)随技能安装，可用于查找 IE 常用素材及其来源。安装包仅包含素材目录与许可文本，不附带 IE 或 Minecraft 原图、裁切图、模型及其预览；工具 release 附件也只提供脚本。确认用途获准后，再从本地来源提取所需素材到目标项目。

调用用途受限的素材前，助手会按[用途与授权确认](skills/block-asset-design/shared/references/material-permissions.md)说明限制，并询问尚未明确的用途。仅要求“调用 IE 素材”并不代表确认用于 IE 附属模组；同一用途在当前会话中已明确时，不重复询问。用户的用途确认不能代替权利人的许可。

第三方素材仍适用各自的许可，技能或工具代码的许可不能覆盖它们。新增随包素材须有允许独立分发的依据，并携带来源、署名、许可与修改记录。当前仓库未指定统一的文档／代码开源许可证；公开可读取不代表获得任意再分发授权。

## 使用

首次需要配套脚本时，[tool-setup](skills/block-asset-design/setup/SKILL.md) 会从指定的 release 附件下载脚本，放入目标项目。后续任务可按需修改这份副本，重复 setup 会保留已有修改。setup 负责准备文件，助手会在使用时审阅脚本、按项目需要适配并验证。

向助手说明目标，并提供模型路径和参考资料，例如：

> 用 block-asset-design 修改这个资产的外观，保留现有动画和受保护图案。

完整制作从讨论资产需求开始。确认方案后，助手会完成建模、基本材质和必要的简单动画，分阶段检查和修复，直到达到约定要求。如果需要改变已确认的设计，或反复修改仍未解决关键问题，助手会与你讨论取舍。

用 `asset-iterate` 可继续调整已有资产的外观或运动。`asset-review-panel` 可为目标资产制作方便查看成果的侧栏面板，并提供手动运行说明。面板由你启动，制作过程中无需逐轮点击确认。

游戏内验收需要项目提供测试世界、客户端探针和校验入口；本集合不自带通用于所有版本和加载器的游戏驱动。验收会同时检查自动校验结果和实际游戏画面，详见 [game-acceptance](skills/block-asset-design/game-acceptance/SKILL.md)。

也可以只做单步操作。模型操作需要 Blender 与 [Blender MCP](https://github.com/ahujasid/mcp-for-blender)；独立脚本需要 Python 3.10+，图像处理还需要 Pillow。

## 文档

- [制作入口](skills/block-asset-design/SKILL.md)
- [局部迭代](skills/block-asset-design/iterate/SKILL.md)
- [审阅面板制作](skills/block-asset-design/review-panel/SKILL.md)
- [场景盘点](skills/block-asset-design/inspect/SKILL.md)
- [几何与 UV 检查工具](skills/block-asset-design/shared/references/tools.md)
- [贴图工具](skills/block-asset-design/texture/references/texture-pipeline.md)
- [模组资源提取](skills/block-asset-design/mod-resource-extract/SKILL.md)
- [开发与测试](tests/README.md)
