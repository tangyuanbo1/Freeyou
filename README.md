<div align="center">

# FreeYou - 全域感知AI主动服务智能体

<p align="center">
  <img src="logo/logo15.png" alt="Free Logo" width="200"/>
</p>

<!-- <p align="center">
  <img src="logo/FreeYou.png" alt="FreeYou" width="300"/>
</p> -->

**全量感知 | 主动服务 | 多模态数据交互 | 边云协同 | 隐私保护 | 打通全流程的AI智能体**

[English](README_EN.md) • [中文](README.md)

[快速开始](#-快速开始) • [核心特性](#-核心特性) • [应用场景](#-应用场景) • [技术架构](#-技术架构) • [贡献指南](#-贡献指南)

</div>

## 🌟 项目愿景

想象一下，在日常工作和生活中，你不需要手动唤醒或输入指令，就有一个"幕后助手"静静观察你的需求，在合适的时机主动出现，帮你完成各种琐碎或复杂的任务。这就是 FreeYou —— 一个打通全流程的 AI 智能体。

## 📖 项目简介

FreeYou是一个开源的AI主动服务智能体系统，它能够无感知地观察用户环境，理解用户意图，并在最恰当的时机提供智能服务。不同于传统的被动式AI助手，FreeYou采用创新的主动交互算法，能够实时监控用户活动，自动识别用户可能需要帮助的场景，并提供针对性的建议和解决方案。

## ✨ 核心特性

### 🔍 全量感知与隐私保护

- **全天候感知**：实时捕获并理解用户环境中的多模态数据（文本、图像、视频等）
- **主动服务意识**：通过先进的判别算法，精确识别用户需要帮助的场景
- **多模态交互**：支持文本、图像等多种数据类型的处理和分析
- **隐私保护**：内置强大的隐私过滤机制，自动对敏感信息（如人名、密码、证件号等）进行脱敏与保护

### 🧠 本地与云端结合的小脑与大脑

- **边云协同**：结合本地模型和云端模型，平衡隐私保护与处理效率
- **本地模型（"小脑"）**：提供实时、低延迟的分析与判断，保护私有数据
- **云端模型（"大脑"）**：在需要更强大推理能力时，无缝衔接云端大模型

### 🚀 强大的执行力与扩展性

- **多方案建议**：针对识别出的问题场景，提供多种解决方案供用户选择
- **简单决策**：只需一个"Yes"或"No"，FreeYou便能替你完成繁琐的任务
- **扩展接口**：轻松接入各种执行器和第三方API，实现"AI for everything"



## 🔍 应用场景

### 💻 工作效率提升

- **文档编辑辅助**：检测文档中的逻辑错误、图文不匹配等问题
- **邮件撰写优化**：提供多种回复方式建议，提升沟通效率
- **日程管理**：自动识别与日程相关的信息，提供日程安排建议
- **编程助手**：识别代码问题，提供调试建议和解决方案

### 🎮 生活与娱乐

- **游戏辅助**：识别游戏场景，提供快捷键信息和操作建议
- **社交媒体互动**：判断回复语气是否得体，提供改进建议
- **信息筛选**：自动过滤和整理重要信息，减轻信息过载

### 🌐 无障碍体验

- **AI for Everyone**：让所有人都能傻瓜式地享受AI带来的便利
- **无需学习**：不需要学习复杂的操作，也不需要频繁输入指令
- **主动服务**：当FreeYou感知到你需要帮助时，它会主动弹出最适合的方案

## 🧠 技术架构

### 系统组件

- **感知器(Perceptor)**：负责从环境中获取多模态数据并整合上下文信息
- **判别器(Discriminator)**：分析当前场景，判断是否需要主动提供服务
- **规划器(Planner)**：为识别出的问题场景制定服务计划
- **隐私过滤器(PrivacyFilter)**：对敏感信息进行脱敏处理
- **执行器(Executor)**：生成并执行具体的服务建议

### 技术栈

- **后端**：Python
- **AI模型**：支持多种大型语言模型(LLM)，包括：
  - 本地模型：包括但不限于Ollama（DeepSeek）等
  - 云端模型：可配置API接入
- **图像处理**：BLIP模型用于图像描述和理解
- **OCR技术**：用于从图像中提取文本信息
- **前端**：Flask提供API服务



## 📊 使用示例

### 主动服务流程

1. 感知器实时监控用户环境，获取屏幕内容和上下文信息
2. 判别器分析当前场景，决定是否需要主动提供服务
3. 如需服务，规划器制定服务计划，决定使用本地还是云端模型
4. 隐私过滤器对敏感信息进行脱敏处理（如使用云端模型）
5. 执行器生成多个服务建议，等待用户选择或自动执行


<p align="center">FreeYou -  AI 感知万物，智启无限可能</p>