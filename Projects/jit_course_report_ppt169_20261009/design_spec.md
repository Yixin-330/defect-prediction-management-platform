# 即时软件缺陷预测系统阶段汇报 - Design Spec
## I. Project Information
- Project Name: 即时软件缺陷预测系统阶段汇报
- Page Count: 8
- Target Audience: 高校软件工程课程师生
- Use Case: 10分钟以内课程阶段汇报
- Content Strategy: 保留用户标题、页面顺序、表格全部条目和关键事实。讲稿补充写入备注。建议用时共8分40秒。
- Created Date: 2026-10-09
## II. Canvas Specification
- Format: PPT 16:9
- Dimensions: 1280 × 720
- Margins: 左右64，上下48
## III. Visual Theme
- Mode: custom，遵循用户阶段汇报结构
- Visual style: swiss-minimal
- Theme: Light
- Colors: 白#FFFFFF，浅底#F3F6FA，主色#18324F，强调#2166AC，正文#263444，辅助#617286，线#D4DEE8
## IV. Typography Plan
- Font stacks: "Microsoft YaHei", Arial, sans-serif
- Cover: 52px；Title: 40px；Body: 24px；Annotation: 20px
- Formula policy: text-only，内容无公式
- PPTX fonts: Microsoft YaHei，Windows已安装
## V. Layout Guidelines
- 平整表格、左右分栏、简洁关系图和双层流程，按内容调整布局
- 封面仅用户给出的标题、副标题、阶段说明和成员，留足空白
- 无不必要的动画或装饰
## VI. Icon Usage
- 无图标
## VII. Visualization Reference List
- P02: 完整六步产品流程，原生可编辑
- P04: 五模块架构及用户，原生可编辑
- P05: 离线与在线两条流程，原生可编辑
- P02、P03、P06、P07、P08: 原生表格
## VIII. Image Resource List
- P03: placeholder。右半页有意预留1张主要成果截图或2张裁剪截图，不制作虚假证据
- 当前目录没有真实截图，后续可由用户替换占位区域
## IX. Content Outline
| Page | Title | Core Message | Content / Visual | Rhythm | Time |
|---|---|---|---|---|---|
| P01 | 即时软件缺陷预测系统阶段汇报 | 已完成设计阶段工作 | 极简封面 | anchor | 20秒 |
| P02 | 产品定位与产品主线 | 面向课程团队提供提交风险与审查辅助 | 定位、三类用户表、六步流程 | dense | 80秒 |
| P03 | 已完成工作与成果展示 | 四项设计形成开发依据 | 左侧四行表、右侧截图区 | dense | 60秒 |
| P04 | 技术架构：用户使用系统 | 后端连接数据、特征处理与预测 | 五模块可编辑关系图 | dense | 70秒 |
| P05 | 技术架构：模型训练与在线预测 | 提前训练、在线调用，共用特征规则 | 上下两条四步流程 | breathing | 70秒 |
| P06 | 小组分工与模块责任 | 四名成员主责明确 | 三列四行表格 | dense | 60秒 |
| P07 | 当前问题与应对计划 | 四项待解决或验证事项都有行动 | 三列四行表格 | dense | 80秒 |
| P08 | 下一步计划与阶段交付 | 先跑通首个可用流程再验证适用性 | 按顺序四阶段表和结束语 | anchor | 80秒 |
## X. Speaker Notes Guidelines
- 写入完整中文讲述提示与建议用时
- P06备注包含技能侧重与两类评估指标名称
- 解释架构图关系，强调计划不代表已实现
- SZZ只用于历史训练与评估，在线不用等未来修复结果
## XI. Technical Constraints
- SVG主代理逐页手写，逐页读取spec_lock
- 最终使用Artifact Tool创建可编辑PPTX，表格和图示保持可编辑
- 渲染8页逐页检查，再运行PPTX包、布局、字体及原生表格校验
