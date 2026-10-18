# 提取清单与工具

先按[文件位置约定](../../machine-design/shared/references/workflow.md#文件位置)确定目标项目，再按[脚本适配约定](../../machine-design/shared/references/workflow.md#脚本适配)准备调用。将以下示例路径替换为项目脚本副本、来源包和项目路径后，命令可从任意目录运行。需要 Python 3.10+；仅在裁切图片时，需要安装项目工具副本 `resources/requirements.txt` 中的依赖。

```sh
python3 "/path/to/project/tools/machine-design/resources/extract_resources.py" \
  --archive "/path/to/downloads/mod.jar" \
  --manifest "/path/to/project/assets/resources/extraction.json" \
  --output "/path/to/project/assets/resources/example-mod/1.0"
```

清单为版本 1 JSON：

| 字段 | 内容 |
| --- | --- |
| `archive_sha256` | 实际输入包的 SHA-256 |
| `usage_status` | 依[授权确认规则](../../machine-design/shared/references/material-permissions.md)完成适用许可核查和必要的用户用途确认后，设为 `confirmed`；工具不判断协议 |
| `usage_scope` | 具体用途、改动及交付方式 |
| `permission_evidence` | 固定版本协议／说明的位置、本用途的许可依据，以及必要的当前会话用途确认或另行授权证据；写明依据，不只填写“允许” |
| `entries` | 包内文件，每项为 `source`、`output`、`sha256`，可选 `crop` |
| `notice_files` | 可选的包外协议／署名文件，每项为 `source`、`output`、`sha256`；`source` 相对于清单所在目录，或使用绝对路径 |
| `notice_outputs` | 已列入 `entries` 或 `notice_files` 的协议及署名输出路径，至少一项 |

可附 `source` 记录模组、版本、官方地址或提交号，用 `interfaces` 记录网格／UV／贴图关系、安装坐标系和用途；工具保留这些字段，不推导其语义。

`entries` 中的 `source` 为 ZIP 内相对路径，`output` 为输出目录内相对路径。`crop: [x0,y0,x1,y1]` 以左上角为原点，不包含右下边界，裁切结果输出为 PNG。包外声明只复制原字节，不裁切或改写。

原始协议文件没有固定目录要求，可按来源命名为 `LICENSE`、`NOTICE`，或放入 `notices/` 目录；记录必须指向随输出实际存在的文件。包外声明需能对应固定版本来源，而非直接套用上游当前分支协议。不能用生成的摘要替代原文。

输出必须为新目录，工具拒绝覆盖。包内条目与包外声明合计最多 512 项，单项最多 64 MiB。工具核验来源哈希后写入，`resource-record.json` 保留清单与每项实际输出哈希。缺少适用声明时，先解决来源缺口，不伪造文件以通过校验。

输出路径由项目管理，不默认存入技能目录；通过项目索引复用旧提取结果，无需重新提取。
