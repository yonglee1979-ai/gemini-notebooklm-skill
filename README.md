Gemini NotebookLM Skill
用于在用户明确授权的前提下，通过已登录的 Chrome 会话完成 Gemini Notebook（NotebookLM）的阅读、分析、演示文稿生成、下载与交付。

能力范围
阅读指定 Notebook 的来源、对话和 Studio 产物，并区分原始来源与模型总结。
基于用户指定的 PDF：先生成指定页数的演示大纲，再在 Studio 中生成统一风格的演示文稿。
下载并核验演示文稿的格式、页数和代表性页面。
仅在用户明确授权时，使用 notebooklmwatermark.com/zh 对 NotebookLM 导出的 PDF 做本地浏览器处理，并交付处理后的 PDF。
使用边界
只访问、读取或修改用户明确指定的 Notebook 和文件。
不分享、删除、上传或生成云端内容，除非用户明确提出。
不将 NotebookLM 的 PDF 去水印描述为可编辑 PPTX 去水印；该流程的产物是 PDF。
所有医学、科研或商业内容在正式使用前应由领域专家复核。
安装
将本目录复制到 Codex 的技能目录：

text
复制
~/.codex/skills/gemini-notebooklm/
目录至少应包含：

text
复制
gemini-notebooklm/
├── SKILL.md
└── agents/
    └── openai.yaml
安装后，在涉及 Gemini Notebook 或 NotebookLM 的明确请求中即可调用该技能。

典型请求
打开指定 Notebook，全面阅读其中的 PDF，并基于文献先生成 20 页大纲，再在 Studio 中制作统一白底的中文演示文稿；下载 PDF 并在我授权的去水印网站处理后交付。

隐私说明
本仓库不包含个人账号、邮箱、Notebook 标题、源文件、会话内容、浏览器配置或凭据。实际操作依赖用户自己的已登录浏览器会话和明确授权。

许可
请根据你的组织或项目要求添加适用许可证。
