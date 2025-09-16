# DeepResearchAgent

[English](README.md) | 简体中文
## 简介

**DeepResearchAgent** 是一个分层多智能体系统，设计目标是处理深度研究任务，同时也适用于通用任务求解。该框架通过顶层规划智能体协调多个专门的子智能体，实现了任务的自动分解与高效执行，适用于多样且复杂的任务场景。

## 系统架构

<p align="center">
  <img src="./docs/assets/architecture.png" alt="Architecture" width="700"/>
</p>

本系统采用两层结构：

### 1. 顶层规划智能体

* 负责理解任务、规划整体流程。
* 将任务分解为子任务并分配给合适的子智能体。
* 动态协调各智能体之间的协作，确保任务顺利完成。

### 2. 专业子智能体

* **深度分析器（Deep Analyzer）**

  * 对输入信息进行深入分析，提取关键信息与潜在需求。
  * 支持文本和结构化数据的分析。
* **深度研究者（Deep Researcher）**

  * 对指定主题或问题进行深度研究，自动获取并整合高质量信息。
  * 可生成研究报告或知识总结。
* **浏览器操作（Browser Use）**

  * 自动化浏览器行为，支持网页搜索、信息提取与数据收集。
  * 为研究者提供实时网页信息支持。

## 主要特性

* 分层协作，适用于复杂和动态任务
* 易于扩展，可集成更多专业智能体
* 支持信息分析、研究与网页交互

## 更新日志
* **2025.07.08**：添加了Image生成工具，该工具可根据输入文本生成图像。图像生成工具基于 Imagen 模型。
* **2025.07.07**：由于TOML文件配置灵活度有限，现改成mmengine支持的config配置。
* **2025.06.20**：支持 MCP 架构，包括本地MCP和远程MCP.
* **2025.06.17**：更新技术报告https://arxiv.org/abs/2506.12508.
* **2025.06.01**：升级 browser-use 至 v0.1.48
* **2025.05.30**：将子智能体调用方式改为函数调用，支持 GPT-4.1 和 Gemini-2.5-Pro 作为规划智能体
* **2025.05.27**：支持 OpenAI、Anthropic、Google LLM，以及本地 Qwen 模型（使用 vLLM）

## TODO 清单

* [x] 异步功能完成
* [x] 图像生成工具已完成
* [x] MCP 架构开发中
* [ ] AI4Research 智能体开发中
* [ ] 小说创作智能体开发中

## 安装说明

### 环境准备

```bash
conda create -n dra python=3.11
conda activate dra
make install

# 或者使用 requirements.txt 安装
conda create -n dra python=3.11
conda activate dra
make install-requirements

# 安装 playwright 以启用浏览器支持
pip install playwright
playwright install chromium --with-deps --no-shell
```

### 设置 `.env` 文件

请参考 `.env.template` 文件，在项目根目录创建 `.env` 文件。该文件用于配置 API 密钥和其他环境变量。

如需使用 Google 模型：
* 获取 API Key：[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
* 获取 application\_default\_credentials.json：

```bash
brew install --cask google-cloud-sdk
gcloud init
gcloud auth application-default login
```

## 使用说明

### 示例 1：运行主示例
这是一个简单的示例，演示如何使用 DeepResearchAgent 框架。
```bash
python main.py
```

### 示例 2：运行单智能体
一个简单示例，用于演示单一Agent的用法，比如一个能够调用通用工具的Agent。

```bash
python examples/run_general.py
```

### 示例 2：评估 GAIA 数据集

```bash
mkdir data && cd data
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA
python examples/run_gaia.py
```

## 实验结果

我们在 GAIA 验证集上进行了评估，并于 5 月 10 日达到最先进性能：

<p align="center">
  <img src="./docs/assets/gaia_benchmark.png" alt="GAIA Example Result" width="700"/>
</p>

## 常见问题

### 1. 如何使用本地 Qwen 模型？

支持以下模型：

* qwen2.5-7b-instruct
* qwen2.5-14b-instruct
* qwen2.5-32b-instruct

配置：

```toml
model_id = "qwen2.5-7b-instruct"
```

### 2. 浏览器模块安装问题？

```bash
pip install "browser-use[memory]"==0.1.48
pip install playwright
playwright install chromium --with-deps --no-shell
```

### 3. 子智能体函数调用不生效？

推荐使用 Claude-3.7-Sonnet 作为规划智能体，现已兼容 GPT-4.1 和 Gemini-2.5-Pro。

### 4. 使用 vllm 进行本地模型部署
我们提供 huggingface 作为加载本地模型的快捷方式。我们还提供 vllm 作为启动服务的方式，以便提供并行加速。

### 部署本地 Qwen 模型（使用 vLLM）

#### 第一步：启动 vLLM 服务

```bash
nohup bash -c 'CUDA_VISIBLE_DEVICES=0,1 python -m vllm.entrypoints.openai.api_server \
  --model /input0/Qwen3-32B \
  --served-model-name Qwen \
  --host 0.0.0.0 \
  --port 8000 \
  --max-num-seqs 16 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --tensor_parallel_size 2' > vllm_qwen.log 2>&1 &
```

`.env` 文件配置：

```bash
QWEN_API_BASE=http://localhost:8000/v1
QWEN_API_KEY="abc"
```

#### 第二步：启动智能体服务

```bash
python main.py
```

输入任务命令示例：

```bash
Use deep_researcher_agent to search the latest papers on the topic of 'AI Agent' and then summarize it.
```

## 致谢

DeepResearchAgent 主要借鉴了 smolagents 的架构设计，并在此基础上做出了以下改进：
- 对 smolagents 的代码进行了模块化重构，使其结构更加清晰和易于维护。
- 将原有的同步执行框架改为异步执行框架。
- 优化了多智能体的初始化与部署流程，使其更加高效且易用。

我们由衷感谢以下开源项目对本项目的重要贡献：
- [smolagents](https://github.com/huggingface/smolagents) - 轻量级智能体框架。
- [OpenManus](https://github.com/mannaandpoem/OpenManus) - 异步智能体框架。
- [browser-use](https://github.com/browser-use/browser-use) - 基于 AI 的浏览器自动化工具。
- [crawl4ai](https://github.com/unclecode/crawl4ai) - 面向 AI 应用的网页爬取库。
- [markitdown](https://github.com/microsoft/markitdown) - 文件转 Markdown 工具。

我们由衷感谢上述项目的所有贡献者和维护者，感谢他们推动 AI 技术进步并将其开放给社区使用。

## 贡献

欢迎任何形式的贡献！欢迎提 issue 或提交 PR。

## 引用

```bibtex
@misc{zhang2025agentorchestrahierarchicalmultiagentframework,
      title={AgentOrchestra: A Hierarchical Multi-Agent Framework for General-Purpose Task Solving}, 
      author={Wentao Zhang, Liang Zeng, Yuzhen Xiao, Yongcong Li, Ce Cui, Yilei Zhao, Rui Hu, Yang Liu, Yahui Zhou, Bo An},
      year={2025},
      eprint={2506.12508},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2506.12508}, 
}
```
