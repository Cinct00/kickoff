# Catalog

Generated 2026-11-02 by `python3 scripts/toolkit.py catalog`. Do not edit by hand.

Status: **own** = in this repo · **active** = in your profile (`toolkit.json` → `upstream.profile`) · available = installable from that marketplace.

Machine-readable versions: [`index.json`](index.json) and the kickoff skill's [`catalog.tsv`](../plugins/kickoff/skills/kickoff/references/catalog.tsv).

## kickoff

`Cinct00/kickoff` · Cinct00 · trust: own

| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |
|---|---|---|---|---|---|---|---|
| `codemap` | **own** | 2 | 1 | 0 | SessionStart | codemap | Token-efficient repository map and change review: a SQLite index of symbols, imports, references and packages with a ranked repo map, search, outlines, exact s… |
| `communication-and-leadership` | **own** | 7 | 0 | 0 | — | — | Skills for writing, teaching, presenting, persuading, hard conversations, meetings and leading a team. |
| `doc-coauthor` | **own** | 1 | 3 | 0 | — | — | Three-stage document co-authoring (context, draft, reader-simulation review) with isolated sub-agents. For RFCs, PRDs, decision docs, architecture specs and pr… |
| `engineering-craft` | **own** | 11 | 0 | 0 | — | — | Judgment skills for software work: understanding the problem, scoping, implementing, exploring code, architecture, debugging, testing, reviewing, refactoring,… |
| `kickoff` | **own** | 3 | 1 | 0 | SessionStart, Stop | — | The router. Classifies a task, loads the right skills, agents and plugin commands on whatever platform you are on, checks the catalog for gaps and existing plu… |
| `thinking-tools` | **own** | 10 | 0 | 0 | — | — | Reasoning skills: first principles, systems thinking, probabilistic thinking, decisions, creativity, maths, scientific method, evaluating information and resea… |

## claude-plugins-official

`anthropics/claude-plugins-official` · Anthropic · trust: official

| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |
|---|---|---|---|---|---|---|---|
| `claude-code-setup` | **active** | 1 | 0 | 0 | — | — | Analyze codebases and recommend tailored Claude Code automations such as hooks, skills, MCP servers, and subagents. |
| `claude-md-management` | **active** | 1 | 0 | 1 | — | — | Tools to maintain and improve CLAUDE.md files - audit quality, capture session learnings, and keep project memory current. |
| `claude-security` | **active** | 1 | 9 | 0 | PermissionRequest, PostToolUse, PostToolUseFailure, UserPromptExpansion | — | Deep vulnerability scanning of your own code, run entirely inside your Claude Code session at a chosen effort tier, with every finding challenged before it is… |
| `code-modernization` | **active** | 0 | 8 | 13 | PostToolUseFailure, SessionStart, Stop, StopFailure, UserPromptSubmit | — | Guided modernization for any legacy codebase: start with /modernize, get an assessment, an interactive map, the business rules mined from the code, and a plan… |
| `code-review` | **active** | 0 | 0 | 1 | — | — | Automated code review for pull requests using multiple specialized agents with confidence-based scoring to filter false positives |
| `code-simplifier` | **active** | 0 | 1 | 0 | — | — | Agent that simplifies and refines code for clarity, consistency, and maintainability while preserving functionality. Focuses on recently modified code. |
| `feature-dev` | **active** | 0 | 3 | 1 | — | — | Comprehensive feature development workflow with specialized agents for codebase exploration, architecture design, and quality review |
| `frontend-design` | **active** | 1 | 0 | 0 | — | — | Create distinctive, production-grade frontend interfaces with high design quality. Generates creative, polished code that avoids generic AI aesthetics. |
| `hookify` | **active** | 1 | 1 | 4 | PostToolUse, PreToolUse, Stop, UserPromptSubmit | — | Easily create custom hooks to prevent unwanted behaviors by analyzing conversation patterns or from explicit instructions. Define rules via simple markdown fil… |
| `learn-with-coursera` | **active** | 1 | 0 | 0 | — | — | Turn any learning intent into a personalized Coursera experience. Asks three quick questions (topic, familiarity, preferred format), searches Coursera's catalo… |
| `modern-web-guidance` | **active** | 2 | 0 | 0 | — | — | Keep your coding agent up to date with the latest web best practices |
| `playground` | **active** | 1 | 0 | 0 | — | — | Creates interactive HTML playgrounds — self-contained single-file explorers with visual controls, live preview, and prompt output with copy button. Includes te… |
| `pr-review-toolkit` | **active** | 0 | 6 | 1 | — | — | Comprehensive PR review agents specializing in comments, tests, error handling, type design, code quality, and code simplification |
| `ralph-loop` | **active** | 0 | 0 | 3 | Stop | — | Interactive self-referential AI loops for iterative development, implementing the Ralph Wiggum technique. Claude works on the same task repeatedly, seeing its… |
| `security-guidance` | **active** | 0 | 0 | 0 | PostToolUse, SessionStart, Stop, UserPromptSubmit | — | Security review for Claude-generated code. Pattern-based warnings on edits, LLM-powered diff review on Stop, and an agentic commit reviewer that catches inject… |
| `skill-creator` | **active** | 1 | 0 | 0 | — | — | Create new skills, improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing s… |
| `42crunch-api-security-testing` | available | 0 | 0 | 0 | — | — | Automate API security directly in Claude Code with 42Crunch - automatically audit OpenAPI specs, detect vulnerabilities aligned with OWASP API Security risks (… |
| `activecampaign` | available | 0 | 0 | 0 | — | — | Marketing automation, CRM, and email marketing powered by ActiveCampaign. Manage contacts, campaigns, automations, deals, and get AI-powered marketing insights… |
| `adobe-for-creativity` | available | 0 | 0 | 0 | — | — | Harness Adobe's creative AI-powered tools to edit images, automate design workflows, and bring creative visions to life — from background removal to vectorizat… |
| `agent-sdk-dev` | available | 0 | 2 | 1 | — | — | Development kit for working with the Claude Agent SDK |
| `agentforce-adlc` | available | 0 | 0 | 0 | — | — | Agentforce Agent Development Life Cycle — author, discover, scaffold, deploy, test, and optimize .agent files |
| `ai-plugins` | available | 0 | 0 | 0 | — | — | Set up endorctl and use Endor Labs to scan, prioritize, and fix security risks across your software supply chain |
| `aikido` | available | 0 | 0 | 0 | — | — | Aikido Security scanning for Claude Code — SAST, secrets, and IaC vulnerability detection powered by the Aikido MCP server. |
| `airtable` | available | 0 | 0 | 0 | — | — | Airtable is the database and operations layer for your agents — whether running product, marketing, sales, ops, HR, or a custom business app. It combines struc… |
| `airwallex-agentos` | available | 0 | 0 | 0 | — | — | Bring Airwallex's global financial infrastructure to Claude. Orchestrate actions across your account in plain language, e.g., set up invoices from a PO, onboar… |
| `airwallex-dev` | available | 0 | 0 | 0 | — | — | Build Airwallex payment integrations in your own codebase. Generates the checkout, card-element, onboarding, and subscription-billing code for an Airwallex int… |
| `aiven` | available | 0 | 0 | 0 | — | — | Easily deploy managed PostgreSQL (pg), Kafka, OpenSearch, Clickhouse and other databases, streaming and apps. Free tier available, up and running in minutes. |
| `alloydb` | available | 0 | 0 | 0 | — | — | Create, connect, and interact with an AlloyDB for PostgreSQL database and data. |
| `alloydb-omni` | available | 0 | 0 | 0 | — | — | Create, connect, and interact with an AlloyDB Omni database and data. |
| `altimate-code` | available | 0 | 0 | 0 | — | — | Delegates dbt and warehouse work to altimate-code, a specialized CLI agent with 100+ purpose-built data tools (SQL analysis, column-level lineage, dbt build/te… |
| `amazon-location-service` | available | 0 | 0 | 0 | — | — | Guide developers through adding maps, places search, geocoding, routing, and other geospatial features with Amazon Location Service, including authentication s… |
| `amazon-selling-partner` | available | 0 | 0 | 0 | — | — | Connect your Amazon Seller Central account to Claude. Ask about sales, inventory, and listing performance and get recommendations grounded in your own data, th… |
| `amd-skills` | available | 0 | 0 | 0 | — | — | AMD's verified Agent Skills in one plugin: route image/audio through local AI on Ryzen AI, serve LLMs on AMD Instinct GPUs with vLLM, optimize inference throug… |
| `amplitude` | available | 0 | 0 | 0 | — | — | Use Amplitude as an expert analyst — instrument Amplitude, discover product opportunities, analyze charts, create dashboards, manage experiments, and understan… |
| `apollo` | available | 0 | 0 | 0 | — | — | Prospect, enrich leads, load outreach sequences, and query sales analytics with Apollo.io — one-click MCP server integration for Claude Code and Cowork. |
| `apollo-skills` | available | 0 | 0 | 0 | — | — | Apollo GraphQL agent skills for Claude Code — Apollo Client, Server, Federation, Connectors, Router, Rover CLI, iOS, Kotlin, and the Apollo MCP server. Covers… |
| `appwrite` | available | 0 | 0 | 0 | — | — | Appwrite tools for Claude Code, including SDK skills, Appwrite MCP servers, and deployment commands. |
| `asana` | available | 0 | 0 | 1 | — | — | Asana project management integration. Connects Claude Code to Asana's V2 MCP server to create and manage tasks, search projects, update assignments, and track… |
| `astronomer-data-agents` | available | 0 | 0 | 0 | — | — | Data engineering for Apache Airflow and Astronomer. Author DAGs with best practices, debug pipeline failures, trace data lineage, profile tables, migrate Airfl… |
| `atlan` | available | 0 | 0 | 0 | — | — | Atlan data catalog plugin for Claude Code. Search, explore, govern, and manage your data assets through natural language. Powered by the Atlan MCP server with… |
| `atlassian` | available | 0 | 0 | 0 | — | — | Connect to Atlassian products including Jira and Confluence. Search and create issues, access documentation, manage sprints, and integrate your development wor… |
| `atlassian-twg-cli` | available | 0 | 0 | 0 | — | — | Teamwork Graph CLI is Atlassian's agent-first interface to your entire work context: Jira issues, Confluence pages, Bitbucket PRs, along with your connected th… |
| `atomic-agents` | available | 0 | 0 | 0 | — | — | Comprehensive development workflow for building AI agents with the Atomic Agents framework. Includes specialized agents for schema design, architecture plannin… |
| `auth0` | available | 0 | 0 | 0 | — | — | Enterprise-grade auth, easy to implement. Add login, SSO, MFA, and access control to any app with framework-aware guidance. |
| `aws-agents` | available | 0 | 0 | 0 | — | — | Build, deploy, and operate AI agents on AWS. Skills for scaffolding agents with Amazon Bedrock AgentCore, connecting tools, memory, policies, evaluation, debug… |
| `aws-agents-for-devsecops` | available | 0 | 0 | 0 | — | — | Investigate incidents, review code and execute UAT for release readiness, scan code for vulnerabilities, and run penetration tests with AWS DevOps Agent and AW… |
| `aws-amplify` | available | 0 | 0 | 0 | — | — | Build full-stack apps with AWS Amplify Gen 2 using guided workflows for authentication, data models, storage, GraphQL APIs, and Lambda functions. |
| `aws-core` | available | 0 | 0 | 0 | — | — | Build, deploy, and operate applications on AWS. Skills to author infrastructure-as-code, use core services, and complete common tasks. |
| `aws-data-analytics` | available | 0 | 0 | 0 | — | — | Data lake, analytics, and ETL workflows with S3 Tables, AWS Glue, and Athena. |
| `aws-serverless` | available | 0 | 0 | 0 | — | — | Design, build, deploy, test, and debug serverless applications with AWS Serverless services. |
| `aws-startup-advisor` | available | 0 | 0 | 0 | — | — | Personalized AWS guidance built on patterns from 350,000+ startups. Get architecture, cost, and security recommendations matched to your stage, from day-one ac… |
| `aws-transform` | available | 0 | 0 | 0 | — | — | Migrate, modernize, and upgrade codebases to AWS. Transforms .NET Framework to .NET 8/10, mainframe COBOL to Java, VMware VMs to EC2, SQL Server to Aurora, and… |
| `azure` | available | 0 | 0 | 0 | — | — | Transform Claude into an Azure expert. This plugin integrates the Azure MCP server and specialized Azure skills to move beyond generic advice. It enables Claud… |
| `azure-cosmos-db-assistant` | available | 0 | 0 | 0 | — | — | Expert assistant for Azure Cosmos DB — data modeling, query optimization, performance tuning, and best practices. |
| `azure-sql-developer` | available | 0 | 0 | 0 | — | — | Agent skills for Azure SQL Developer, the Azure SQL Database engine running locally in a container. Teaches your agent to run the engine, connect, migrate, sca… |
| `base44` | available | 0 | 0 | 0 | — | — | Build and deploy Base44 full-stack apps with CLI project management and JavaScript/TypeScript SDK development skills |
| `bigdata-com` | available | 0 | 0 | 0 | — | — | Official Bigdata.com plugin providing financial research, analytics, and intelligence tools powered by Bigdata MCP. |
| `bigquery-data-analytics` | available | 0 | 0 | 0 | — | — | Connect, query, and generate data insights for BigQuery datasets and data. |
| `blackrock-advisor-center-plugin` | available | 0 | 0 | 0 | — | — | BlackRock Advisor Center 360° skills for financial advisors: portfolio review, opportunity and fund-health checks, guided benchmark selection, guided portfolio… |
| `boltz` | available | 0 | 0 | 0 | — | — | Predict structures, screen molecules and proteins, and design binders with Boltz from Claude Code. |
| `box` | available | 0 | 0 | 0 | — | — | Work with your Box content directly from Claude Code — search files, organize folders, collaborate with your team, and use Box AI to answer questions, summariz… |
| `brightdata-plugin` | available | 0 | 0 | 0 | — | — | Web scraping, Google search, structured data extraction, and MCP server integration powered by Bright Data. Includes 7 skills: scrape any webpage as markdown (… |
| `browser-use` | available | 0 | 0 | 0 | — | — | Give Claude a real browser — your Chrome or a Browser Use Cloud browser. Use it whenever a task involves a website or web app: browsing, scraping and data extr… |
| `build-with-wordpress` | available | 0 | 0 | 0 | — | — | Craft production-grade WordPress sites and applications. Everything from themes and plugins to commerce and deployment. |
| `buildkite` | available | 0 | 0 | 0 | — | — | Official Buildkite skills for Claude Code, Cursor, and other AI coding agents — pipelines, migration, preflight, agent runtime, CLI, and API |
| `canva` | available | 0 | 0 | 0 | — | — | Create, edit, review, resize, and brand-check Canva designs with the Canva MCP server. |
| `carbone-skill` | available | 0 | 0 | 0 | — | — | Official Carbone skill — complete templating language reference covering tags, loops, conditions, formatters, aggregators, and all output formats (DOCX, XLSX,… |
| `carta-cap-table` | available | 0 | 0 | 0 | — | — | Carta Cap Table plugin — skills and hooks for querying cap tables, grants, SAFEs, 409A valuations, waterfall scenarios, and more |
| `carta-crm` | available | 0 | 0 | 0 | — | — | Manage the Carta CRM conversationally — search, add, update, and enrich investors, companies, contacts, deals, notes, and fundraisings via the Carta CRM MCP Se… |
| `carta-investors` | available | 0 | 0 | 0 | — | — | Carta Investors plugin — skills for querying investor data, performance benchmarks, regulatory reporting, AGM deck generation, brand extraction, and more via t… |
| `catalyst-by-zoho` | available | 0 | 0 | 0 | — | — | Official Claude Code plugin for Catalyst by Zoho — full-stack serverless cloud platform. With Skills that covers all services, SDKs, CLI, architecture patterns… |
| `cds-mcp` | available | 0 | 0 | 0 | — | — | AI-assisted development of SAP Cloud Application Programming Model (CAP) projects. Search CDS models and CAP documentation. |
| `chrome-devtools-mcp` | available | 0 | 0 | 0 | — | — | Control and inspect a live Chrome browser from your coding agent. Record performance traces, analyze network requests, check console messages with source-mappe… |
| `chronograph-gp` | available | 0 | 0 | 0 | — | — | Portfolio monitoring, valuations and analytics for private-capital GP teams using the Chronograph connector: portfolio-company one-pagers, fund quarterly revie… |
| `chronograph-lp` | available | 0 | 0 | 0 | — | — | Portfolio monitoring and analytics for private-capital LP teams using the Chronograph connector: cashflow forecasting, commitment pacing, look-through exposure… |
| `circle-skills` | available | 0 | 0 | 0 | — | — | Ship stablecoin apps faster. Best-practice skills for USDC payments, cross-chain transfers, wallets, and smart contracts — plus Circle's MCP server for real-ti… |
| `circleback` | available | 0 | 0 | 0 | — | — | Circleback conversational context integration. Search and access meetings, emails, calendar events, and more. |
| `ckeditor` | available | 0 | 0 | 0 | — | — | Install, configure, and integrate CKEditor 5 (free and premium) in any JavaScript project. |
| `clangd-lsp` | available | 0 | 0 | 0 | — | — | C/C++ language server (clangd) for code intelligence |
| `clay` | available | 0 | 0 | 0 | — | — | Work with Clay from Claude Code: set up and sign in to the clay CLI, query and analyze Clay tables, search Clay's GTM database for people and companies, manage… |
| `clickhouse` | available | 0 | 0 | 0 | — | — | Connect Claude to your ClickHouse Cloud databases. Browse organizations, services, databases, and table schemas. Run read-only SQL queries against your data an… |
| `clickhouse-best-practices` | available | 0 | 0 | 0 | — | — | 28 best practice rules for ClickHouse schema design, query optimization, and data ingestion — prioritized by impact |
| `cloud-sql-mysql` | available | 0 | 0 | 0 | — | — | Connect and interact with a Cloud SQL for MySQL database and data. |
| `cloud-sql-postgresql` | available | 0 | 0 | 0 | — | — | Create, connect, and interact with a Cloud SQL for PostgreSQL database and data. |
| `cloud-sql-sqlserver` | available | 0 | 0 | 0 | — | — | Connect to Cloud SQL for SQL Server |
| `cloudflare` | available | 0 | 0 | 0 | — | — | Skills for the Cloudflare developer platform: Workers, Durable Objects, Agents SDK, MCP servers, Wrangler CLI, and web performance. |
| `cloudinary` | available | 0 | 0 | 0 | — | — | Use Cloudinary directly in Claude. Manage assets, apply transformations, optimize media, and more through natural conversation. |
| `cockroachdb` | available | 0 | 0 | 0 | — | — | Connect Claude Code directly to your CockroachDB clusters for hands-on database work — explore schemas, write optimized SQL, debug queries, and manage distribu… |
| `coderabbit` | available | 0 | 0 | 0 | — | — | Your code review partner. CodeRabbit provides external validation using a specialized AI architecture and 40+ integrated static analyzers—offering a different… |
| `codspeed` | available | 0 | 0 | 0 | — | — | CodSpeed is the all-in-one performance testing toolkit. Dive into benchmarking results, flamegraphs, and performance comparisons — give Claude granular profili… |
| `commit-commands` | available | 0 | 0 | 3 | — | — | Commands for git commit workflows including commit, push, and PR creation |
| `confidence` | available | 0 | 0 | 0 | — | — | Access Confidence feature flags, experiments, and migration tools directly from Claude Code. |
| `context7` | available | 0 | 0 | 0 | — | context7 | Upstash Context7 MCP server for up-to-date documentation lookup. Connects to Context7's hosted remote MCP server (https://mcp.context7.com/mcp) — no local Node… |
| `convex` | available | 0 | 0 | 0 | — | — | Official Convex plugin for Claude Code with bundled Convex skills, the convex-expert subagent for code-writing, a runtime-error monitor, and MCP access for bac… |
| `crowdsec` | available | 0 | 0 | 0 | — | — | Operational skill for installing, configuring, operating, and debugging CrowdSec (cscli, LAPI/CAPI, hub, bouncers, WAF/AppSec) across bare-metal, Docker, and K… |
| `crowdstrike-falcon-foundry` | available | 0 | 0 | 0 | — | — | CrowdStrike Falcon Foundry development skills for building cybersecurity applications on the Falcon platform. Includes UI development, collections, functions,… |
| `crowdstrike-falcon-fusion` | available | 0 | 0 | 0 | — | — | CrowdStrike Falcon Fusion skills for authoring, deploying, and executing Fusion workflows. Includes live action discovery, YAML authoring with schema validatio… |
| `csharp-lsp` | available | 0 | 0 | 0 | — | — | C# language server for code intelligence |
| `cwc-makers` | available | 2 | 0 | 1 | — | — | Onboard a Code-with-Claude Makers Cardputer with one /maker-setup command — clones the build-with-claude repo, flashes UIFlow firmware, and installs the Claude… |
| `dash0` | available | 0 | 0 | 0 | — | — | OpenTelemetry observability for Claude Code sessions. Captures tool calls, LLM invocations, token usage, and errors as OTel traces. Send telemetry to Dash0 or… |
| `data` | available | 0 | 0 | 0 | — | — | Data engineering for Apache Airflow and Astronomer. Author DAGs with best practices, debug pipeline failures, trace data lineage, profile tables, migrate Airfl… |
| `data-agent-kit` | available | 0 | 0 | 0 | — | — | This plugin provides a specialized suite of skills for data engineers and database practitioners working on Google Cloud. It acts as an expert assistant, allow… |
| `data-engineering` | available | 0 | 0 | 0 | — | — | Data engineering plugin - warehouse exploration, pipeline authoring, Airflow integration |
| `databases-on-aws` | available | 0 | 0 | 0 | — | — | Expert database guidance for the AWS database portfolio. Design schemas, execute queries, handle migrations, and choose the right database for your workload. |
| `databricks` | available | 0 | 0 | 0 | — | — | Databricks skills for the CLI, Apps, Lakebase, Model Serving, Lakeflow Jobs, Spark Declarative Pipelines, Declarative Automation Bundles (DABs), and classic-to… |
| `datadog` | available | 0 | 0 | 0 | — | — | Use Datadog directly in Claude Code through a preconfigured Datadog MCP server. Query logs, metrics, traces, dashboards, and more through natural conversation.… |
| `datahub-skills` | available | 0 | 0 | 0 | — | — | DataHub development and interaction toolkit with connector planning, PR review, catalog search, metadata enrichment, lineage tracing, data quality management,… |
| `dataproc` | available | 0 | 0 | 0 | — | — | Manage Dataproc clusters and jobs. |
| `datarobot-agent-skills` | available | 0 | 0 | 0 | — | — | DataRobot skills for AI/ML workflows — model training, deployment, predictions, feature engineering, monitoring, explainability, data preparation, App Framewor… |
| `dataverse` | available | 0 | 0 | 0 | — | — | Agent skills for building on, analyzing, and managing Microsoft Dataverse — with Dataverse MCP, PAC CLI, and Python SDK. |
| `deepeval` | available | 0 | 0 | 0 | — | — | Skills for adding DeepEval evaluations, tracing, datasets, Confident AI reports, and iterative improvement loops to AI applications. |
| `deploy-on-aws` | available | 0 | 0 | 0 | — | — | Deploy applications to AWS with architecture recommendations, cost estimates, and IaC deployment. |
| `desktop-commander` | available | 0 | 0 | 0 | — | — | MCP server for terminal commands, process management, and file operations across text, code, PDF, DOCX, Excel, images, and structured data. |
| `discord` | available | 2 | 0 | 0 | — | discord | Discord messaging bridge with built-in access control. Manage pairing, allowlists, and policy via /discord:access. |
| `dominodatalab` | available | 0 | 0 | 0 | — | — | Full Domino Data Lab platform support — workspaces, jobs, model deployment, experiment tracking, GenAI tracing, Spark/Ray/Dask, and app deployment for data sci… |
| `dropbox` | available | 0 | 0 | 0 | — | — | The Dropbox plugin for Claude connects your Dropbox files directly to Claude, so you can search, organize, save generated content, and create sharing links wit… |
| `duckdb-skills` | available | 0 | 0 | 0 | — | — | DuckDB-powered skills for Claude Code: read any data file, attach and query DuckDB databases, search DuckDB/DuckLake docs, search past session logs, and instal… |
| `duende-skills` | available | 0 | 0 | 0 | — | — | Duende development skills and agents for Claude Code — covering OAuth/OIDC protocols, IdentityServer, token management, ASP.NET Core authentication/authorizati… |
| `dynatrace` | available | 0 | 0 | 0 | — | — | Dynatrace observability skills: DQL query patterns, application and infrastructure monitoring, log analysis, problem investigation, and incident response workf… |
| `exa` | available | 0 | 0 | 0 | — | — | Exa AI web search, deep research, and content extraction. Provides MCP tools and research skills for comprehensive web search, people discovery, company resear… |
| `explanatory-output-style` | available | 0 | 0 | 0 | SessionStart | — | Adds educational insights about implementation choices and codebase patterns (mimics the deprecated Explanatory output style) |
| `expo` | available | 0 | 0 | 0 | — | — | Official Expo skills for building, deploying, upgrading, and debugging React Native apps with Expo. Covers UI development with Expo Router, SwiftUI and Jetpack… |
| `fakechat` | available | 0 | 0 | 0 | — | fakechat | Localhost web chat for testing the channel notification flow. No tokens, no access control, no third-party service. |
| `fastly-agent-toolkit` | available | 0 | 0 | 0 | — | — | Fastly development tools and platform skills |
| `fiftyone` | available | 0 | 0 | 0 | — | — | Build high-quality datasets and computer vision models. Visualize datasets, analyze models, find duplicates, run inference, evaluate predictions, and develop c… |
| `figma` | available | 0 | 0 | 0 | — | — | Figma design platform integration. Access design files, extract component information, read design tokens, and translate designs into code. Bridge the gap betw… |
| `firebase` | available | 0 | 0 | 0 | — | firebase | Google Firebase MCP integration. Manage Firestore databases, authentication, cloud functions, hosting, and storage. Build and manage your Firebase backend dire… |
| `firecrawl` | available | 0 | 0 | 0 | — | — | Web scraping and crawling powered by Firecrawl. Turn any website into clean, LLM-ready markdown or structured data. Scrape single pages, crawl entire sites, se… |
| `firestore-native` | available | 0 | 0 | 0 | — | — | Connect and interact with Firestore databases, collections, and documents. |
| `forge-skills` | available | 0 | 0 | 0 | — | — | Forge-focused skills and MCP configuration for Atlassian Forge: scaffold and deploy apps (forge create, templates, dev spaces), build Teamwork Graph connectors… |
| `fullstory` | available | 0 | 0 | 0 | — | — | Connect Claude to Fullstory to query behavioral analytics, session replays, and customer experience insights. |
| `gc-ai` | available | 0 | 0 | 0 | — | — | Work in your GC AI legal knowledge base from Claude: upload documents, run review playbooks, and ask questions grounded in your own files, all as you. |
| `github` | available | 0 | 0 | 0 | — | github | Official GitHub MCP server for repository management. Create issues, manage pull requests, review code, search repositories, and interact with GitHub's full AP… |
| `gitkraken` | available | 0 | 0 | 0 | — | — | Gives Claude access to your real Git and project context: commits, branches, pull requests, and issues across every repo you work in. Works with GitHub, GitLab… |
| `gitlab` | available | 0 | 0 | 0 | — | gitlab | GitLab DevOps platform integration. Manage repositories, merge requests, CI/CD pipelines, issues, and wikis. Full access to GitLab's comprehensive DevOps lifec… |
| `google-cloud-storage` | available | 0 | 0 | 0 | — | — | Official Google Cloud Storage (GCS) plugin. Manage buckets and objects, transfer data, and configure MCP, FUSE, IAM, security, lifecycle rules, signed URLs, Te… |
| `gopls-lsp` | available | 0 | 0 | 0 | — | — | Go language server for code intelligence and refactoring |
| `govtribe` | available | 0 | 0 | 0 | — | — | Government contracting research and capture workflows in Claude: opportunity and pipeline briefs, bid/no-bid and competitor analysis, price-to-win and proposal… |
| `grafana-assistant` | available | 0 | 0 | 0 | — | — | Skills and rules for developing and using the Grafana Assistant app and CLI. |
| `grafana-cloud-mcp` | available | 0 | 0 | 0 | — | — | Hosted MCP server for AI-assisted Grafana Cloud observability — no local installation required. |
| `grafana-mcp` | available | 0 | 0 | 0 | — | — | MCP server for AI-assisted Grafana dashboard, datasource, alerting, and incident management. |
| `greptile` | available | 0 | 0 | 0 | — | — | AI code review agent for GitHub and GitLab. View and resolve Greptile's PR review comments, run reviews on your working branch, and search your organization's… |
| `growthbook` | available | 0 | 0 | 0 | — | — | A suite of agent skills for the full GrowthBook feature flag and experimentation lifecycle. |
| `honeycomb` | available | 0 | 0 | 0 | — | — | Skills, agents, and workflows for Honeycomb observability — query patterns, production investigations, SLOs, OpenTelemetry instrumentation, and Beeline migrati… |
| `hostinger` | available | 0 | 0 | 0 | — | — | Deploy, manage and monitor your Hostinger services directly from Claude Code. The plugin connects Claude to Hostinger's remote MCP server, so you can ship site… |
| `hubspot-sales` | available | 0 | 0 | 0 | — | — | Run your HubSpot sales workflow directly from Claude. Adds skills that cover the full sales day: import contacts and deals into HubSpot, get a prioritised morn… |
| `huggingface-skills` | available | 0 | 0 | 0 | — | — | Build, train, evaluate, and use open source AI models, datasets, and spaces. |
| `hunter` | available | 0 | 0 | 0 | — | — | Find and verify professional email addresses, search contacts by domain, and enrich company data -- directly in Claude. |
| `hyperframes` | available | 0 | 0 | 0 | — | — | HyperFrames by HeyGen. Write HTML, render video. Compositions, GSAP and runtime adapter animations, captions, voiceovers, audio-reactive visuals, and website-t… |
| `idmp-plugin` | available | 0 | 0 | 0 | — | — | TDengine IDMP plugin with packaged skills for discovery, schema inspection, and safe operational workflows. |
| `imessage` | available | 2 | 0 | 0 | — | imessage | iMessage messaging bridge with built-in access control. Reads chat.db directly, sends via AppleScript. Manage pairing, allowlists, and policy via /imessage:acc… |
| `incident-io` | available | 0 | 0 | 0 | — | — | Work with incident.io from Claude: respond to and investigate incidents, check on-call schedules and escalations, and author the runbooks, skills and architect… |
| `informatica-for-claude-platform` | available | 0 | 0 | 0 | — | — | Governed catalog discovery for Informatica Intelligent Data Management Cloud (CDGC): find tables, columns, files, glossary terms and policies across the enterp… |
| `intercom` | available | 0 | 0 | 0 | — | — | Intercom integration for Claude Code. Search conversations, analyze customer support patterns, look up contacts and companies, and install the Intercom Messeng… |
| `intuit-quickbooks` | available | 0 | 0 | 0 | — | — | QuickBooks business insights and actions: financial health briefings across P&L, cash flow, balance sheet and A/R, industry benchmarking, payroll cost analysis… |
| `jdtls-lsp` | available | 0 | 0 | 0 | — | — | Java language server (Eclipse JDT.LS) for code intelligence |
| `jfrog` | available | 0 | 0 | 0 | — | — | Use the JFrog Platform from Claude Code: Artifactory repos and artifacts, security findings and exposures, Catalog package safety and downloads, workflows acro… |
| `knowledge-catalog` | available | 0 | 0 | 0 | — | — | Connect to Knowledge Catalog to discover, manage, monitor, and govern data and AI artifacts across your data platform |
| `kotlin-lsp` | available | 0 | 0 | 0 | — | — | Kotlin language server for code intelligence |
| `langfuse` | available | 0 | 0 | 0 | — | — | Skills for working with Langfuse, the open-source LLM engineering platform for tracing, prompt management, and evaluation. |
| `langfuse-observability` | available | 0 | 0 | 0 | — | — | Langfuse observability plugin for Claude Code — captures and exports traces, spans, and session telemetry from Claude Code to Langfuse for LLM monitoring, debu… |
| `laravel-boost` | available | 0 | 0 | 0 | — | laravel-boost | Laravel development toolkit MCP server. Provides intelligent assistance for Laravel applications including Artisan commands, Eloquent queries, routing, migrati… |
| `leadfeeder` | available | 0 | 0 | 0 | — | — | Turn website visitor signals into pipeline with Leadfeeder: daily visitor briefs, visitor company research, buyer and contact discovery, personalised outreach… |
| `learning-output-style` | available | 0 | 0 | 0 | SessionStart | — | Interactive learning mode that requests meaningful code contributions at decision points (mimics the unshipped Learning output style) |
| `legalzoom` | available | 0 | 0 | 0 | — | — | Attorney guidance and legal tools for business and personal needs. AI-powered document review identifies critical risks and important clauses, advises when to… |
| `linear` | available | 0 | 0 | 0 | — | linear | Linear issue tracking integration. Create issues, manage projects, update statuses, search across workspaces, and streamline your software development workflow… |
| `linq-alpha` | available | 0 | 0 | 0 | — | — | LinqAlpha financial research in Claude: guided setup for the LinqAlpha connector, capability-based source selection for fundamentals, estimates, transcripts, f… |
| `liquid-lsp` | available | 0 | 0 | 0 | — | — | LSP integration for Shopify Liquid templates via the Shopify CLI theme language server. |
| `liquid-skills` | available | 0 | 0 | 0 | — | — | Liquid language fundamentals, CSS/JS/HTML coding standards, and WCAG accessibility patterns for Shopify themes |
| `logfire` | available | 0 | 0 | 0 | — | — | Add Logfire observability to Python applications with auto-instrumentation for FastAPI, httpx, asyncpg, SQLAlchemy, and more |
| `logrocket` | available | 0 | 0 | 0 | — | — | Connect Claude Code to LogRocket to query session replays, metrics, issues, and user behavior using natural language. |
| `looker` | available | 0 | 0 | 0 | — | — | Connect to Looker and interact with your data using LookML. |
| `lovable` | available | 0 | 0 | 0 | — | — | Build, iterate on, deploy, and manage Lovable apps from Claude Code. Bundles the official Lovable MCP server (remote, OAuth 2.1) and adds focused commands for… |
| `lua-lsp` | available | 0 | 0 | 0 | — | — | Lua language server for code intelligence |
| `lumen` | available | 0 | 0 | 0 | — | — | Precise local semantic code search via MCP. Indexes your codebase with Go AST parsing, embeds with Ollama or LM Studio, and exposes vector search to Claude thr… |
| `lusha` | available | 0 | 0 | 0 | — | — | Prospect, enrich, and build call-ready lead lists using Lusha's B2B intelligence platform — verified phone numbers, company signals, and lookalike targeting. |
| `mapbox` | available | 0 | 0 | 0 | — | — | Mapbox skills and MCP servers for building location-aware applications with AI. Includes geospatial tools, style management, and patterns for web, iOS, Android… |
| `math-olympiad` | available | 1 | 0 | 0 | — | — | Solve competition math (IMO, Putnam, USAMO) with adversarial verification that catches what self-verification misses. Fresh-context verifiers attack proofs wit… |
| `math-proof` | available | 2 | 3 | 0 | — | — | Two skills for hard mathematics problems, each ending in a self-contained proof.md: /math-proof:solo has the session work the problem itself in stages with a n… |
| `mattpocock-skills` | available | 0 | 0 | 0 | — | — | Matt Pocock's agent skills for real engineering — grilling, spec/ticket flows, TDD, code review, domain modelling and more. Plug-and-play, not vibe coding. |
| `mcp-apps` | available | 0 | 0 | 0 | — | — | Skills for creating MCP Apps with the MCP Apps SDK |
| `mcp-server-dev` | available | 3 | 0 | 0 | — | — | Skills for designing and building MCP servers that work seamlessly with Claude. Guides you through deployment models (remote HTTP, MCPB, local), tool design pa… |
| `mcp-tunnels` | available | 0 | 0 | 1 | — | — | Connect Claude to a private MCP server through an Anthropic MCP tunnel. The /create-docker-mcp-tunnel command drives the Docker Compose quickstart end to end:… |
| `mercadopago` | available | 0 | 0 | 0 | — | — | Mercado Pago full-product integration toolkit. One agent routes to four orchestration skills (mp-integrate wizard, mp-webhooks, mp-test-setup, mp-review) that… |
| `mergify` | available | 0 | 0 | 0 | — | — | Skills for the Mergify CLI: manage merge queues, stacked pull requests, Test Insights (flaky tests, quarantine), merge protections, and Mergify configuration d… |
| `microsoft-docs` | available | 0 | 0 | 0 | — | — | Access official Microsoft documentation, API references, and code samples for Azure, .NET, Windows, and more. |
| `migration-to-aws` | available | 0 | 0 | 0 | — | — | Plan a migration from Google Cloud Platform (and OpenAI/Gemini AI workloads) to AWS. Analyzes your Infrastructure-as-Code files, app code, and GCP billing data… |
| `mintlify` | available | 0 | 0 | 0 | — | — | Build beautiful documentation sites with Mintlify. Convert non-markdown files into properly formatted MDX pages, add and modify content with correct component… |
| `miro` | available | 0 | 0 | 0 | — | — | Secure access to Miro boards. Enables AI to read board context, create diagrams, and generate code with enterprise-grade security. |
| `mlflow` | available | 0 | 0 | 0 | — | — | Skills for tracing, evaluating, and improving AI agents with MLflow. Supports the full agent improvement loop: instrument → trace → evaluate → iterate → valida… |
| `monday-crm` | available | 0 | 0 | 0 | — | — | Run your monday CRM in plain language. Build a pipeline from scratch, start the day with a ranked deal briefing, spin up a forecast dashboard, audit board heal… |
| `mongodb` | available | 0 | 0 | 0 | — | — | Official Claude plugin for MongoDB (MCP Server + Skills). Connect to databases, explore data, manage collections, optimize queries, generate reliable code, imp… |
| `mongodb-atlas` | available | 0 | 0 | 0 | — | — | Connect to MongoDB Atlas clusters only through the Atlas Managed MCP Server. Sign in with your Atlas account to explore data, manage collections, optimize quer… |
| `neon` | available | 0 | 0 | 0 | — | — | Manage your Neon projects and databases with the neon-postgres agent skill and the Neon MCP Server. |
| `netlify-skills` | available | 0 | 0 | 0 | — | — | Netlify platform skills for Claude Code — functions, edge functions, blobs, database, image CDN, forms, config, CLI, frameworks, caching, AI gateway, and deplo… |
| `netsuite-ai-companion` | available | 0 | 0 | 0 | — | — | Guides AI assistants that use the NetSuite AI Connector: tool-selection order, output formatting, NetSuite domain knowledge, multi-subsidiary and currency hand… |
| `netsuite-finance-analyst` | available | 0 | 0 | 0 | — | — | Director-level finance analysis on live NetSuite data: financial reporting, period close, variance, aging and reconciliation reviews, cash reporting, and board… |
| `netsuite-suitecloud` | available | 0 | 0 | 0 | — | — | Develop NetSuite SuiteCloud solutions with SuiteScript, SDF, and best practices: SuiteScript records and upgrades, SDF objects, roles and permissions, UIF sing… |
| `newrelic` | available | 0 | 0 | 0 | — | — | New Relic observability intelligence for Claude Code. Investigate APM performance, analyze cloud costs, debug Kubernetes, write NRQL queries, and respond to al… |
| `nightvision` | available | 0 | 0 | 0 | — | — | Skills for working with NightVision, a DAST and API Discovery platform that finds exploitable vulnerabilities in web applications and REST APIs |
| `nimble` | available | 0 | 0 | 0 | — | — | Nimble web data toolkit — search, extract, map, crawl the web and work with structured data agents |
| `noibu` | available | 0 | 0 | 0 | — | — | Built for ecommerce, the Noibu plugin bridges the gap between customer experience and revenue by connecting Claude directly to your store's session, error, and… |
| `notion` | available | 0 | 0 | 0 | — | — | Notion workspace integration. Search pages, create and update documents, manage databases, and access your team's knowledge base directly from Claude Code for… |
| `nvidia-skills` | available | 0 | 0 | 0 | — | — | Find the right NVIDIA skill for GPU acceleration, CUDA, AI agents, data loading, training, inference, robotics, Physical AI, Omniverse, simulation, and other N… |
| `oracle-ai-data-platform-workbench-databricks-migrator` | available | 0 | 0 | 0 | — | — | Drive the Oracle AI Data Platform (AIDP) Databricks Migration Toolkit in natural language. Plans and executes automated Databricks → AIDP migrations of noteboo… |
| `oracle-ai-data-platform-workbench-engineer-agent` | available | 0 | 0 | 0 | — | — | Oracle AI Data Platform (AIDP) Workbench engineer agent for Claude Code — a 37-skill agent that operates the full Spark/Delta lakehouse in natural language. Di… |
| `oracle-ai-data-platform-workbench-spark-connectors` | available | 0 | 0 | 0 | — | — | Oracle AI Data Platform Workbench Spark connectors for Claude Code. 18 connector skills covering every data source workbench customers commonly need: Oracle Au… |
| `oracledb` | available | 0 | 0 | 0 | — | — | Connect, query, and interact with Oracle Databases and their data. |
| `outputai` | available | 0 | 0 | 0 | — | — | Output.ai workflow development toolkit for Claude Code. Adds 5 specialist agents (planner, builder, debugger, prompt writer, quality reviewer), 40+ slash-comma… |
| `pagerduty` | available | 0 | 0 | 0 | — | — | Enhance code quality and security through PagerDuty risk scoring and incident correlation. Score pre-commit diffs against historical incident data and surface… |
| `paypal` | available | 0 | 0 | 0 | — | — | PayPal development plugin for Claude — integrate payments, subscriptions, invoices, disputes, and more using PayPal's APIs and MCP server |
| `pendo-analytics` | available | 0 | 0 | 0 | — | — | Bring Pendo product analytics into Claude Code: account health, feature adoption, session replay lookup and triage, feedback analysis, and data-informed planni… |
| `pendo-guides` | available | 0 | 0 | 0 | — | — | Create production-ready Pendo in-app guides (walkthroughs, announcements, alerts, polls, promotions) as HTML/CSS/JS from a short intake conversation, using Pen… |
| `pendo-orchestrate` | available | 0 | 0 | 0 | — | — | Create, configure and edit draft Pendo Orchestrate email journeys, including multi-email and conditional split flows, via the Pendo connector. Journeys stay in… |
| `php-lsp` | available | 0 | 0 | 0 | — | — | PHP language server (Intelephense) for code intelligence |
| `pigment` | available | 0 | 0 | 0 | — | — | Analyze business data and build custom Pigment models, metrics, and boards through natural language. |
| `pinecone` | available | 0 | 0 | 0 | — | — | Pinecone vector database integration. Streamline your Pinecone development with powerful tools for managing vector indexes, querying data, and rapid prototypin… |
| `pixeltable` | available | 0 | 0 | 0 | — | — | Build multimodal AI applications with Pixeltable -- tables, computed columns, embedding search, UDFs, tool-calling agents, and 25+ AI provider integrations. |
| `planetscale` | available | 0 | 0 | 0 | — | — | An authenticated hosted MCP server that accesses your PlanetScale organizations, databases, branches, schema, and Insights data. Query against your data, surfa… |
| `playwright` | available | 0 | 0 | 0 | — | playwright | Browser automation and end-to-end testing MCP server by Microsoft. Enables Claude to interact with web pages, take screenshots, fill forms, click elements, and… |
| `plugin-dev` | available | 7 | 3 | 1 | — | — | Comprehensive toolkit for developing Claude Code plugins. Includes 7 expert skills covering hooks, MCP integration, commands, agents, and best practices. AI-as… |
| `posthog` | available | 0 | 0 | 0 | — | — | Access PostHog analytics, feature flags, experiments, error tracking, and insights directly from Claude Code. |
| `postiz` | available | 0 | 0 | 0 | — | — | Social media automation CLI for scheduling posts, managing integrations, uploading media, and tracking analytics across 28+ platforms including X, LinkedIn, Re… |
| `postman` | available | 0 | 0 | 0 | — | — | Work with Postman from your agent: bootstrap a repo's Postman setup, mock an API before it's implemented, run collection and governance checks in CI, monitor a… |
| `preset-cli-skills` | available | 0 | 0 | 0 | — | — | Preset CLI skills for explicit shell, scripting, and CI/CD workflows driven by the `sup` CLI (PyPI package `superset-sup`). Use only for CLI workflows; do not… |
| `prisma` | available | 0 | 0 | 0 | — | — | Prisma MCP integration for Postgres database management, schema migrations, SQL queries, and connection string management. Provision Prisma Postgres databases,… |
| `project-artifact` | available | 1 | 0 | 0 | — | — | Generate and publish a living project status page — overview & success criteria, the workstream sequence, and next steps — as a shareable claude.ai artifact ba… |
| `pydantic-ai` | available | 0 | 0 | 0 | — | — | Write accurate Pydantic AI code from the start. Up-to-date patterns, decision trees, and common gotchas for agents, tools, structured output, streaming, and mu… |
| `pyright-lsp` | available | 0 | 0 | 0 | — | — | Python language server (Pyright) for type checking and code intelligence |
| `qdrant-skills` | available | 0 | 0 | 0 | — | — | Agent skills for Qdrant vector search covering scaling, performance optimization, search quality, monitoring, deployment, model migration, version upgrades, an… |
| `qodo` | available | 0 | 0 | 0 | — | — | Bring Qodo's codebase intelligence, coding standards, and code review into your coding agent. |
| `qodo-standards` | available | 0 | 0 | 0 | — | — | Optional Qodo rules discovery and standards administration workflows. |
| `qt-development-skills` | available | 0 | 0 | 0 | — | — | Agentic engineering skills for Qt software development — Qt C++/QML code review, QML coding, and Qt C++/QML code documentation. |
| `quarkus-agent` | available | 0 | 0 | 0 | — | — | MCP server for AI coding agents to create, manage, and interact with Quarkus applications. Provides tools for project scaffolding, dev mode lifecycle, extensio… |
| `railway` | available | 0 | 0 | 0 | — | — | Deploy and manage apps, databases, and infrastructure on Railway. Covers project setup, deploys, environment configuration, networking, troubleshooting, and mo… |
| `rc` | available | 0 | 0 | 0 | — | — | Configure RevenueCat projects, apps, products, entitlements, and offerings directly from Claude Code. Manage your in-app purchase backend without leaving your… |
| `receipts` | available | 1 | 0 | 0 | — | — | A personal Claude Code impact report for justifying your usage to a manager or a self-review: what you shipped, which projects it went to, and each project's s… |
| `redis-development` | available | 0 | 0 | 0 | — | — | Redis development best practices — data structures, query engine, vector search, caching, and performance optimization |
| `remember` | available | 0 | 0 | 0 | — | — | Continuous memory for Claude Code. Extracts, summarizes, and compresses conversations into tiered daily logs. Claude remembers what you did yesterday. |
| `render` | available | 0 | 0 | 0 | — | — | Deploy, debug, and monitor applications on Render. Includes skills, an agent, slash commands, and a render.yaml validation hook. |
| `resend` | available | 0 | 0 | 0 | — | — | Agent skills for working with Resend to send and receive emails — email API integration, agent inbox, CLI, React Email components, and deliverability best prac… |
| `revenuecat` | available | 0 | 0 | 0 | — | — | Configure RevenueCat projects, apps, products, entitlements, and offerings directly from Claude Code. Manage your in-app purchase backend without leaving your… |
| `rill` | available | 0 | 0 | 0 | — | — | Skills for developing and querying projects in the Rill business intelligence platform |
| `rootly` | available | 0 | 0 | 0 | — | — | Full-lifecycle incident management: deploy safety, incident response, on-call management, and retrospectives. |
| `ruby-lsp` | available | 0 | 0 | 0 | — | — | Ruby language server for code intelligence and analysis |
| `runway-api` | available | 0 | 0 | 0 | — | — | Get guidance for integrating video, image and audio generation with the Runway API and official SDKs. Connect to your Runway Dev account to inspect available m… |
| `rust-analyzer-lsp` | available | 0 | 0 | 0 | — | — | Rust language server for code intelligence and analysis |
| `sagemaker-ai` | available | 0 | 0 | 0 | — | — | Build, train, and deploy AI models with deep AWS AI/ML expertise brought directly into your coding assistants, covering the surface area of Amazon SageMaker AI. |
| `salesforce-development` | available | 0 | 0 | 0 | — | — | Build Salesforce apps and agents using these core building blocks: metadata, Apex, deploy/retrieve, security, reporting, and generated installed-versus-availab… |
| `sanity` | available | 0 | 0 | 0 | — | — | Sanity content platform integration with MCP server, agent skills, and slash commands. Query and author content, build and optimize GROQ queries, design schema… |
| `sap-cds-mcp` | available | 0 | 0 | 0 | — | — | AI-assisted development of SAP Cloud Application Programming Model (CAP) projects. Search CDS models and CAP documentation. |
| `sap-fiori-mcp-server` | available | 0 | 0 | 0 | — | — | MCP server for SAP Fiori development tools for Claude Code. Build and modify SAP Fiori applications with AI assistance. |
| `sap-hana-cli` | available | 0 | 0 | 0 | — | — | 150+ SAP HANA database tools for AI assistants. Query tables, import/export data, profile data quality, compare schemas, manage backups, monitor performance, a… |
| `sap-mdk-server` | available | 0 | 0 | 0 | — | — | MCP server for SAP Mobile Development Kit (MDK). Build and modify MDK applications with AI assistance — schema lookups, action validation, rule editing, and pr… |
| `save-to-spotify` | available | 0 | 0 | 0 | — | — | Create polished audio episodes with TTS narration, rich timelines, cover images, and save them to Spotify via the save-to-spotify CLI. |
| `scandit-sdk` | available | 0 | 0 | 0 | — | — | AI agent skills for integrating the Scandit Data Capture SDK — product selection, documentation, and implementation guides for barcode scanning, ID capture, an… |
| `semgrep` | available | 0 | 0 | 0 | — | — | Semgrep catches security vulnerabilities in real-time and guides Claude to write secure code from the start. |
| `sentry` | available | 0 | 0 | 0 | — | — | Sentry error monitoring integration. Access error reports, analyze stack traces, search issues by fingerprint, and debug production errors directly from your d… |
| `sentry-cli` | available | 0 | 0 | 0 | — | — | Skills for using the Sentry CLI to interact with Sentry from the command line |
| `serena` | available | 0 | 0 | 0 | — | serena | Semantic code analysis MCP server providing intelligent code understanding, refactoring suggestions, and codebase navigation through language server protocol i… |
| `servicenow-sdk` | available | 0 | 0 | 0 | — | — | Create, edit, and deploy ServiceNow applications with the Fluent SDK effortlessly through Claude AI. |
| `session-report` | available | 1 | 0 | 0 | — | — | Generate an explorable HTML report of Claude Code session usage — tokens, cache efficiency, subagents, skills, and the most expensive prompts — from local ~/.c… |
| `setup-agent-analytics` | available | 0 | 0 | 0 | — | — | Detect AI agents in your codebase and instrument them with Pendo Agent Analytics via the best-fit path: Python SDK, TypeScript SDK, client-side trackAgent(), o… |
| `setup-mcp-agent-analytics` | available | 0 | 0 | 0 | — | — | Detect an MCP server's language (Python, TypeScript or Go) and instrument it with the matching Pendo SDK so MCP tool calls flow into Pendo Agent Analytics. |
| `shippo` | available | 0 | 0 | 0 | — | — | Shippo connects you to USPS, UPS, FedEx, DHL, and 40+ carriers, so you can handle a shipment end to end right inside Claude. Compare live rates and pick the ch… |
| `shopify-ai-toolkit` | available | 0 | 0 | 0 | — | — | Shopify's AI Toolkit provides 18 development skills for building on the Shopify platform, covering documentation search, API schema access, GraphQL and Liquid… |
| `slack` | available | 0 | 0 | 0 | — | — | Slack workspace integration. Search messages, access channels, read threads, and stay connected with your team's communications while coding. Find relevant dis… |
| `snowflake-cortex-code` | available | 0 | 0 | 0 | — | — | Automatically route Snowflake prompts from Claude Code to Cortex Code for execution. Provides slash commands for code review and task delegation, plus skills f… |
| `sonarqube` | available | 0 | 0 | 0 | — | — | Automatically enforce SonarQube code quality and security in the agent coding loop — 7,000+ rules, secrets scanning, agentic analysis, and quality gates across… |
| `sonatype-guide` | available | 0 | 0 | 0 | — | — | Sonatype Guide MCP server for software supply chain intelligence and dependency security. Analyze dependencies for vulnerabilities, get secure version recommen… |
| `sourcegraph` | available | 0 | 0 | 0 | — | — | Code search and understanding across codebases. Search, read, and trace references across repositories; analyze refactor impact; investigate incidents via comm… |
| `spanner` | available | 0 | 0 | 0 | — | — | Connect and interact with Spanner data using natural language. |
| `spotify-ads-api` | available | 0 | 0 | 0 | — | — | Manage Spotify ad campaigns with natural language. Create campaigns, ad sets, ads, pull reports, and handle OAuth — all through conversation. |
| `stackhawk-api` | available | 0 | 0 | 0 | — | — | Query the StackHawk platform API for security posture reporting, findings analysis, and app management. Guides agents through authentication, data retrieval, a… |
| `stackhawk-hawkscan` | available | 0 | 0 | 0 | — | — | Configure, run, and interpret HawkScan DAST results inside Claude Code. Generates stackhawk.yml configs, runs scans via CLI or Docker, and transforms security… |
| `streaming-skills-plugin` | available | 0 | 0 | 0 | — | — | Skills for streaming application developers, covering Kafka and Flink client libraries and Schema Registry |
| `stripe` | available | 0 | 0 | 0 | — | — | Stripe development plugin for Claude |
| `sumup` | available | 0 | 0 | 0 | — | — | SumUp payment integrations across terminal and online checkout flows. Build Android and iOS POS apps with SumUp card readers, online checkout with server SDKs… |
| `supabase` | available | 0 | 0 | 0 | — | — | Supabase MCP integration for database operations, authentication, storage, and real-time subscriptions. Manage your Supabase projects, run SQL queries, and int… |
| `superdesign` | available | 0 | 0 | 0 | — | — | Design or redesign frontend UI and marketing graphics on the Superdesign infinite canvas. Reads your codebase for context, sets up a design system, and generat… |
| `superpowers` | available | 0 | 0 | 0 | — | — | Superpowers teaches Claude brainstorming, subagent driven development with built in code review, systematic debugging, and red/green TDD. Additionally, it teac… |
| `swift-lsp` | available | 0 | 0 | 0 | — | — | Swift language server (SourceKit-LSP) for code intelligence |
| `synthflow` | available | 0 | 0 | 0 | — | — | Connects Claude Code to the Synthflow AI voice-agent platform through its hosted MCP server, with skills for reviewing calls and auditing agent prompts, plus a… |
| `tavily` | available | 0 | 0 | 0 | — | — | Build AI applications with real-time web data using Tavily's search, extract, crawl, and research APIs. |
| `teamcity-cli` | available | 0 | 0 | 0 | — | — | Agent skill for interacting with TeamCity CI/CD using the teamcity CLI. Enables Claude to explore builds, view logs, start jobs, manage queues, agents, and mor… |
| `telegram` | available | 2 | 0 | 0 | — | telegram | Telegram messaging bridge with built-in access control. Manage pairing, allowlists, and policy via /telegram:access. |
| `terraform` | available | 0 | 0 | 0 | — | terraform | The Terraform MCP Server provides seamless integration with Terraform ecosystem, enabling advanced automation and interaction capabilities for Infrastructure a… |
| `togetherai-skills` | available | 0 | 0 | 0 | — | — | Agent Skills for Together AI platform — inference, training, embeddings, audio, video, images, function calling, and infrastructure. Covers serverless chat com… |
| `twilio-developer-kit` | available | 0 | 0 | 0 | — | — | Twilio Skills provide procedural knowledge for AI coding agents — which APIs to use, in what order, and what to avoid. Covers SMS, Voice, WhatsApp, Verify, Sen… |
| `typescript-lsp` | available | 0 | 0 | 0 | — | — | TypeScript/JavaScript language server for enhanced code intelligence |
| `ui-theme-designer` | available | 0 | 0 | 0 | — | — | Plugin for coding agents working with UI theme designer. Bundles two skills: how-to and conceptual answers about UI theme designer on BTP, and questions about… |
| `ui5` | available | 0 | 0 | 0 | — | — | SAPUI5 / OpenUI5 plugin for coding agents. Create and validate UI5 projects, access API documentation, run UI5 linter, get development guidelines and best prac… |
| `ui5-modernization` | available | 0 | 0 | 0 | — | — | Complete UI5 modernization toolkit with workflow and specialized fix patterns for modernizing SAPUI5/OpenUI5 applications. |
| `ui5-typescript-conversion` | available | 0 | 0 | 0 | — | — | SAPUI5 / OpenUI5 plugin for coding agents. Convert JavaScript based UI5 projects to TypeScript. |
| `unity` | available | 0 | 0 | 0 | — | — | Unity's official plugin for Claude Code, with curated skills for game development, monetization, and performance optimization. |
| `unreal-engine-skills-for-claude-code` | available | 0 | 0 | 0 | — | — | Control Unreal Editor directly from Claude Code via MCP. Hundreds of tools exposed via Unreal's ToolsetRegistry across 30+ toolsets: actors, blueprints, materi… |
| `valtown` | available | 0 | 0 | 0 | — | — | Build and deploy on Val Town. Bundles the Val Town MCP server and platform skills (HTTP vals, cron/intervals, SQLite, email, OAuth, React UI, third-party integ… |
| `vanguard-advisor-tools` | available | 0 | 0 | 0 | — | — | Vanguard Advisor Tools for financial professionals: research and compare funds and ETFs across the industry and prepare for client conversations, using Vanguar… |
| `vanta` | available | 0 | 0 | 0 | — | — | The Vanta plugin connects Claude Code to Vanta's security and compliance platform through the Vanta MCP server. It combines Vanta's test-specific remediation i… |
| `vanta-mcp-plugin` | available | 0 | 0 | 0 | — | — | The Vanta plugin connects Claude Code to Vanta's security and compliance platform through the Vanta MCP server. It combines Vanta's test-specific remediation i… |
| `vercel` | available | 0 | 0 | 0 | — | — | Vercel deployment platform integration. Manage deployments, check build status, access logs, configure domains, and control your frontend infrastructure direct… |
| `vibe-prospecting` | available | 0 | 0 | 0 | — | — | Vibe Prospecting connects Claude to live B2B company and contact data so users can search, match, enrich, filter, and export prospects at scale. It turns natur… |
| `vsql-extension-builder` | available | 0 | 0 | 0 | — | — | Builds a VillageSQL extension for MySQL end-to-end through a 7-phase persona-driven workflow. Commonly used to port PostgreSQL extensions to MySQL. |
| `windsor-ai` | available | 0 | 0 | 0 | — | — | Connect Claude Code to 325+ business data sources via Windsor.ai. Query marketing, sales, CRM, ecommerce, finance, and analytics data from Google Ads, Meta, Hu… |
| `wingspan` | available | 0 | 0 | 0 | — | — | Ask Claude about the contractors you pay through Wingspan, what you owe them, and what is holding up a payment, then onboard contractors and log payments as dr… |
| `wix` | available | 0 | 0 | 0 | — | — | Build, manage, and deploy Wix sites and apps. CLI development skills for dashboard extensions, backend APIs, site widgets, and service plugins with the Wix Des… |
| `workos` | available | 0 | 0 | 0 | — | — | WorkOS integration skills for AuthKit, SSO, Directory Sync, RBAC, Vault, Audit Logs, migrations, and API references. |
| `youdotcom-agent-skills` | available | 0 | 0 | 0 | — | — | You.com agent skills for web search, research with citations, and content extraction. Guided integrations for Vercel AI SDK, Claude Agent SDK, OpenAI Agents SD… |
| `zapier` | available | 0 | 0 | 0 | — | — | Connect 8,000+ apps to your AI workflow. Discover, enable, and execute Zapier actions directly from your client. |
| `zilliz` | available | 0 | 0 | 0 | — | — | Zilliz Cloud management plugin with 14 skills covering cluster lifecycle, collection schema, vector search, index tuning, bulk import, RBAC, backups, and monit… |
| `zocks-advisor` | available | 0 | 0 | 0 | — | — | Seven skills for financial advisors built on Zocks meeting intelligence: client behavioral profiles, attrition-risk ranking, held-away asset radar, client jour… |
| `zoom-plugin` | available | 0 | 0 | 0 | — | — | Claude plugin for planning, building, and debugging Zoom integrations across REST APIs, SDKs, webhooks, bots, and MCP workflows. |
| `zoominfo` | available | 0 | 0 | 0 | — | — | Search companies and contacts, enrich leads, find lookalikes, and get AI-ranked contact recommendations. Pre-built skills chain multiple ZoomInfo tools into co… |
| `zscaler` | available | 0 | 0 | 0 | — | — | Manage Zscaler cloud security platform including ZPA (private access), ZIA (internet access), ZDX (digital experience), ZCC (client connector), EASM (attack su… |
| `zyte-web-data` | available | 0 | 0 | 0 | — | — | Web scraping skills for Claude Code powered by the Zyte API — scrape sites, generate and run Scrapy spiders, define extraction schemas, and ship to Scrapy Clou… |

## knowledge-work-plugins

`anthropics/knowledge-work-plugins` · Anthropic · trust: official

| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |
|---|---|---|---|---|---|---|---|
| `cowork-plugin-management` | **active** | 2 | 0 | 0 | — | — | Create, customize, and manage plugins tailored to your organization's tools and workflows. Configure MCP servers, adjust plugin behavior, and adapt templates t… |
| `data` | **active** | 10 | 0 | 0 | — | amplitude, amplitude-eu, atlassian, bigquery, databricks, definite, hex, snowflake | Write SQL, explore datasets, and generate insights faster. Build visualizations and dashboards, and turn raw data into clear stories for stakeholders. |
| `design` | **active** | 7 | 0 | 0 | — | asana, atlassian, figma, gmail, google calendar, intercom, linear, notion, slack | Accelerate design workflows — critique, design system management, UX writing, accessibility audits, research synthesis, and dev handoff. From exploration to pi… |
| `engineering` | **active** | 10 | 0 | 0 | — | asana, atlassian, datadog, github, gmail, google calendar, linear, notion, pagerduty, slack | Streamline engineering workflows — standups, code review, architecture decisions, incident response, and technical documentation. Works with your existing tool… |
| `pdf-viewer` | **active** | 1 | 0 | 4 | — | pdf | View, annotate, and sign PDFs in a live interactive viewer. Mark up contracts, fill forms with visual feedback, stamp approvals, and place signatures — then do… |
| `productivity` | **active** | 4 | 0 | 0 | — | asana, atlassian, clickup, gmail, google calendar, linear, monday, notion, slack | Manage tasks, plan your day, and build up memory of important context about your work. Syncs with your calendar, email, and chat to keep everything organized a… |
| `activecampaign` | available | 0 | 0 | 0 | — | — | Marketing automation, CRM, and email marketing powered by ActiveCampaign. Manage contacts, campaigns, automations, deals, and get AI-powered marketing insights… |
| `adobe-for-creativity` | available | 0 | 0 | 0 | — | — | Brings together Adobe Creative Cloud tools for images, vectors, design, and video. Edit multiple assets at once, adapt for different platforms, and complete mu… |
| `adspirer-ads-agent` | available | 0 | 0 | 0 | — | — | Cross-platform ad management for Google Ads, Meta Ads, TikTok Ads, and LinkedIn Ads. 91 tools for keyword research, campaign creation, performance analysis, an… |
| `ai-firstify` | available | 0 | 0 | 0 | — | — | AI-first project auditor and re-engineer based on the 9 design principles and 7 design patterns from the TechWolf AI-First Bootcamp |
| `airtable` | available | 0 | 0 | 0 | — | — | Airtable is the database and operations layer for your agents — whether running product, marketing, sales, ops, HR, or a custom business app. It combines struc… |
| `airwallex-agentos` | available | 0 | 0 | 0 | — | — | Bring Airwallex's global financial infrastructure to Claude. Orchestrate actions across your account in plain language, e.g., set up invoices from a PO, onboar… |
| `amazon-selling-partner` | available | 0 | 0 | 0 | — | — | Connect your Amazon Seller Central account to Claude. Ask about sales, inventory, and listing performance and get recommendations grounded in your own data, th… |
| `apollo` | available | 3 | 0 | 0 | — | apollo | Prospect, enrich leads, and load outreach sequences with Apollo.io — one-click MCP server integration for Claude Code and Cowork. |
| `atlan` | available | 0 | 0 | 0 | — | — | Atlan data catalog plugin for Claude Code. Search, explore, govern, and manage your data assets through natural language. Powered by the Atlan MCP server with… |
| `auth0` | available | 0 | 0 | 0 | — | — | Essential Auth0 skills including quickstarts, migration from other providers, and Multi-Factor Authentication (MFA). |
| `b12-claude-plugin` | available | 0 | 0 | 0 | — | — | B12 plugin with two skills: Website Generator (create a B12 website from a brief description) and B12 Website Editor (edit a live B12 website using Claude's br… |
| `base44` | available | 0 | 0 | 0 | — | — | Build and deploy Base44 full-stack apps with CLI project management and JavaScript/TypeScript SDK development skills |
| `bigdata-com` | available | 0 | 0 | 0 | — | — | Official Bigdata.com plugin providing financial research, analytics, and intelligence tools powered by Bigdata MCP. |
| `bio-research` | available | 6 | 0 | 0 | — | benchling, biorender, biorxiv, c-trials, chembl, consensus, ot, owkin, pubmed, synapse, wiley | Connect to preclinical research tools and databases (literature search, genomics analysis, target prioritization) to accelerate early-stage life sciences R&D |
| `blackrock-advisor-center-plugin` | available | 0 | 0 | 0 | — | — | BlackRock Advisor Center 360° skills for financial advisors: portfolio review, opportunity and fund-health checks, guided benchmark selection, guided portfolio… |
| `box` | available | 0 | 0 | 0 | — | — | Work with your Box content directly from Claude Code — search files, organize folders, collaborate with your team, and use Box AI to answer questions, summariz… |
| `brand-voice` | available | 3 | 5 | 3 | — | atlassian, box, figma, gong, granola, notion | Discover your brand voice from existing documents and conversations, generate enforceable guidelines, and validate AI-generated content against your establishe… |
| `brightdata-plugin` | available | 0 | 0 | 0 | — | — | Web scraping, Google search, structured data extraction, and MCP server integration powered by Bright Data. Includes 7 skills: scrape any webpage as markdown (… |
| `browser-use` | available | 0 | 0 | 0 | — | — | Give Claude a real browser — your Chrome or a Browser Use Cloud browser. Use it whenever a task involves a website or web app: browsing, scraping and data extr… |
| `buildkite` | available | 0 | 0 | 0 | — | — | Official Buildkite skills for Claude Code, Cursor, and other AI coding agents — pipelines, migration, preflight, agent runtime, CLI, and API |
| `canva` | available | 0 | 0 | 0 | — | — | Create, edit, review, resize, and brand-check Canva designs with the Canva MCP server. |
| `carbone-skill` | available | 0 | 0 | 0 | — | — | Official Carbone skill — complete templating language reference covering tags, loops, conditions, formatters, aggregators, and all output formats (DOCX, XLSX,… |
| `carta-cap-table` | available | 0 | 0 | 0 | — | — | Carta Cap Table plugin — skills and hooks for querying cap tables, grants, SAFEs, 409A valuations, waterfall scenarios, and more |
| `carta-crm` | available | 0 | 0 | 0 | — | — | Manage the Carta CRM conversationally — search, add, update, and enrich investors, companies, contacts, deals, notes, and fundraisings via the Carta CRM MCP Se… |
| `carta-investors` | available | 0 | 0 | 0 | — | — | Carta Investors plugin — skills for querying investors data, performance benchmarks, regulatory reporting, AGM deck generation, brand extraction, and more via… |
| `chronograph-gp` | available | 0 | 0 | 0 | — | — | Portfolio monitoring, valuations and analytics for private-capital GP teams using the Chronograph connector: portfolio-company one-pagers, fund quarterly revie… |
| `chronograph-lp` | available | 0 | 0 | 0 | — | — | Portfolio monitoring and analytics for private-capital LP teams using the Chronograph connector: cashflow forecasting, commitment pacing, look-through exposure… |
| `claude-for-financial-advisors` | available | 0 | 0 | 0 | — | — | Ready-to-run workflows for financial advisors in Claude Cowork, drawing live data from the tools their firm already uses through third-party connectors. The pl… |
| `clickhouse` | available | 0 | 0 | 0 | — | — | ClickHouse Claude Code plugin: skills (ClickHouse best practices), rules and MCP. |
| `cloudinary` | available | 0 | 0 | 0 | — | — | Use Cloudinary directly in Claude. Manage assets, apply transformations, optimize media, and more through natural conversation. |
| `cockroachdb` | available | 0 | 0 | 0 | — | — | CockroachDB plugin for Claude Code — explore schemas, write optimized SQL, debug queries, and manage distributed database clusters directly from your AI coding… |
| `common-room` | available | 6 | 0 | 2 | — | common-room | Turn Common Room into your GTM copilot. Research accounts and contacts, prep for calls with attendee profiles and talking points, and draft personalized outrea… |
| `customer-support` | available | 5 | 0 | 0 | — | atlassian, gmail, google calendar, guru, hubspot, intercom, notion, slack | Triage tickets, draft responses, escalate issues, and build your knowledge base. Research customer context and turn resolved issues into self-service content. |
| `daloopa` | available | 0 | 0 | 0 | — | — | Financial analysis skills powered by Daloopa's institutional-grade data |
| `datadog` | available | 0 | 0 | 0 | — | — | Use Datadog directly in Claude Code through a preconfigured Datadog MCP server. Query logs, metrics, traces, dashboards, and more through natural conversation.… |
| `datarobot-agent-skills` | available | 0 | 0 | 0 | — | — | DataRobot skills for AI/ML workflows — model training, deployment, predictions, feature engineering, monitoring, explainability, data preparation, App Framewor… |
| `desktop-commander` | available | 0 | 0 | 0 | — | — | MCP server for terminal commands, process management, and file operations across text, code, PDF, DOCX, Excel, images, and structured data. |
| `dropbox` | available | 0 | 0 | 0 | — | — | The Dropbox plugin for Claude connects your Dropbox files directly to Claude, so you can search, organize, save generated content, and create sharing links wit… |
| `enterprise-search` | available | 5 | 0 | 0 | — | asana, atlassian, gmail, google calendar, guru, notion, slack | Search across all of your company's tools in one place. Find anything across email, chat, documents, and wikis without switching between apps. |
| `exa` | available | 0 | 0 | 0 | — | — | Exa AI web search, deep research, and content extraction. Provides MCP tools and research skills for comprehensive web search, people discovery, company resear… |
| `fastly-agent-toolkit` | available | 0 | 0 | 0 | — | — | Fastly development tools and platform skills |
| `figma` | available | 0 | 0 | 0 | — | — | Figma design platform integration. Access design files, extract component information, read design tokens, and translate designs into code. Bridge the gap betw… |
| `finance` | available | 8 | 0 | 0 | — | bigquery, databricks, gmail, google calendar, slack, snowflake | Streamline finance and accounting workflows, from journal entries and reconciliation to financial statements and variance analysis. Speed up audit prep, month-… |
| `gc-ai` | available | 0 | 0 | 0 | — | — | Work in your GC AI legal knowledge base from Claude: upload documents, run review playbooks, and ask questions grounded in your own files, all as you. |
| `gitkraken` | available | 0 | 0 | 0 | — | — | Gives Claude access to your real Git and project context: commits, branches, pull requests, and issues across every repo you work in. Works with GitHub, GitLab… |
| `govtribe` | available | 0 | 0 | 0 | — | — | Government contracting research and capture workflows in Claude: opportunity and pipeline briefs, bid/no-bid and competitor analysis, price-to-win and proposal… |
| `grafana-assistant` | available | 0 | 0 | 0 | — | — | Skills and rules for developing and using the Grafana Assistant app and CLI. |
| `grafana-cloud-mcp` | available | 0 | 0 | 0 | — | — | Hosted MCP server for AI-assisted Grafana Cloud observability — no local installation required. |
| `grasp` | available | 0 | 0 | 0 | — | — | Deal-work workflows powered by Grasp company lookup, table creation, import, buyer, transaction, table enrichment, contact, and market research tools. |
| `growthbook` | available | 0 | 0 | 0 | — | — | A suite of agent skills for the full GrowthBook feature flag and experimentation lifecycle. |
| `honeycomb` | available | 0 | 0 | 0 | — | — | Skills, agents, and workflows for Honeycomb observability — query patterns, production investigations, SLOs, OpenTelemetry instrumentation, and Beeline migrati… |
| `hostinger` | available | 0 | 0 | 0 | — | — | Deploy, manage and monitor Hostinger services — Websites, Domains, Ecommerce, Email Marketing, Subscriptions & Payments, and VPS. Authenticate via browser (OAu… |
| `hubspot-sales` | available | 0 | 0 | 0 | — | — | Run your HubSpot sales workflow directly from Claude. Adds skills that cover the full sales day: import contacts and deals into HubSpot, get a prioritised morn… |
| `human-resources` | available | 9 | 0 | 0 | — | atlassian, gmail, google calendar, notion, slack | Streamline people operations — recruiting, onboarding, performance reviews, compensation analysis, and policy guidance. Maintain compliance and keep your team… |
| `incident-io` | available | 0 | 0 | 0 | — | — | Work with incident.io from Claude: respond to and investigate incidents, check on-call schedules and escalations, and author the runbooks, skills and architect… |
| `informatica-for-claude-platform` | available | 0 | 0 | 0 | — | — | Governed catalog discovery for Informatica Intelligent Data Management Cloud (CDGC): find tables, columns, files, glossary terms and policies across the enterp… |
| `intercom` | available | 0 | 0 | 0 | — | — | Intercom integration for Claude Code. Search conversations, analyze customer support patterns, look up contacts and companies, and install the Intercom Messeng… |
| `intuit-quickbooks` | available | 0 | 0 | 0 | — | — | QuickBooks business insights and actions: financial health briefings across P&L, cash flow, balance sheet and A/R, industry benchmarking, payroll cost analysis… |
| `langfuse` | available | 0 | 0 | 0 | — | — | Skills for working with Langfuse, the open-source LLM engineering platform for tracing, prompt management, and evaluation. |
| `leadfeeder` | available | 0 | 0 | 0 | — | — | Turn website visitor signals into pipeline with Leadfeeder: daily visitor briefs, visitor company research, buyer and contact discovery, personalised outreach… |
| `learn-with-coursera` | available | 0 | 0 | 0 | — | — | Turn any learning intent into a personalized Coursera experience. Asks three quick questions (topic, familiarity, preferred format), searches Coursera's catalo… |
| `legal` | available | 9 | 0 | 0 | — | atlassian, box, docusign, egnyte, gmail, google calendar, slack | Speed up contract review, NDA triage, and compliance workflows for in-house legal teams. Draft legal briefs, organize precedent research, and manage institutio… |
| `lseg` | available | 0 | 0 | 0 | — | — | Price bonds, analyze yield curves, evaluate FX carry trades, value options, and build macro dashboards using LSEG financial data and analytics. |
| `lusha` | available | 0 | 0 | 0 | — | — | Prospect, enrich, and build call-ready lead lists using Lusha's B2B intelligence platform — verified phone numbers, company signals, and lookalike targeting. |
| `marketing` | available | 8 | 0 | 0 | — | ahrefs, amplitude, amplitude-eu, canva, figma, gmail, google calendar, hubspot, klaviyo, notion, similarweb, slack, supermetrics | Create content, plan campaigns, and analyze performance across marketing channels. Maintain brand voice consistency, track competitors, and report on what's wo… |
| `maven-bio` | available | 0 | 0 | 0 | — | — | Evidence-backed BioPharma research workflows over Maven Bio's drug, trial, company, and deal knowledge graph. Skills for competitive pipelines, indication land… |
| `mintlify` | available | 0 | 0 | 0 | — | — | Build beautiful documentation sites with Mintlify. Convert non-markdown files into properly formatted MDX pages, add and modify content with correct component… |
| `miro` | available | 0 | 0 | 0 | — | — | Secure access to Miro boards. Enables AI to read board context, create diagrams, and generate code with enterprise-grade security. |
| `modern-web-guidance` | available | 0 | 0 | 0 | — | — | Keep your coding agent up to date with the latest web best practices |
| `monday-com` | available | 0 | 0 | 0 | — | — | The official monday.com plugin for Claude Cowork. Manage boards, items, docs, and forms across work management, CRM, dev, service, and campaigns. Full read and… |
| `monday-crm` | available | 0 | 0 | 0 | — | — | Run your monday CRM in plain language. Build a pipeline from scratch, start the day with a ranked deal briefing, spin up a forecast dashboard, audit board heal… |
| `netsuite-ai-companion` | available | 0 | 0 | 0 | — | — | Guides AI assistants that use the NetSuite AI Connector: tool-selection order, output formatting, NetSuite domain knowledge, multi-subsidiary and currency hand… |
| `netsuite-finance-analyst` | available | 0 | 0 | 0 | — | — | Director-level finance analysis on live NetSuite data: financial reporting, period close, variance, aging and reconciliation reviews, cash reporting, and board… |
| `nimble` | available | 0 | 0 | 0 | — | — | Nimble web data toolkit — search, extract, map, crawl the web and work with structured data agents |
| `noibu` | available | 0 | 0 | 0 | — | — | Built for ecommerce, the Noibu plugin bridges the gap between customer experience and revenue by connecting Claude directly to your store's session, error, and… |
| `operations` | available | 9 | 0 | 0 | — | asana, atlassian, gmail, google calendar, notion, slack | Optimize business operations — vendor management, process documentation, change management, capacity planning, and compliance tracking. Keep your organization… |
| `pendo-analytics` | available | 0 | 0 | 0 | — | — | Bring Pendo product analytics into Claude: account health, feature adoption, session replay lookup and triage, feedback analysis, and data-informed planning gr… |
| `pendo-guides` | available | 0 | 0 | 0 | — | — | Create production-ready Pendo in-app guides (walkthroughs, announcements, alerts, polls, promotions) as HTML/CSS/JS from a short intake conversation, using Pen… |
| `pendo-orchestrate` | available | 0 | 0 | 0 | — | — | Create, configure and edit draft Pendo Orchestrate email journeys, including multi-email and conditional split flows, via the Pendo connector. Journeys stay in… |
| `pixeltable` | available | 0 | 0 | 0 | — | — | Build multimodal AI applications with Pixeltable -- tables, computed columns, embedding search, UDFs, tool-calling agents, and 25+ AI provider integrations. |
| `planetscale` | available | 0 | 0 | 0 | — | — | An authenticated hosted MCP server that accesses your PlanetScale organizations, databases, branches, schema, and Insights data. Query against your data, surfa… |
| `postiz` | available | 0 | 0 | 0 | — | — | Social media automation CLI for scheduling posts, managing integrations, uploading media, and tracking analytics across 28+ platforms including X, LinkedIn, Re… |
| `prisma` | available | 0 | 0 | 0 | — | — | Prisma MCP integration for Postgres database management, schema migrations, SQL queries, and connection string management. Provision Prisma Postgres databases,… |
| `product-management` | available | 8 | 0 | 1 | — | amplitude, amplitude-eu, asana, atlassian, clickup, figma, fireflies, gmail, google calendar, intercom, linear, monday, notion, pendo, similarweb, slack | Write feature specs, plan roadmaps, and synthesize user research faster. Keep stakeholders updated and stay ahead of the competitive landscape. |
| `product-tracking-skills` | available | 0 | 0 | 0 | — | — | AI agent skills that make SaaS products data-ready for product analytics — from codebase scan to tracking plan to working instrumentation code. |
| `qdrant-skills` | available | 0 | 0 | 0 | — | — | Agent skills for Qdrant vector search: scaling, performance optimization, search quality, monitoring, deployment, model migration, version upgrades, and SDK us… |
| `qodo` | available | 0 | 0 | 0 | — | — | Bring Qodo's codebase intelligence, coding standards, and code review into your coding agent. |
| `qodo-standards` | available | 0 | 0 | 0 | — | — | Optional Qodo rules discovery and standards administration workflows. |
| `qt-development-skills` | available | 0 | 0 | 0 | — | — | Agentic engineering skills for Qt software development, including Qt C++/QML code review, QML coding, and Qt C++/QML code documentation. These skills use AI an… |
| `render` | available | 0 | 0 | 0 | — | — | Deploy, debug, and monitor applications on Render: skills for blueprints, deploys and troubleshooting, a Render assistant agent, deploy/status commands, a rend… |
| `sales` | available | 36 | 0 | 0 | — | apollo, atlassian, calendly, clay, close, crunchbase, fireflies, gmail, gong, google calendar, google drive, hubspot, lusha, microsoft-365, monday, notion, otter-ai, outreach, salesforce, similarweb, slack, zoom, zoominfo | Prep calls, summarize and follow up, research accounts, review deals and pipeline, and write the forecast, using the CRM, email, calendar and chat tools your t… |
| `sanity-plugin` | available | 0 | 0 | 0 | — | — | Sanity content platform integration with MCP server, agent skills, and slash commands. Query and author content, build and optimize GROQ queries, design schema… |
| `searchfit-seo` | available | 0 | 0 | 0 | — | — | Free AI-powered SEO toolkit — audit websites, plan content strategy, optimize pages, generate schema markup, cluster keywords, and track AI visibility. Works w… |
| `security-guidance` | available | 0 | 0 | 0 | — | — | Security review for Claude-generated code. Pattern-based warnings on edits, LLM-powered diff review on Stop, and an agentic commit reviewer that catches inject… |
| `servicenow-sdk` | available | 0 | 0 | 0 | — | — | Create, edit, and deploy ServiceNow applications with the Fluent SDK effortlessly through Claude. Helps developers build, extend, and manage ServiceNow applica… |
| `signoz` | available | 0 | 0 | 0 | — | — | Official SigNoz plugin for MCP setup, docs, queries, dashboards, and alerts |
| `slack-by-salesforce` | available | 2 | 0 | 5 | — | slack | Slack integration for searching messages, sending communications, managing canvases, and more |
| `small-business` | available | 44 | 0 | 0 | — | airwallex-agentos, apollo-io, atlassian-rovo, canva, clay, docusign, emergent, expensify, gmail, google-calendar, google-drive, gusto, hubspot, intuit-mailchimp, intuit-quickbooks, monday-com, myob, notion, paypal, ramp, ringex-chat, shopify, slack, square, stripe, tiktok, trello, wix, xero, zapier, zoho-books, zoho-crm, zoho-desk, zoho-projects, zoom | Pre-built small business workflows to help you run and grow your business. Supports a majority of the tools you already use. You approve every step that touche… |
| `sp-global` | available | 0 | 0 | 0 | — | — | S&P Global - Financial data and analytics skills including company tearsheets, earnings previews, and transaction summaries |
| `stackhawk-api` | available | 0 | 0 | 0 | — | — | Query the StackHawk platform API for security posture reporting, findings analysis, and app management. Guides agents through authentication, data retrieval, a… |
| `stackhawk-hawkscan` | available | 0 | 0 | 0 | — | — | Configure, run, and interpret HawkScan DAST results. Generates stackhawk.yml configs, runs scans via CLI or Docker, and transforms security findings into prior… |
| `synthflow` | available | 0 | 0 | 0 | — | — | Connects Claude Code to the Synthflow AI voice-agent platform through its hosted MCP server, with skills for reviewing calls and auditing agent prompts, plus a… |
| `tavily` | available | 0 | 0 | 0 | — | — | Build AI applications with real-time web data using Tavily's search, extract, crawl, and research APIs. |
| `tinyfish` | available | 0 | 0 | 0 | — | — | The complete web toolkit for your agent. Search the web and get answers in milliseconds. Fetch any URL and get clean markdown content back. Send a browser agen… |
| `twilio-developer-kit` | available | 0 | 0 | 0 | — | — | Twilio Skills provide procedural knowledge for AI coding agents — which APIs to use, in what order, and what to avoid. Covers SMS, Voice, WhatsApp, Verify, Sen… |
| `unity` | available | 0 | 0 | 0 | — | — | Unity's official plugin for Claude Code, with curated skills for game development, monetization, and performance optimization. |
| `unstructured-foundation` | available | 0 | 0 | 0 | — | — | Connect sources and search processed documents with Unstructured Foundation. Provides MCP access to source setup, processing status, document search, and docum… |
| `valtown` | available | 0 | 0 | 0 | — | — | Build and deploy on Val Town. Bundles the Val Town MCP server and platform skills (HTTP vals, cron/intervals, SQLite, email, OAuth, React UI, third-party integ… |
| `vanguard-advisor-tools` | available | 0 | 0 | 0 | — | — | Vanguard Advisor Tools for financial professionals: research and compare funds and ETFs across the industry and prepare for client conversations, using Vanguar… |
| `vanta-mcp-plugin` | available | 0 | 0 | 0 | — | — | The Vanta plugin connects Claude to Vanta's security and compliance platform through the Vanta MCP server. List failing compliance tests, get test-specific rem… |
| `vibe-prospecting` | available | 0 | 0 | 0 | — | — | Vibe Prospecting connects Claude to live B2B company and contact data so users can search, match, enrich, filter, and export prospects at scale. It turns natur… |
| `wingspan` | available | 0 | 0 | 0 | — | — | Ask Claude about the contractors you pay through Wingspan, what you owe them, and what is holding up a payment, then onboard contractors and log payments as dr… |
| `wix` | available | 0 | 0 | 0 | — | — | Build, manage, and deploy Wix sites and apps. Includes CLI development skills and Wix MCP server for site management, eCommerce, CMS, dashboard extensions, and… |
| `zapier` | available | 0 | 0 | 0 | — | — | Connect 8,000+ apps to your AI workflow. Discover, enable, and execute Zapier actions directly from your client. |
| `zocks-advisor` | available | 0 | 0 | 0 | — | — | Seven skills for financial advisors built on Zocks meeting intelligence: client behavioral profiles, attrition-risk ranking, held-away asset radar, client jour… |
| `zoom-plugin` | available | 30 | 0 | 0 | — | zoom-docs-mcp, zoom-mcp, zoom-whiteboard-mcp | Plan, build, and debug Zoom integrations across REST APIs, Meeting SDK, Video SDK, webhooks, bots, and MCP workflows. Search meetings, retrieve recordings, acc… |
| `zoominfo` | available | 0 | 0 | 0 | — | — | Search companies and contacts, enrich leads, find lookalikes, and get AI-ranked contact recommendations. Pre-built skills chain multiple ZoomInfo tools into co… |

## anthropic-agent-skills

`anthropics/skills` · Anthropic · trust: official

| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |
|---|---|---|---|---|---|---|---|
| `document-skills` | **active** | 4 | 0 | 0 | — | — | Collection of document processing suite including Excel, Word, PowerPoint, and PDF capabilities |
| `example-skills` | **active** | 12 | 0 | 0 | — | — | Collection of example skills demonstrating various capabilities including skill creation, MCP building, visual design, algorithmic art, internal communications… |
| `academy-guide` | available | 1 | 0 | 0 | — | — | Recommends relevant Claude Academy courses, tutorials, and use cases when users ask how to use Claude |
| `claude-api` | available | 1 | 0 | 0 | — | — | Claude API and SDK documentation skill for building LLM-powered applications |
| `discernment-nudge` | available | 1 | 0 | 0 | — | — | Appends two or three short follow-up questions after a substantive answer to help users check key facts, probe the reasoning, and notice missing context |

## claude-for-financial-services

`anthropics/financial-services-plugins` · Anthropic · trust: official

| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |
|---|---|---|---|---|---|---|---|
| `market-researcher` | **active** | 5 | 1 | 0 | — | — | Sector or theme to industry overview, competitive landscape, peer comps, and ideas shortlist |
| `claude-for-msft-365-install` | available | 0 | 0 | 9 | — | — | Provision direct cloud access (Vertex AI, Bedrock, or LLM gateway) for the Claude Microsoft 365 add-in. Generates the customized manifest, walks through Azure… |
| `earnings-reviewer` | available | 6 | 1 | 0 | — | — | Earnings call and filings to model update to note draft |
| `equity-research` | available | 9 | 0 | 9 | — | — | Equity research tools: earnings analysis, initiating coverage reports, and research workflows |
| `financial-analysis` | available | 13 | 0 | 7 | — | aiera, box, chronograph, daloopa, egnyte, factset, lseg, moodys, morningstar, mtnewswire, pitchbook, sp-global | Core financial modeling and analysis tools: DCF, comps, LBO, 3-statement models, competitive analysis, and deck QC |
| `fund-admin` | available | 6 | 0 | 0 | — | — | Fund administration and finance ops: GL reconciliation, break tracing, accruals, roll-forwards, variance commentary, NAV tie-out |
| `gl-reconciler` | available | 4 | 1 | 0 | — | — | Finds breaks, traces root cause, routes for sign-off |
| `investment-banking` | available | 9 | 0 | 7 | — | mcpServers | Investment banking productivity tools - client and market insights, deck creation, financial analysis, and transaction management |
| `kyc-screener` | available | 3 | 1 | 0 | — | — | Parses onboarding docs, runs the rules engine, flags gaps |
| `lseg` | available | 8 | 0 | 8 | — | lseg | Price bonds, analyze yield curves, evaluate FX carry trades, value options, and build macro dashboards using LSEG financial data and analytics. |
| `meeting-prep-agent` | available | 4 | 1 | 0 | — | — | Briefing pack before every client meeting |
| `model-builder` | available | 6 | 1 | 0 | — | — | DCF, LBO, 3-statement, comps - live in Excel |
| `month-end-closer` | available | 5 | 1 | 0 | — | — | Accruals, roll-forwards, variance commentary |
| `operations` | available | 2 | 0 | 0 | — | — | Operational workflows: KYC document parsing and rules-grid evaluation |
| `pitch-agent` | available | 11 | 1 | 0 | — | — | Comps, precedents, LBO to a branded pitch deck, end to end |
| `private-equity` | available | 10 | 0 | 10 | — | mcpServers | Private equity deal sourcing and workflow tools: company discovery, CRM integration, and founder outreach |
| `sp-global` | available | 3 | 0 | 0 | — | spglobal | S&P Global - Financial data and analytics skills including company tearsheets, earnings previews, and transaction summaries |
| `statement-auditor` | available | 3 | 1 | 0 | — | — | Audits pre-generated LP statements before distribution |
| `valuation-reviewer` | available | 4 | 1 | 0 | — | — | Ingests GP packages, runs valuation template, stages LP reporting |

## claude-for-legal

`anthropics/claude-for-legal` · Anthropic · trust: official

| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |
|---|---|---|---|---|---|---|---|
| `ai-governance-legal` | **active** | 10 | 0 | 0 | — | Google Drive, Slack | Triages proposed AI use cases against your registry, runs impact assessments across the regimes in scope, reviews vendor AI terms for training-on-data and liab… |
| `cocounsel-legal` | available | 1 | 0 | 0 | — | cocounsel-legal | CoCounsel Legal delivers comprehensive Westlaw Deep Research reports with inline, linked citations to Westlaw and Practical Law sources. |
| `commercial-legal` | available | 12 | 3 | 0 | — | Definely, DocuSign, Google Drive, Ironclad, Slack, TopCounsel, iManage | Reviews vendor agreements, NDAs, and SaaS subscriptions against your sales-side or purchasing-side playbook, tracks renewals and cancel-by deadlines before the… |
| `corporate-legal` | available | 13 | 1 | 0 | — | Box, Definely, Google Drive, Slack, Solve Intelligence, TopCounsel, iManage | Runs M&A diligence at scale with cited tabular review, builds disclosure schedules and closing checklists, drafts board consents and minutes in house format, a… |
| `employment-legal` | available | 20 | 1 | 0 | — | Google Drive, Slack | Reviews hires and terminations for jurisdiction-specific risk flags, classifies workers against the controlling state test, tracks leave deadlines before they'… |
| `ip-legal` | available | 12 | 1 | 0 | — | CourtListener, Descrybe, Google Drive, Slack, Solve Intelligence | Runs first-pass trademark clearance and freedom-to-operate triage, screens invention disclosures for initial patentability, drafts and triages cease-and-desist… |
| `law-student` | available | 13 | 0 | 0 | — | CourtListener, Descrybe, Google Drive, Slack | Drills Socratically, briefs cases, builds outlines, runs bar prep sessions tuned to your jurisdiction, grades IRAC practice, and plans the study schedule — wit… |
| `legal-builder-hub` | available | 10 | 1 | 0 | — | Google Drive, Lawve AI, Slack | Finds, evaluates, and installs community legal skills — with a security review gate before anything lands in your environment. |
| `legal-clinic` | available | 16 | 0 | 0 | — | CourtListener, Courtroom5, Descrybe, Google Drive, Slack | Sets up the clinic, onboards students, runs structured intake, tracks deadlines with malpractice-aware caution, and hands off cases at semester end — built wit… |
| `litigation-legal` | available | 19 | 1 | 0 | — | Aurora, CourtListener, Everlaw, Google Drive, Slack, TopCounsel, Trellis | Manages the litigation portfolio — matters, deadlines, holds, demands, outside counsel — and does the work: claim charts (patent and civil), chronologies, depo… |
| `privacy-legal` | available | 9 | 0 | 0 | — | Google Drive, Slack | Triages processing activities, generates PIAs, reviews DPAs as controller or processor, drafts DSAR responses within statutory timelines, and monitors policy d… |
| `product-legal` | available | 7 | 1 | 0 | — | Asana, Atlassian, Google Drive, Linear, Slack | Reviews product launches against your risk calibration, answers 'is this a problem?' questions in minutes, checks marketing copy for claims that need substanti… |
| `regulatory-legal` | available | 9 | 1 | 0 | — | Google Drive, Slack | Watches regulatory feeds, diffs new rules against your policy library, tracks comment deadlines and open gaps, and writes the digest your team reads Monday mor… |

## copilot-plugins

`github/copilot-plugins` · GitHub · trust: official

| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |
|---|---|---|---|---|---|---|---|
| `advanced-security` | available | 0 | 0 | 0 | — | — | Advanced Security plugin for GitHub Copilot. |
| `azure-devops-copilot-plugin` | available | 0 | 0 | 0 | — | — | Bring Azure DevOps work-item, repository, and pull-request workflows into GitHub Copilot. |
| `build-perf-cpp` | available | 1 | 0 | 0 | sessionStart, userPromptSubmitted | — | Analyze MSVC build performance using vcperf.exe and ETL traces. |
| `canvas-apps` | available | 0 | 0 | 0 | — | — | Build Power Apps Canvas Apps using the Canvas Authoring MCP server. |
| `code-apps-preview` | available | 0 | 0 | 0 | — | — | Build and deploy Power Apps code apps using React, Vite, and Power Platform connectors. |
| `cpp-language-server` | available | 0 | 0 | 0 | — | — | Navigate and interact with your C++ code using the Microsoft C++ Language Server. |
| `dataverse` | available | 0 | 0 | 0 | — | — | Microsoft Dataverse plugin for coding agents, covering record CRUD, bulk data operations, advanced queries, schema and metadata, administration, security, envi… |
| `fabric-skills` | available | 0 | 0 | 0 | — | — | Complete bundle: all Microsoft Skills for Fabric for developers and consumers. |
| `mcp-apps` | available | 0 | 0 | 0 | — | — | Generate MCP App widgets for MCP tools. Produces self-contained HTML widgets using the MCP Apps protocol. |
| `microsoft-365-agents-toolkit` | available | 0 | 0 | 0 | — | — | Toolkit for building Microsoft 365 Copilot declarative agents — scaffolding, JSON manifest development, and capability configuration. |
| `mobile-app` | available | 0 | 0 | 0 | — | — | Build and deploy Power Apps code apps for mobile using Expo (React Native), with native device functionality and Power Platform connectors |
| `model-apps` | available | 0 | 0 | 0 | — | — | Build and deploy Power Apps generative pages for model-driven apps with specialist agents for planning, entity creation, and parallel code generation. Requires… |
| `power-automate` | available | 0 | 0 | 0 | — | — | Build, edit, run, and debug Power Automate cloud flows via the FlowAgent MCP server — connection lifecycle, surgical edits, copy across environments, run manag… |
| `power-pages` | available | 0 | 0 | 0 | — | — | Create and deploy Power Pages sites using modern development approaches. Supports code sites (SPAs) with React, Angular, Vue, or Astro. Includes ALM orchestrat… |
| `powerbi-authoring` | available | 0 | 0 | 0 | — | — | Developer skills for authoring Microsoft Power BI solutions. |
| `spark` | available | 0 | 0 | 0 | — | — | Spark plugin for GitHub Copilot. |
| `workiq` | available | 0 | 0 | 0 | — | — | Query Microsoft 365 data with natural language — emails, meetings, documents, Teams messages, and more. |
| `workiq-productivity` | available | 0 | 0 | 0 | — | — | WorkIQ productivity skills powered by the local WorkIQ CLI — read-only insights across email, meetings, calendar, Teams, SharePoint, projects, and people. |

## awesome-copilot

`github/awesome-copilot` · GitHub community · trust: community

| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |
|---|---|---|---|---|---|---|---|
| `accessibility-agents` | available | 0 | 0 | 0 | — | — | WCAG 2.2 AA enforcement as Agent Skills: six router skills that dispatch accessibility specialists for web, document, markdown, desktop and GitHub work, hooks… |
| `accessibility-kanban` | available | 0 | 0 | 0 | — | — | Kanban board to manage accessibility issues, allow you to plan, track, and complete remediation work. |
| `acreadiness-cockpit` | available | 0 | 0 | 0 | — | — | Drive Microsoft AgentRC from Copilot chat: assess AI readiness, generate Copilot instructions (flat or nested with applyTo globs for monorepos), and manage pol… |
| `agent-council` | available | 0 | 0 | 0 | — | — | A runtime-portable 5-agent quality gate that adjudicates text artifacts before they ship. Five role-conditioned LLM deliberators run a 2-round async protocol w… |
| `agent-radar` | available | 0 | 0 | 0 | — | — | See a live map of the Copilot agents on your computer, their sub-agents, their commands, and where their data goes. |
| `agentcouncil` | available | 0 | 0 | 0 | — | — | Multi-model council for Copilot CLI: three subagents on different model families (Anthropic, OpenAI, Google) answer independently, then build on each other or… |
| `ai-credits-breakdown` | available | 0 | 0 | 0 | — | — | See exactly where your own GitHub Copilot AI credits go: dollars by day, repository, model, call type and prompt-cache state, built privately on your computer… |
| `ai-ready` | available | 0 | 0 | 0 | — | — | Analyze any repository and generate AI-ready configuration — AGENTS.md, copilot-instructions.md, CI workflows, issue templates, and more. Mines your PR review… |
| `ai-team-orchestration` | available | 0 | 0 | 0 | — | — | Run a lightweight, role-separated AI development team with flexible tools, developer-selected models, proportionate planning, and optional QA. |
| `anarlog` | available | 0 | 0 | 0 | — | — | Query Anarlog meetings locally, or connect through OAuth to read opted-in Cloud snapshots. |
| `apify` | available | 0 | 0 | 0 | — | — | Helps devs extract data from any website with thousands of trusted scrapers, crawlers, and automations from Apify Store. Integrate ready-made Actors to access… |
| `apng-studio` | available | 0 | 0 | 0 | — | — | Interactive GitHub Copilot app canvas extension for building Animated PNG (APNG) files from frames. Draw or upload frames, tune per-frame timing and compositin… |
| `arcade-canvas` | available | 0 | 0 | 0 | — | — | Play six retro Phaser mini-games in a Copilot canvas while agents work. |
| `arch` | available | 0 | 0 | 0 | — | — | Architecture and modernization toolkit: produce a cited architecture document for a locally-cloned repo, and generate a phased modernization plan that auto-run… |
| `arize-ax` | available | 0 | 0 | 0 | — | — | Arize AX platform skills for LLM observability, evaluation, and optimization. Includes trace export, instrumentation, datasets, experiments, evaluators, AI pro… |
| `atlassian-twg-cli` | available | 0 | 0 | 0 | — | — | Installs and configures Atlassian Teamwork Graph CLI (`twg`) for use with GitHub Copilot. After setup, the CLI provides access to authorized work context acros… |
| `automate-this` | available | 0 | 0 | 0 | — | — | Record your screen doing a manual process, drop the video on your Desktop, and let Copilot CLI analyze it frame-by-frame to build working automation scripts. S… |
| `awesome-copilot` | available | 0 | 0 | 0 | — | awesome-copilot | Meta prompts that help you discover and generate curated GitHub Copilot agents, instructions, prompts, and skills. |
| `aws-cloud-development` | available | 0 | 0 | 0 | — | — | Comprehensive AWS cloud development tools including Infrastructure as Code, serverless functions, architecture patterns, and cost optimization for building sca… |
| `aws-core` | available | 0 | 0 | 0 | — | — | Build, deploy, and operate applications on AWS. Skills for infrastructure as code (CDK, CloudFormation), core services (Lambda, API Gateway, Step Functions, EC… |
| `azure` | available | 0 | 0 | 0 | — | — | Microsoft Azure MCP and Skills integration for cloud resource management, deployments, and Azure services. Manage your Azure infrastructure, monitor applicatio… |
| `azure-cloud-development` | available | 0 | 0 | 0 | — | — | Comprehensive Azure cloud development tools including Infrastructure as Code, serverless functions, architecture patterns, and cost optimization for building s… |
| `azure-cost-health-check` | available | 0 | 0 | 0 | — | — | Read-only Azure cost, forecasts, budget alerts, Advisor recommendations, and AI billing analysis in a Copilot canvas. |
| `azure-functions` | available | 0 | 0 | 0 | — | — | Create, edit, modernize, review, run, deploy, and monitor Azure Function Apps in a Copilot canvas, with optional AI help. Includes official function templates,… |
| `azure-functions-hosted-skills` | available | 0 | 0 | 0 | — | — | Build, run, and debug Azure Functions Hosted Skills locally or invoke supported functions in an existing Function App from a Copilot canvas. |
| `azure-resiliency-agent` | available | 0 | 0 | 0 | — | — | Validate Azure application architectures and infrastructure-as-code for resiliency gaps, generate new resilient templates, and review existing templates. |
| `azure-resources-query` | available | 0 | 0 | 0 | — | — | Browse Azure resources through read-only Resource Graph queries with explicit subscription selection in a Copilot canvas. |
| `azure-sre-agent` | available | 0 | 0 | 0 | — | — | Investigate failing Azure apps with your existing Azure SRE Agent through an interactive Copilot canvas. Review investigation threads and incident evidence, an… |
| `azure-storage` | available | 0 | 0 | 0 | — | — | Browse Azure Storage on a shared Copilot canvas: explore blobs, files, queues and tables, filter blob statistics, preview and download blobs, open read-only SA… |
| `backlog-swipe-triage` | available | 0 | 0 | 0 | — | — | Quickly swipe through backlog issues to triage decisions like assign, needs-info, defer, close, or ignore. |
| `backrooms-canvas` | available | 0 | 0 | 0 | — | — | Wander an endless first-person backrooms in a Copilot canvas while agents work; their status ghost-writes on the walls. |
| `bd-skills` | available | 0 | 0 | 0 | — | — | Helps GitHub Copilot investigate mobile app telemetry, diagnose crashes, manage [bitdrift](bitdrift.ai) workflows and dashboards, integrate the Capture SDK int… |
| `blea` | available | 0 | 0 | 0 | — | — | Safe, agent-first Bluetooth Low Energy diagnostics with portable evidence capture/diff/replay and guarded writes through a Skill, CLI, and local MCP server. |
| `bootui` | available | 0 | 0 | 0 | — | — | Diagnose running Spring Boot and Quarkus applications with BootUI. Includes a setup and troubleshooting skill plus a local MCP connection for runtime diagnosti… |
| `brainmaxxing` | available | 0 | 0 | 0 | — | — | Codebase-grounded concept-mastery quizzes with an interactive BrainMax Canvas dashboard. |
| `cache-stats` | available | 0 | 0 | 0 | — | — | Shows live prompt-cache reuse, expiry, token composition, and AI Credit cost for the current GitHub Copilot session without making model calls. |
| `canvas-authoring` | available | 0 | 0 | 0 | — | — | Toolkit setup and Azure or counter starters for the host’s native `create-canvas` skill; skill-only, not a canvas extension. Includes prebuilt packages and gui… |
| `cast-imaging` | available | 0 | 0 | 0 | — | — | A comprehensive collection of specialized agents for software analysis, impact assessment, structural quality advisories, and architectural review using CAST I… |
| `catalyst-by-zoho` | available | 0 | 0 | 0 | — | — | Official GitHub Copilot plugin for Catalyst by Zoho — a full-stack serverless cloud platform. Includes skills covering services, SDKs, CLI workflows, architect… |
| `chat-cards` | available | 0 | 0 | 0 | — | — | Interactive card deck in a GHCP canvas: tab cards, tables, SVG charts, show/hide sections, numbered outlines, rendered markdown documents, video clips, and for… |
| `chat-fork-map` | available | 0 | 0 | 0 | — | — | Maps branching Copilot conversations so parallel follow-up questions and exploration paths from complex tasks or learning can be navigated without losing conte… |
| `chrome-devtools-plugin` | available | 0 | 0 | 0 | — | — | Reliable automation, in-depth debugging, and performance analysis in Chrome using Chrome DevTools and Puppeteer. |
| `chromium-control-canvas` | available | 0 | 0 | 0 | — | — | Opens a real Chromium window you can navigate and interact with from a Copilot canvas control panel and agent actions. |
| `chronicle-stats` | available | 0 | 0 | 0 | — | — | See your local Copilot token usage by day, model, and session, and get tips to use it more efficiently. |
| `clojure-interactive-programming` | available | 0 | 0 | 0 | — | — | Tools for REPL-first Clojure workflows featuring Clojure instructions, the interactive programming chat mode and supporting guidance. |
| `cms-development` | available | 0 | 0 | 0 | — | — | Skills for CMS development across themes, plugins, admin tooling, media workflows, markdown rendering, and static export pipelines. |
| `cockroachdb` | available | 0 | 0 | 0 | — | — | Connect GitHub Copilot to your CockroachDB clusters: run and explore SQL through MCP, with DBA/Developer/Operator agents, CockroachDB best-practice skills, and… |
| `color-orb` | available | 0 | 0 | 0 | — | — | A visual orb that users can ask the agent to recolor while showing a live activity log in the canvas. |
| `connector-namespaces` | available | 0 | 0 | 0 | — | — | Interactive GitHub Copilot canvas for discovering, connecting, and managing hosted MCP servers from an Azure Connector Namespace. |
| `containers` | available | 0 | 0 | 0 | — | — | Browse and operate local Docker containers and images in a Copilot canvas. Follow logs, watch resource usage, browse files, inspect image layers, and recover D… |
| `context-engineering` | available | 0 | 0 | 0 | — | — | Tools and techniques for maximizing GitHub Copilot effectiveness through better context management. Includes guidelines for structuring code, an agent for plan… |
| `context-matic` | available | 0 | 0 | 0 | — | context-matic | Coding agents hallucinate APIs. ContextMatic gives them curated, versioned API and SDK docs. Ask your agent to "integrate the payments API" and it guesses — fa… |
| `convert-to-md` | available | 0 | 0 | 0 | — | — | A collection of Copilot skills that convert common document formats into Markdown so their contents can be accurately analyzed, summarized, searched, or extrac… |
| `copilot-goal-skill` | available | 0 | 0 | 0 | — | — | Goal-driven task orchestration with independent verification. Interviews the user to define a clear goal, then loops between a Builder subagent (does the work)… |
| `copilot-sdk` | available | 0 | 0 | 0 | — | — | Build applications with the Microsoft Copilot SDK, transitioning from GitHub Copilot SDK, across multiple programming languages. Includes instructions for C#,… |
| `copilot-session-dj` | available | 0 | 0 | 0 | — | — | A playful, local Strudel soundtrack for the current GitHub Copilot session and its subagents. Includes an English/Japanese DJ Canvas, three synth-only presets,… |
| `crowdstrike-charlotte-ai-agentworks` | available | 0 | 0 | 0 | — | — | CrowdStrike Charlotte AI AgentWorks skills for creating, managing, and invoking AI agents via external Falcon API Gateway endpoints. Includes agent lifecycle m… |
| `crowdstrike-falcon-foundry` | available | 0 | 0 | 0 | — | — | AI coding assistant skills for building CrowdStrike Falcon Foundry apps: scaffolding, deployment, and best practices for API integrations, collections, functio… |
| `crowdstrike-falcon-fusion` | available | 0 | 0 | 0 | — | — | AI coding assistant skills for building CrowdStrike Falcon Fusion workflows: action discovery, YAML authoring, deployment, execution monitoring, and best pract… |
| `csharp-dotnet-development` | available | 0 | 0 | 0 | — | — | Essential prompts, instructions, and chat modes for C# and .NET development including testing, documentation, and best practices. |
| `database-data-management` | available | 0 | 0 | 0 | — | — | Database administration, SQL optimization, and data management tools for PostgreSQL, SQL Server, and general database development best practices. |
| `datadog` | available | 0 | 0 | 0 | — | — | Use Datadog directly in Copilot / VS Code through a preconfigured Datadog MCP server. Query logs, metrics, traces, dashboards, and more through natural convers… |
| `dataverse` | available | 0 | 0 | 0 | — | — | Microsoft Dataverse plugin for coding agents, covering record CRUD, bulk data operations, advanced queries, schema and metadata, administration, security, envi… |
| `dataverse-sdk-for-python` | available | 0 | 0 | 0 | — | — | Comprehensive collection for building production-ready Python integrations with Microsoft Dataverse. Includes official documentation, best practices, advanced… |
| `dependabot-triage` | available | 0 | 0 | 0 | — | — | Triage Dependabot alerts and recommend safe, evidence-based dependency updates. |
| `devops-oncall` | available | 0 | 0 | 0 | — | — | A focused set of prompts, instructions, and a chat mode to help triage incidents and respond quickly with DevOps tools and Azure resources. |
| `diagram-viewer` | available | 0 | 0 | 0 | — | — | Render diagrams, click nodes to drill down, and view agent-generated explanations directly in the canvas. |
| `dotnet` | available | 0 | 0 | 0 | — | — | C# language server (LSP) integration for coding agents and high-level .NET development skills. |
| `dotnet-diag` | available | 0 | 0 | 0 | — | — | Skills for .NET performance investigations, debugging, and incident analysis. |
| `dotnet-test` | available | 0 | 0 | 0 | — | — | Skills for running, generating, analyzing, and improving .NET tests: test execution, filtering, platform detection, coverage, testability, and MSTest workflows. |
| `doublecheck` | available | 0 | 0 | 0 | — | — | Three-layer verification pipeline for AI output. Extracts claims, finds sources, and flags hallucination risks so humans can verify before acting. |
| `draw` | available | 0 | 0 | 0 | — | — | Draw simple diagrams in a Copilot canvas: shapes, arrows that stay attached, text and a freehand pen. Copilot can read, create and edit the same drawing, tidy… |
| `edge-ai-tasks` | available | 0 | 0 | 0 | — | — | Task Researcher and Task Planner for intermediate to expert users and large codebases - Brought to you by microsoft/edge-ai |
| `edit-tutorial` | available | 0 | 0 | 0 | — | — | Turn the code edits Copilot made in your session into an interactive lesson: a step-by-step walkthrough of each change with before/after views and quizzes, the… |
| `elasticsearch` | available | 0 | 0 | 0 | — | — | Official Elastic plugin for GitHub Copilot — translate natural language to ES/QL queries, ingest data, manage Elasticsearch security (authn, authz, audit), and… |
| `ember` | available | 0 | 0 | 0 | — | — | An AI partner, not a tool. Ember carries fire from person to person — helping humans discover that AI partnership isn't something you learn, it's something you… |
| `excel-cli` | available | 0 | 0 | 0 | — | — | Let your coding agent work with real Microsoft Excel workbooks from the terminal: formulas, Power Query, PivotTables, charts, and VBA. Same features as Excel M… |
| `excel-mcp` | available | 0 | 0 | 0 | — | — | Let an AI assistant create and update Microsoft Excel workbooks: work with cells, formulas, Power Query, PivotTables, charts, and VBA in the desktop app. Requi… |
| `eyeball` | available | 0 | 0 | 0 | — | — | Document analysis with inline source screenshots. When you ask Copilot to analyze a document, Eyeball generates a Word doc where every factual claim includes a… |
| `fastah-ip-geo-tools` | available | 0 | 0 | 0 | — | — | This plugin is for network operations engineers who wish to tune and publish IP geolocation feeds in RFC 8805 format. It consists of an AI Skill and an associa… |
| `feedback-themes` | available | 0 | 0 | 0 | — | — | Explore grouped customer feedback signals by impact and drill into a theme to guide product next steps. |
| `figma` | available | 0 | 0 | 0 | — | — | Plugin that includes the Figma MCP server and Skills for common workflows. |
| `flight-map-canvas` | available | 0 | 0 | 0 | — | — | A GitHub Copilot canvas that generates a view where Google Maps can be explored using 3D controls, as if a flight simulator. Agents can send the flight anywher… |
| `flowstudio-power-automate` | available | 0 | 0 | 0 | — | — | Give your AI agent full visibility into Power Automate cloud flows via the FlowStudio MCP server. Connect, debug, build, monitor health, and govern flows at sc… |
| `fluentui-blazor` | available | 0 | 0 | 0 | — | fluent-ui-blazor | Build Blazor apps with the Microsoft Fluent UI Blazor library. Bundles the fluentui-blazor skill for correct usage patterns (providers, service registration, i… |
| `foundation-models` | available | 0 | 0 | 0 | — | — | Helps coding agents write and review Apple Foundation Models code for iOS, macOS, visionOS, and watchOS using the SDK installed on the developer's Mac. It veri… |
| `foundry-agentic-loop` | available | 0 | 0 | 0 | — | — | Build agentic solutions on Microsoft Foundry, GitHub and Azure. Prototype in an existing Foundry project, or run spec-driven development (SDD): a dynamic workf… |
| `foundry-hosted-agent-copilotkit` | available | 0 | 0 | 0 | — | foundry, microsoft-learn | Build CopilotKit + AG-UI web apps on Microsoft Foundry hosted agents (Microsoft Agent Framework): wiring, native Foundry primitives, human-in-the-loop approval… |
| `frontend-web-dev` | available | 0 | 0 | 0 | — | — | Essential prompts, instructions, and chat modes for modern frontend web development including React, Angular, Vue, TypeScript, and CSS frameworks. |
| `gem-team` | available | 0 | 0 | 0 | — | — | Self-Learning Multi-agent orchestration framework for spec-driven development and automated verification. With smarter tool calling and leaner context. |
| `gesture-review` | available | 0 | 0 | 0 | — | — | Review pull requests with a live camera feed and approve or reject using thumbs-up/thumbs-down gestures. |
| `gh-skills-builder` | available | 0 | 0 | 0 | — | — | Design, build, review, and publish GitHub Skills-style exercises with one coordinating agent and five Agent Skills for learner journeys, workflow-backed valida… |
| `git-ape` | available | 0 | 0 | 0 | — | — | Intelligent agent system for deploying any Azure workload through GitHub Copilot. Provides guided, safe, and validated deployments using ARM templates, with bu… |
| `git-worktree-explorer` | available | 0 | 0 | 0 | — | — | Visualize the active Git repository through worktrees, branches, commits, and optional GitHub pull request context. |
| `github-copilot-modernization` | available | 0 | 0 | 0 | — | — | Autonomous application modernization using multi-agent orchestration for GitHub Copilot CLI. Supports Java upgrades (8→21, Spring Boot 2.x→3.x), .NET moderniza… |
| `github-security` | available | 0 | 0 | 0 | — | — | Review your session's changes for vulnerabilities and fix code scanning alerts |
| `globestudio` | available | 0 | 0 | 0 | — | globestudio | Make dotted world maps and animated 3D globes and put them on a website. Bundles the globestudio skill, which writes the design as one config and embeds it as… |
| `go-mcp-development` | available | 0 | 0 | 0 | — | — | Complete toolkit for building Model Context Protocol (MCP) servers in Go using the official github.com/modelcontextprotocol/go-sdk. Includes instructions for b… |
| `incident-io` | available | 0 | 0 | 0 | — | — | Official incident.io plugins for AI agents: skills for working with [incident.io](https://incident.io/) — incidents, on-call, and investigations — and for auth… |
| `java-development` | available | 0 | 0 | 0 | — | — | Comprehensive collection of prompts and instructions for Java development including Spring Boot, Quarkus, testing, documentation, and best practices. |
| `java-mcp-development` | available | 0 | 0 | 0 | — | — | Build Model Context Protocol (MCP) servers in Java with the official MCP Java SDK 2.x. Includes a skill that generates a server project and an expert agent for… |
| `java-modernization-studio` | available | 0 | 0 | 0 | — | — | Drive the GitHub Copilot App Modernization for Java workflow from an interactive canvas: environment readiness, repo assessment, prioritized plan and progress,… |
| `jira-workbench` | available | 0 | 0 | 0 | — | — | A Copilot app canvas that shows any Jira project's full hierarchy (epics, issues and subtasks) and traces each item to its Copilot sessions and GitHub pull req… |
| `jupyter-notebooks` | available | 0 | 0 | 0 | — | — | Create, edit, run, save, and checkpoint Jupyter notebooks in an interactive Copilot canvas. |
| `keep-the-why` | available | 0 | 0 | 0 | — | — | Preserves or recovers the reasoning behind a codebase — architectural decisions, rejected alternatives, workarounds, incident learnings, operational constraint… |
| `kotlin-mcp-development` | available | 0 | 0 | 0 | — | — | Complete toolkit for building Model Context Protocol (MCP) servers in Kotlin using the official io.modelcontextprotocol:kotlin-sdk library. Includes instructio… |
| `markdstage` | available | 0 | 0 | 0 | — | — | Create, edit, present, and export Markdown slides in a GitHub Copilot Canvas. |
| `mcp-m365-copilot` | available | 0 | 0 | 0 | — | — | Comprehensive collection for building declarative agents with Model Context Protocol integration for Microsoft 365 Copilot |
| `megalinter` | available | 0 | 0 | 0 | — | — | Set up, run and fix MegaLinter on any repository: 100+ linters for 69+ languages, 23+ formats and 21+ tooling formats, from CI or locally. |
| `microsoft-docs` | available | 0 | 0 | 0 | — | — | Access official Microsoft documentation, API references, and code samples for Azure, .NET, Windows, and more. |
| `microsoft-events` | available | 0 | 0 | 0 | — | — | Connect your project to Microsoft Build and Ignite sessions — discover relevant talks, explore what's new for your stack, and plan next steps from your develop… |
| `microsoft-foundry` | available | 0 | 0 | 0 | — | — | Skills and interactive Copilot canvas for designing, configuring, testing and deploying agents to Microsoft Foundry. |
| `mobile-canvas` | available | 0 | 0 | 0 | — | — | View, create, boot, and interact with local iOS simulators and Android emulators from a GitHub Copilot canvas. The plugin also exposes the same device controls… |
| `modern-web-guidance` | available | 0 | 0 | 0 | — | — | Modern Web Guidance is an agent skill and CLI tool designed to help AI coding agents build web applications using modern, secure, and high-performance APIs rat… |
| `modernization-workflow` | available | 0 | 0 | 0 | — | — | Visualize and guide the GitHub Copilot Modernize CLI Assess, Plan, and Execute workflow for .NET, Java, and C++ application repositories. |
| `modernize-dotnet` | available | 0 | 0 | 0 | — | — | AI-powered .NET modernization and upgrade assistant. Helps upgrade .NET Framework and .NET applications to the latest versions of .NET. |
| `modernize-java` | available | 0 | 0 | 0 | — | — | GitHub Copilot modernization – Java Upgrade CLI Plugin helps you upgrade Java applications from the command line. It brings intelligent modernization capabilit… |
| `msgraph-developer-skills` | available | 0 | 0 | 0 | — | — | Builds and modernizes Microsoft Graph applications with minimal, purpose-built API clients. The plugin identifies the required Microsoft Graph endpoints and th… |
| `napkin` | available | 0 | 0 | 0 | — | — | Visual whiteboard collaboration for Copilot CLI. Opens an interactive whiteboard in your browser where you can draw, sketch, and add sticky notes — then share… |
| `netlify` | available | 0 | 0 | 0 | — | — | Netlify platform skills covering functions, edge functions, blobs, database, identity, image CDN, forms, config, CLI, frameworks, caching, AI Gateway, and depl… |
| `nitrosend` | available | 0 | 0 | 0 | — | — | Prepare and review email campaigns, automation flows, contacts and transactional messages in Nitrosend through its hosted OAuth MCP server. Includes a scoped s… |
| `noob-mode` | available | 0 | 0 | 0 | — | — | Plain-English translation layer for non-technical Copilot CLI users. Translates every approval prompt, error message, and technical output into clear, jargon-f… |
| `openapi-to-application-csharp-dotnet` | available | 0 | 0 | 0 | — | — | Generate production-ready .NET applications from OpenAPI specifications. Includes ASP.NET Core project scaffolding, controller generation, entity framework int… |
| `openapi-to-application-go` | available | 0 | 0 | 0 | — | — | Generate production-ready Go applications from OpenAPI specifications. Includes project scaffolding, handler generation, middleware setup, and Go best practice… |
| `openapi-to-application-java-spring-boot` | available | 0 | 0 | 0 | — | — | Generate production-ready Spring Boot applications from OpenAPI specifications. Includes project scaffolding, REST controller generation, service layer organiz… |
| `openapi-to-application-nodejs-nestjs` | available | 0 | 0 | 0 | — | — | Generate production-ready NestJS applications from OpenAPI specifications. Includes project scaffolding, controller and service generation, TypeScript best pra… |
| `openapi-to-application-python-fastapi` | available | 0 | 0 | 0 | — | — | Generate production-ready FastAPI applications from OpenAPI specifications. Includes project scaffolding, route generation, dependency injection, and Python be… |
| `oracle-to-postgres-migration-expert` | available | 0 | 0 | 0 | — | — | Expert agent for Oracle-to-PostgreSQL application migrations in .NET solutions. Performs code edits, runs commands, and invokes extension tools to migrate .NET… |
| `orrery` | available | 0 | 0 | 0 | — | — | Architecture and system design diagrams with official AWS, Azure, Google Cloud, Kubernetes and GitHub icons, auto-laid out by ELK and rendered from a YAML spec… |
| `ospo-sponsorship` | available | 0 | 0 | 0 | — | — | Tools and resources for Open Source Program Offices (OSPOs) to identify, evaluate, and manage sponsorship of open source dependencies through GitHub Sponsors,… |
| `partners` | available | 0 | 0 | 0 | — | — | Custom agents that have been created by GitHub partners |
| `pcf-development` | available | 0 | 0 | 0 | — | — | Complete toolkit for developing custom code components using Power Apps Component Framework for model-driven and canvas apps |
| `phoenix` | available | 0 | 0 | 0 | — | — | Phoenix AI observability skills for LLM application debugging, evaluation, and tracing. Includes CLI debugging tools, LLM evaluation workflows, and OpenInferen… |
| `php-mcp-development` | available | 0 | 0 | 0 | — | — | Comprehensive resources for building Model Context Protocol servers using the official PHP SDK with attribute-based discovery, including best practices, projec… |
| `pm-skills` | available | 0 | 0 | 0 | — | — | MCP server and 12 skills for product analysis, specification writing, strategy, narrative, and stakeholder alignment. Run competitive analyses, write zero-ques… |
| `pmx-canvas` | available | 0 | 0 | 0 | — | — | PMX Canvas is a collaborative canvas where you and your AI agent collect evidence, analyze findings, and develop ideas together. Pin material as context for yo… |
| `postgres-skills` | available | 0 | 0 | 0 | — | — | Expert PostgreSQL guidance and live database tools for Postgres anywhere, including local, self-hosted, containers, on-premises, AWS, Google Cloud, Azure Datab… |
| `power-apps-code-apps` | available | 0 | 0 | 0 | — | — | Complete toolkit for Power Apps Code Apps development including project scaffolding, development standards, and expert guidance for building code-first applica… |
| `power-bi-development` | available | 0 | 0 | 0 | — | — | Comprehensive Power BI development resources including data modeling, DAX optimization, performance tuning, visualization design, security best practices, and… |
| `power-platform-architect` | available | 0 | 0 | 0 | — | — | Solution Architect for the Microsoft Power Platform, turning business requirements into functioning Power Platform solution architectures. |
| `power-platform-mcp-connector-development` | available | 0 | 0 | 0 | — | — | Complete toolkit for developing Power Platform custom connectors with Model Context Protocol integration for Microsoft Copilot Studio |
| `pr-artifact-explorer` | available | 0 | 0 | 0 | — | — | Navigate pull requests and workflow runs (including scheduled and manual runs without a PR) and securely explore GitHub Actions artifacts, including test resul… |
| `pr-review` | available | 0 | 0 | 0 | — | — | Review GitHub pull requests in a read-only canvas with AI-grouped changes, expandable diffs, and questions scoped to groups, files, or hunks. |
| `project-documenter` | available | 0 | 0 | 0 | — | — | Generate professional project documentation with draw.io architecture diagrams and Word (.docx) output with embedded images. Automatically discovers any projec… |
| `project-planning` | available | 0 | 0 | 0 | — | — | Tools and guidance for software project planning, feature breakdown, epic management, implementation planning, and task organization for development teams. |
| `python-mcp-development` | available | 0 | 0 | 0 | — | — | Build Model Context Protocol (MCP) servers in Python with the official MCP Python SDK v2 (MCPServer). Includes a skill that generates a server project and an e… |
| `radius` | available | 0 | 0 | 0 | — | — | Model, visualize, and deploy applications with Radius from the GitHub Copilot app and CLI. |
| `rayfin` | available | 0 | 0 | 0 | — | — | Getting-started router skill for Rayfin - scaffold a new app with the Rayfin CLI, then use the version-locked skill installed in the project. |
| `react18-upgrade` | available | 0 | 0 | 0 | — | — | Enterprise React 18 migration toolkit with specialized agents and skills for upgrading React 16/17 class-component codebases to React 18.3.1. Includes auditor,… |
| `react19-upgrade` | available | 0 | 0 | 0 | — | — | Enterprise React 19 migration toolkit with specialized agents and skills for upgrading React 18 codebases to React 19. Includes auditor, dependency surgeon, so… |
| `release-notes-showcase` | available | 0 | 0 | 0 | — | — | Compose and refine launch-ready release notes with contributor callouts and export-friendly output. |
| `remotion` | available | 0 | 0 | 0 | — | — | Make videos agentically. |
| `repo-actions-hub` | available | 0 | 0 | 0 | — | — | Browse repository GitHub Actions workflows, inspect recent runs, and trigger manual workflow_dispatch runs from a Copilot canvas. |
| `rhost` | available | 0 | 0 | 0 | — | — | Use an installed rhost CLI to run ordinary commands on SSH-reachable Linux hosts with local-like stdin, output, and exit behavior. |
| `roundup` | available | 0 | 0 | 0 | — | — | Self-configuring status briefing generator. Learns your communication style from examples, discovers your data sources, and produces draft updates for any audi… |
| `ruby-mcp-development` | available | 0 | 0 | 0 | — | — | Complete toolkit for building Model Context Protocol servers in Ruby using the official MCP Ruby SDK gem with Rails integration support. |
| `rug-agentic-workflow` | available | 0 | 0 | 0 | — | — | Three-agent workflow for orchestrated software delivery with an orchestrator plus implementation and QA subagents. |
| `rust-mcp-development` | available | 0 | 0 | 0 | — | — | Build high-performance Model Context Protocol servers in Rust using the official rmcp SDK with async/await, procedural macros, and type-safe implementations. |
| `salesforce-development` | available | 0 | 0 | 0 | — | — | Complete Salesforce agentic development environment covering Apex & Triggers, Flow automation, Lightning Web Components, Aura components, and Visualforce pages. |
| `sap-ux-fiori-tools` | available | 0 | 0 | 0 | — | — | MCP server and skills for SAP Fiori development. Helps AI coding assistants build, modify, and test SAP Fiori Elements applications connected to CAP or ABAP OD… |
| `security-best-practices` | available | 0 | 0 | 0 | — | — | Security frameworks, accessibility guidelines, performance optimization, and code quality best practices for building secure, maintainable, and high-performanc… |
| `sentry-triage` | available | 0 | 0 | 0 | — | — | Scan live Sentry issues in a Copilot canvas, group them by urgency, and hand issues off for tracking or a fix PR. |
| `signals-dashboard` | available | 0 | 0 | 0 | — | — | Real-time Workshop dashboard with agent signals, honesty calibration, cost-aware desk profiles, and fail-closed Local Delegation. |
| `site-studio` | available | 0 | 0 | 0 | — | — | Plan, draft, and track a personal website section by section — a shared canvas where you and your agent author content, watch progress, and review every change. |
| `skill-image-gen` | available | 0 | 0 | 0 | — | — | Generate images using AI directly from your coding workflow. Supports OpenAI (gpt-image-2) and Google Gemini. BYO API key — the skill guides you through setup… |
| `skills-for-copilot-studio` | available | 0 | 0 | 0 | — | — | Microsoft Copilot Studio YAML authoring toolkit. Create, edit, validate, and test Copilot Studio agents using YAML files. |
| `software-engineering-team` | available | 0 | 0 | 0 | — | — | 7 specialized agents covering the full software development lifecycle from UX design and architecture to security and DevOps. |
| `sonarqube` | available | 0 | 0 | 0 | — | — | SonarQube is the AI code quality and security verification platform used by millions of developers to catch bugs, vulnerabilities, and leaked secrets. This plu… |
| `spacefast` | available | 0 | 0 | 0 | — | — | Build and publish websites, dashboards, reports, and small web tools with Spacefast. Includes skills for editing Spaces, sharing previews, connecting domains,… |
| `stacked-prs` | available | 0 | 0 | 0 | — | — | Split an existing large branch into smaller stacked PRs on GitHub, Azure DevOps or GitLab, and manage the branches as PRs are merged. |
| `statuslines` | available | 0 | 0 | 0 | — | — | A checkout-aware session dashboard for Copilot CLI: group pull requests and linked issues by branch/worktree, show local changes and upstream/base divergence,… |
| `stripe` | available | 0 | 0 | 0 | — | — | Accept payments and grow your business. Stripe's agent plugin includes best practices, upgrade guidance, and our MCP server. |
| `structured-autonomy` | available | 0 | 0 | 0 | — | — | Premium planning, thrifty implementation |
| `sumo-logic` | available | 0 | 0 | 0 | — | — | Query Sumo Logic logs, alerts, dashboards, and SIEM insights directly from Copilot. |
| `swift-mcp-development` | available | 0 | 0 | 0 | — | — | Comprehensive collection for building Model Context Protocol servers in Swift using the official MCP Swift SDK with modern concurrency features. |
| `technical-spike` | available | 0 | 0 | 0 | — | — | Tools for creation, management and research of technical spikes to reduce unknowns and assumptions before proceeding to specification and implementation of sol… |
| `testing-automation` | available | 0 | 0 | 0 | — | — | Comprehensive collection for writing tests, test automation, and test-driven development including unit tests, integration tests, and end-to-end testing strate… |
| `the-workshop` | available | 0 | 0 | 0 | — | — | Stop being the switchboard between your AI agents — direct a team. The Workshop puts long-running AI agents (desks) in the same room, on the same work, each wi… |
| `timebase` | available | 0 | 0 | 0 | — | — | Connect your AI agent to TimeBase, a high-performance database for financial market and other time-series data, via MCP tools and skills for QQL query and Time… |
| `tiny-tool-town-submitter` | available | 0 | 0 | 0 | — | — | Inspect a repository, improve Tiny Tool Town readiness, submit its listing issue, and launch remediation work. |
| `tmforge` | available | 0 | 0 | 0 | — | — | The Strider agent that comes with the tmforge plugin adds evidence-backed STRIDE threat modeling to GitHub Copilot, with structured risk assessment, determinis… |
| `token-pacman` | available | 0 | 0 | 0 | — | — | Visualizes live session AI-credit usage as a Pac-Man board with pellets, ghosts, fruit milestones, and game-over limits. |
| `typescript` | available | 0 | 0 | 0 | — | — | Skills from the TypeScript team for coding agents working with TypeScript, JavaScript, and Node.js. Covers complex TypeScript tasks like upgrades, project setu… |
| `typescript-mcp-development` | available | 0 | 0 | 0 | — | — | Complete toolkit for building Model Context Protocol (MCP) servers in TypeScript/Node.js using the official SDK. Includes instructions for best practices, a pr… |
| `typespec-m365-copilot` | available | 0 | 0 | 0 | — | — | Comprehensive collection of prompts, instructions, and resources for building declarative agents and API plugins using TypeSpec for Microsoft 365 Copilot exten… |
| `ui-theme-designer` | available | 0 | 0 | 0 | — | — | Equips AI coding agents with knowledge and tooling for working with UI theme designer, the SAP Design System, and SAP Fiori design tokens. |
| `ui5` | available | 0 | 0 | 0 | — | — | SAPUI5 / OpenUI5 plugin for GitHub CoPilot. Create and validate UI5 projects, access API documentation, run UI5 linter, get development guidelines and best pra… |
| `ui5-modernization` | available | 0 | 0 | 0 | — | — | Complete UI5 modernization toolkit with workflow and specialized fix patterns for modernizing SAPUI5/OpenUI5 applications |
| `ui5-typescript-conversion` | available | 0 | 0 | 0 | — | — | SAPUI5 / OpenUI5 plugin for GitHub CoPilot. Convert JavaScript based UI5 projects to TypeScript. |
| `uizze` | available | 0 | 0 | 0 | — | — | Build product-specific interfaces with a focused UIZZE workflow, optional real-screen evidence, and a practical finish check. |
| `upgrade-agent` | available | 0 | 0 | 0 | — | — | AI-powered upgrade assistant for upgrading and migrating applications. Helps modernize legacy code and upgrade .NET applications to current frameworks. |
| `usage-insights` | available | 0 | 0 | 0 | — | — | Inspect current and historical GitHub Copilot token and AI-credit usage with per-agent rollups and in-canvas session drill-down. |
| `vercel-plugin` | available | 0 | 0 | 0 | — | — | Build and deploy web apps and agents. Comprehensive Vercel ecosystem plugin — relational knowledge graph, skills for every major product, specialized agents, a… |
| `visual-pr` | available | 0 | 0 | 0 | — | — | Capture, annotate, and embed screenshots and animated GIF demos in pull request descriptions. Includes Playwright-based UI capture, PIL image annotations, PR e… |
| `whatidid` | available | 0 | 0 | 0 | — | — | Turn your Copilot sessions into proof of impact — research-grounded HTML reports with effort estimation, skills analysis, and ROI metrics from local session lo… |
| `where-was-i` | available | 0 | 0 | 0 | — | — | Reconstruct your dev context (branch, commits, uncommitted work, PR clues) and trigger a resume prompt to continue quickly. |
| `winappcli` | available | 0 | 0 | 0 | — | — | Windows app development, packaging, and distribution. Helps with creating Windows installers (MSIX), code signing, certificates, Windows SDK and Windows App SD… |
| `windbg` | available | 0 | 0 | 0 | — | — | WinDbg diagnosis workflows for native Windows applications, services, UMDF/user-mode drivers, and kernel-mode drivers. Covers crashes, hangs, heap corruption,… |
| `windows-app-storage-inspector-cleanup` | available | 0 | 0 | 0 | — | — | Inspect Windows application storage, understand local disk usage, and safely move approved cleanup items to the Recycle Bin. |
| `winui` | available | 0 | 0 | 0 | — | — | Agents and skills for WinUI 3 app development. Create new WinUI 3 desktop apps, convert from other frameworks (WPF, WinForms, Electron, Tauri, Flutter) to WinU… |
| `wiqd` | available | 0 | 0 | 0 | — | — | Developer toolkit for building, validating, provisioning, and publishing Microsoft 365 Copilot plugins, including extensibility capabilities such as declarativ… |
| `work-hub` | available | 0 | 0 | 0 | — | — | Generic cross-repo command center canvas for GitHub Copilot with onboarding, focus planning, repo health, work signals, and session cleanup. |
