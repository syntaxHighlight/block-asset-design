# Immersive Engineering 目录来源与使用边界

本目录仅包含检索元数据和原始许可证。原图、裁切图、动画元数据文件、预览及模型均未随技能携带；目录条目不代表素材已经安装或当前可用。实际提取产物保存在目标项目中。

目录依据 Immersive Engineering `1.21.1-12.4.2-194` 的归档资源记录。JAR 元数据署名为 BluSunrize and Damien A.W. Hazard，属于项目级署名；各项资源的原作者尚未逐一确认。资源与美术版权属于各自原作者。

[LICENSE.IE.txt](LICENSE.IE.txt) 保留了 Blu's License of Common Sense 原文，来自上游标签 `12.4.2-194` 对应提交 `583a182549d284a35c813b55ac2a0d1fddcf945a`；固定版本地址和许可证哈希见 [catalog.json](catalog.json)。本说明不替代原文或追加授权。

`catalog.json` 保留稳定 ID、分类、包内路径、SHA-256、裁切矩形及模型映射证据，不包含本地项目的用途确认。`usage_scope` 说明素材的使用范围，不能作为当前任务的用途确认；检索标签和模型映射也不能证明图案对应当前模型的电压、能源能力或功能。当前任务遵循[素材用途与授权确认](../../../shared/references/material-permissions.md)。

[provenance.json](provenance.json) 保留固定 JAR SHA-256 与脱敏前的元数据哈希，不包含本地归档名称或目录。历史哈希用于来源复核，不代表脱敏后文件的校验值；`included_files` 列出随包文件。

需要实际资源时，使用 [mod-resource-extract](../../../mod-resource-extract/SKILL.md) 检查指定版本、许可和本次用途。`catalog.json` 是检索目录，不是提取清单；从选定 ID 追到 `sources` 中的包内路径与哈希，检查裁切、模型、材质及动画依赖，再按[版本 1 清单契约](../../../mod-resource-extract/references/manifest.md)生成项目提取清单，完成用途确认后再执行提取。
