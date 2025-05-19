<div align="center">

# FreeYou - Proactive AI Agent with Seamless Perception

<p align="center">
  <img src="logo/logo15.png" alt="FreeYou Logo" width="200"/>
</p>

<!-- <p align="center">
  <img src="logo/FreeYou.png" alt="FreeYou" width="300"/>
</p> -->

**Comprehensive Perception | Proactive Service | Multimodal Data Interaction | Edge-Cloud Collaboration | Privacy Protection | End-to-End AI Agent**

[English](README_EN.md) • [中文](README.md)

[Quick Start](#-quick-start) • [Core Features](#-core-features) • [Use Cases](#-use-cases) • [Technical Architecture](#-technical-architecture) • [Contribution Guidelines](#-contribution-guidelines)

</div>

## 🌟 Vision

Imagine having a "behind-the-scenes assistant" that quietly observes your needs in your daily work and life, proactively appearing at the right moment to help you complete various tasks without manual activation or input commands. This is FreeYou — an end-to-end AI agent.

## 📖 Project Introduction

FreeYou is an open-source proactive AI agent system that can seamlessly observe the user's environment, understand user intent, and provide intelligent services at the most appropriate time. Unlike traditional passive AI assistants, FreeYou adopts innovative proactive interaction algorithms to monitor user activities in real-time, automatically identify scenarios where users may need assistance, and provide targeted suggestions and solutions.

## ✨ Core Features

### 🔍 Full Perception and Privacy Protection

- **24/7 Perception**: Real-time capture and understanding of multimodal data (text, images, video, etc.) in the user environment
- **Proactive Service Awareness**: Precisely identify scenarios where users need assistance through advanced discrimination algorithms
- **Multimodal Interaction**: Support for processing and analyzing multiple data types including text and images
- **Privacy Protection**: Built-in powerful privacy filtering mechanism that automatically desensitizes sensitive information (such as names, passwords, ID numbers, etc.)

### 🧠 Local and Cloud Integration: Small Brain and Big Brain

- **Edge-Cloud Collaboration**: Combining local models and cloud models to balance privacy protection and processing efficiency
- **Local Model ("Small Brain")**: Provides real-time, low-latency analysis and judgment, protecting private data
- **Cloud Model ("Big Brain")**: Seamlessly connects to cloud large models when stronger reasoning capabilities are needed

### 🚀 Powerful Execution and Extensibility

- **Multiple Solution Suggestions**: Provides multiple solutions for identified problem scenarios for users to choose from
- **Simple Decision-Making**: Only a "Yes" or "No" is needed for FreeYou to complete tedious tasks for you
- **Extension Interfaces**: Easily connect to various executors and third-party APIs to achieve "AI for everything"



## 🔍 Use Cases

### 💻 Work Efficiency Enhancement

- **Document Editing Assistance**: Detect logical errors, mismatches between text and images, and other issues in documents
- **Email Writing Optimization**: Provide multiple reply suggestions to improve communication efficiency
- **Schedule Management**: Automatically identify schedule-related information and provide scheduling suggestions
- **Programming Assistant**: Identify code issues and provide debugging suggestions and solutions

### 🎮 Life and Entertainment

- **Game Assistance**: Identify game scenarios and provide shortcut information and operation suggestions
- **Social Media Interaction**: Determine if reply tone is appropriate and provide improvement suggestions
- **Information Filtering**: Automatically filter and organize important information to reduce information overload

### 🌐 Accessible Experience

- **AI for Everyone**: Allow everyone to enjoy the convenience brought by AI in a user-friendly way
- **No Learning Required**: No need to learn complex operations or frequently input commands
- **Proactive Service**: When FreeYou perceives that you need help, it will proactively pop up the most suitable solution

## 🧠 Technical Architecture

### System Components

- **Perceptor**: Responsible for obtaining multimodal data from the environment and integrating contextual information
- **Discriminator**: Analyzes the current scenario and determines whether to proactively provide services
- **Planner**: Develops service plans for identified problem scenarios
- **Privacy Filter**: Processes sensitive information for desensitization
- **Executor**: Generates and executes specific service suggestions

### Technology Stack

- **Backend**: Python
- **AI Models**: Support for various large language models (LLMs), including:
  - Local Models: Including but not limited to Ollama (DeepSeek), etc.
  - Cloud Models: Configurable API access
- **Image Processing**: BLIP model for image description and understanding
- **OCR Technology**: For extracting text information from images
- **Frontend**: Flask providing API services



## 📊 Usage Examples

### Proactive Service Process

1. The perceptor monitors the user environment in real-time, obtaining screen content and contextual information
2. The discriminator analyzes the current scenario and decides whether to proactively provide services
3. If service is needed, the planner develops a service plan and decides whether to use local or cloud models
4. The privacy filter processes sensitive information for desensitization (if using cloud models)
5. The executor generates multiple service suggestions, waiting for user selection or automatic execution



<p align="center">FreeYou - AI for Everything, Unlocking Infinite Possibilities</p>