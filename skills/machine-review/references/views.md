# 审阅视图

按[脚本适配约定](../../machine-design/shared/references/workflow.md#脚本适配)准备项目副本，在交互 Blender 中导入副本的 `review/review_views.py`，调用 `saved = apply_view(objects, 'front-right')`，观察后用 `restore(saved)` 恢复。方向包括 front/back/left/right/top/front-right/back-left。

`plan(objects)` 可在后台返回取景中心和距离，但不能据此声称已看过图像。工具只修改视口状态，不创建相机、不改变对象可见性，也不保存工程；复杂实例需用求值结果补查边界。
