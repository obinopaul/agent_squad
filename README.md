# Agent Squad

Welcome to the Agent Squad repository, a collection of advanced AI agent projects designed for a variety of tasks, from deep research and software engineering to video manipulation and real-time voice interaction. This repository serves as a showcase and development hub for cutting-edge agentic workflows and applications.

## 🚀 Overview

This repository is structured as a monorepo containing multiple, independent yet related projects. Each project is a standalone application or library that demonstrates a specific aspect of AI agent development. The projects are organized into top-level directories, with larger, more complex projects residing in the `1. projects/` directory.

## 📂 Projects

Here is a summary of the main projects in this repository:

###  комплексные проекты (`1. projects/`)

This directory contains a collection of large, standalone agent-based projects.

| Project | Description |
| --- | --- |
| [**Deep Research**](./1.%20projects/deep_research/) | A full-stack LangGraph application for deep research, featuring a React frontend and a Gemini-powered agent that can dynamically generate search terms, query the web, and synthesize well-supported answers with citations. |
| [**DeepResearchAgent**](./1.%20projects/DeepResearchAgent/) | A hierarchical multi-agent system designed for deep research and general-purpose task solving. It uses a top-level planning agent to coordinate multiple specialized lower-level agents. |
| [**DeepVideoDiscovery**](./1.%20projects/DeepVideoDiscovery/) | An agentic search system for understanding long-form video content. It treats video clips as an environment to be explored, allowing the agent to autonomously plan, reason, and use tools to answer complex queries about video content. |
| [**Director**](./1.%20projects/Director/) | A framework for building video agents that can reason through complex video tasks like search, editing, compilation, and generation. It provides a chat-based interface to interact with a media library and orchestrate various video-related agents. |
| [**Open Deep Research**](./1.%20projects/open_deep_research/) | A configurable, fully open-source deep research agent built with LangGraph. It supports a wide range of model providers, search tools, and MCP servers, and is designed for high performance on deep research benchmarks. |
| [**Open SWE**](./1.%20projects/open-swe/) | An open-source, asynchronous coding agent that autonomously understands codebases, plans solutions, and executes code changes across entire repositories, from initial planning to opening pull requests. |
| [**Suna (Kortix)**](./1.%20projects/suna/) | An open-source platform to build, manage, and train AI agents. It includes Suna, a flagship generalist AI worker that can handle research, data analysis, browser automation, and more. |

### Шаблоны и библиотеки

| Project | Description |
| --- | --- |
| [**FastAPI LangGraph Template**](./fastapi-langgraph-template/) | A production-ready FastAPI template for building AI agent applications with LangGraph integration. It includes features like JWT authentication, rate limiting, structured logging, and monitoring with Prometheus and Grafana. |
| [**LangSmart-BigTool**](./langsmart-bigtool/) | A Python library for creating LangGraph agents that can intelligently select and use tools from large tool registries. It uses a two-stage LLM-driven architecture to replace traditional RAG-based tool retrieval. |
| [**Voice Agents**](./voice_agents/langgraph-voice-call-agent/) | A real-time voice/call AI agent that lets you talk to a LangGraph agent over LiveKit, similar to "voice mode" experiences in ChatGPT Voice and Gemini Live. |

### Другие компоненты

The repository also contains several other directories with smaller utilities, examples, and components that support the main projects:

-   `ambient_agent/`: A simple agent that runs in the background.
-   `deepagents/`: A collection of deep learning-based agents.
-   `langgraph-components/`: Reusable components for building LangGraph applications.
-   `reactagent/`: An agent built with the ReAct (Reasoning and Acting) paradigm.
-   `sandbox/`: A directory for testing and experimentation.
-   `sub_agent/`: A smaller, more focused agent.
-   `supervisoragents/`: Agents designed to oversee and manage other agents.
-   `swarmagents/`: A collection of agents that work together in a swarm.

## 🎯 Getting Started

To get started with a specific project, please navigate to its directory and follow the instructions in its `README.md` file.

## 🤝 Contributing

Contributions are welcome! If you would like to contribute to a project, please see the `CONTRIBUTING.md` file in the respective project's directory. If a project does not have a `CONTRIBUTING.md` file, please feel free to open an issue or pull request.

## 📄 License

Each project in this repository has its own license. Please see the `LICENSE` file in each project's directory for more information. If a project does not have a `LICENSE` file, it is assumed to be under the same license as the root repository.
