# 提取清单与工具

先按[文件位置约定](../../machine-design/shared/references/workflow.md#文件位置)确定目标项目。以下路径均为示例，替换为技能实际安装位置、来源包和项目路径；命令可从任意目录运行。Python 3.10+，仅裁切图片时需要安装本技能 `requirements.txt` 中的依赖。

```sh
python3 "/path/to/installed-skills/mod-resource-extract/scripts/extract_resources.py" \
  --archive "/path/to/downloads/mod.jar" \
  --manifest "/path/to/project/assets/resources/extraction.json" \
  --output "/path/to/project/assets/resources/example-mod/1.0"
```

清单为版本 1 JSON：

| 字段 | 内容 |
| --- | --- |
| `archive_sha256` | 实际输入包的 SHA-256 |
| `usage_status` | 执行前已按本轮用途核查时为 `confirmed`；工具不判断协议 |
| `usage_scope` | 具体用途、改动及交付方式 |
| `permission_evidence` | 固定版本协议／说明的位置及本用途对应依据；不只有一个无说明的“允许” |
| `entries` | 包内文件，每项为 `source`、`output`、`sha256`，可选 `crop` |
| `notice_files` | 可选包外协议／署名文件，每项为 `source`、`output`、`sha256`；source 相对于清单目录或为绝对路径 |
| `notice_outputs` | 已列入 entries 或 notice_files 的协议及署名输出路径，至少一项 |

可附 `source` 记录模组、版本、官方地址或提交号，`interfaces` 记录网格／UV／贴图关系、安装坐标系和用途；工具保留这些字段，不推导其语义。`entries` 中 source 为 ZIP 内相对路径，output 为输出目录内相对路径；`crop: [x0,y0,x1,y1]` 使用左上原点、右下不含边界，输出 PNG。包外声明只复制原字节，不裁切或改写。

原始协议文件没有固定文件夹要求，可按来源放在 LICENSE、NOTICE 或 notices/ 内；记录必须指向随输出实际存在的文件。包外声明需能对应固定版本来源，而非直接套用上游当前分支协议。不能用生成的摘要替代原文。

输出必须为新目录，拒绝覆盖。包内条目与包外声明合计最多 512 项，单项最多 64 MiB；核验来源哈希后写入，`resource-record.json` 保留清单与每项实际输出哈希。缺少适用声明时先解决来源缺口，不伪造文件以通过校验。输出路径由项目管理，不默认存入技能目录；旧提取结果通过项目索引复用，无需重新提取。
