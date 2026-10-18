# 素材库入口

查找素材时先复用目标项目已有内容，再按下表找到随技能发布的目录。目录可用不表示原图已安装，也不表示本次用途已获许可；使用前执行[用途与授权确认](../shared/references/material-permissions.md)。

| 来源 | 当前提供 | 获取与使用边界 |
| --- | --- | --- |
| IE `1.21.1-12.4.2-194` | [常用素材目录](material-library/ie-textures/INDEX.md)：稳定 ID、分类、原包路径、哈希和裁切／模型证据 | 随技能仅提供元数据及许可证文件，不包含原图、裁切图或预览。按授权确认规则确认附属用途或取得另行授权后，从对应本地包准备所需条目 |
| Minecraft 原版 | [官方 EULA](https://www.minecraft.net/en-us/eula)与[使用指南](https://www.minecraft.net/en-us/usage-guidelines)；[Minecraft 制作规则](../shared/references/profiles/minecraft.md) | 尚未提供逐项素材目录或获准再分发的原图包。按项目目标版本核查本地来源与具体用途；不将购买游戏或本地持有等同于原图再分发许可 |
| 项目自制或其他第三方素材 | 目标项目的资源索引、NOTICE、manifest 和接口记录 | 沿用真实来源与已核验用途；缺少出处、原图或协议时明确缺口 |

按需使用 IE 目录中的文件映射，通过[模组资源提取](../../mod-resource-extract/SKILL.md)生成提取清单，不默认将整个库复制到项目。完成后，在项目索引中关联实际文件和用途记录。

此目录随整套 skills 安装，不依赖旧项目的隐藏目录或清理归档。`machine-setup` 的 release 附件是工具脚本包，不携带第三方美术。当前发布内容没有通用授权的第三方原图包；后续新增实际素材时按授权确认文档的发布要求逐项纳入。
