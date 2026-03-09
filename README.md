# 🖥️ JustRunMy 自动续期多账号版

> **本项目通过 GitHub Actions 实现 JustRunMy.app 服务的全自动续期。依托动态矩阵技术，实现“零侵入”封装，支持多账号无限扩展。**

---

【 🚀 项目简介 】
基于 GitHub Actions 自动化工作流，利用模拟点击技术绕过 Cloudflare 
验证。支持多账号并发执行，无需修改任何代码即可实现账号动态增减。

【 🛠️ 环境变量配置 (Secrets) 】
请前往仓库 [Settings] -> [Secrets and variables] -> [Actions]
依次添加以下加密变量：

| 变量类型 | 变量名 (Name) | 示例值 (Value) |
| :--- | :--- | :--- |
| **通知 ID（可选）** | TG_ID | 987654321 |
| **通知 Token（可选）** | TG_TOKEN | 123456:ABC-DEF... |
| **账号邮箱** | EML_1, EML_2, EML_3... | user@example.com |
| **账号密码** | PWD_1, PWD_2, PWD_3... | your_password |

### 总结如下图
<img width="1391" height="766" alt="image" src="https://github.com/user-attachments/assets/b4e2c333-1a8c-4e12-8164-f2b53a20f20f" />


【 🔄 运行逻辑 】
- 🔍 智能扫描：自动解析 Secrets 中所有以 "EML_" 开头的配置。
- 🎭 独立环境：每个账号任务运行在独立的隔离虚拟机中，互不干扰。
- 🖱️ 物理模拟：启动 Xvfb 虚拟桌面，模拟真实鼠标轨迹，强效绕过 CF 验证。
- 📱 实时反馈：续期任务结束后，通过 Telegram 机器人即时推送剩余时长。

【 ⚡ 快速开始 】
1. Fork 本项目：点选右上角 [Fork] 将代码同步至个人仓库。
2. 配置密钥：按照上方说明在仓库 Secrets 中填入你的账号信息。
3. 激活行动：进入 [Actions] 页面，选择工作流并点击 "Run workflow"。
4. 周期运行：系统默认设置为 [每 2 天运行一次]，实现无感续期。

【 ⚠️ 调试与报错 】
若 Actions 运行失败，请在当前任务页面的底端 [Artifacts] 区域
下载名为 "debug-acc-X" 的压缩包，查看浏览器报错截图。
============================================================

## 【 🌟 特别鸣谢 】
本项目核心续期逻辑参考并使用了以下开源项目：
👉 原作者项目: [https://github.com/mangguo88/JustRunMy-Renew](https://github.com/mangguo88/JustRunMy-Renew)
在此特别感谢 mangguo88 提供的稳定物理模拟续期算法。
