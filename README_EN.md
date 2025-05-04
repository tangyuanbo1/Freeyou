<div align="center">

# FreeYou - Proactive AI Agent with Seamless Perception

<p align="center">
  <img src="logo/logo.svg" alt="FreeYou Logo" width="200"/>
</p>

<p align="center">
  <img src="logo/FreeYou.png" alt="FreeYou" width="300"/>
</p>

**End-to-end AI Agent | Seamless Proactive Interaction | Complete Privacy Protection | Local-Cloud Collaboration**

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

<div align="center">

<!-- Insert feature showcase image here -->
*Core Feature Showcase*

</div>

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

<div align="center">

<!-- Insert architecture diagram here -->
*System Architecture Diagram*

</div>

## 🚀 Quick Start

### Requirements

- Python 3.8+
- Sufficient GPU memory (recommended for local models)

### Installation Steps

1. Clone the repository

```bash
git clone https://github.com/yourusername/FreeYou.git
cd FreeYou
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure models

Edit the `config.config` file to configure local or cloud model API information:

```json
{
  "api_config": {
    "CLOUD_API_KEY": "your_cloud_api_key",
    "CLOUD_API_BASE": "https://api.example.com/v1",
    "DEFAULT_CLOUD_MODEL": "model_name",
    "LOCAL_API_KEY": "your_local_api_key",
    "LOCAL_API_BASE": "http://localhost:11434/v1",
    "LOCAL_MODEL_NAME": "your_local_model_name"
  }
}
```

4. Start the service

```bash
python app.py
```

## 📊 Usage Examples

### Proactive Service Process

1. The perceptor monitors the user environment in real-time, obtaining screen content and contextual information
2. The discriminator analyzes the current scenario and decides whether to proactively provide services
3. If service is needed, the planner develops a service plan and decides whether to use local or cloud models
4. The privacy filter processes sensitive information for desensitization (if using cloud models)
5. The executor generates multiple service suggestions, waiting for user selection or automatic execution

### API Call Example

```python
import requests

# Get current service status
response = requests.get('http://localhost:5000/items/')
print(response.json())
```

## 🤝 Contribution Guidelines

We welcome various forms of contributions, including but not limited to:

- Submitting issues and feature requests
- Submitting code improvements
- Improving documentation
- Sharing use cases

Please follow these steps:

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🤝 Open Source Community

<div align="center">

### Join our Feishu Community

Scan the QR code below to join the FreeYou open source community and exchange experiences with other developers!

<p align="center">
  <img src="pic/feishu.jpg" alt="Feishu Community QR Code" width="200"/>
</p>

*Scan the QR code to join the discussion group*

</div>

## 📞 Contact Information

- Project Maintainer: [Your Name](mailto:your.email@example.com)
- Project Homepage: [GitHub](https://github.com/yourusername/FreeYou)

---

<p align="center">FreeYou - AI for Everything, Unlocking Infinite Possibilities</p>