# Edge Platform & Automation Architecture

> Platform Solution Architecture Blueprint: Edge Computing, Distributed Event Mesh & Local AI Pipeline

This repository contains the architecture diagrams, automation state models, and design documentation for a distributed edge platform running across microcontrollers, single-board orchestrators (Raspberry Pi), and localized x86 compute.

---

## 1. Global Platform Architecture (C4 Container View)

```mermaid
flowchart TB
    subgraph WAN ["Cloud & Ingress Boundaries"]
        Cloudflare["Cloudflare Zero Trust / Tunnel"]
        AzureAI["Hybrid Fallback: Azure OpenAI"]
        NtfyPush["Ntfy Push Notification Broker"]
    end

    subgraph EdgeSensors ["Layer 1: Sensor & Voice Satellites (Edge)"]
        direction LR
        AtomEcho["M5Stack Atom Echo (ESPHome)"]
        ZigbeeNodes["Zigbee / Matter Sensor Mesh"]
        SmartAppliances["Smart Appliances (Dishwasher, AC Units)"]
        WLED["ESP8266 / WLED (Addressable LED Strips)"]
    end

    subgraph NodePi ["Layer 2: Event Mesh & Home Core (RPi Node)"]
        direction TB
        HA["Home Assistant Core (State Engine)"]
        MQTT["Mosquitto MQTT Broker (:1883)"]
        HyperHDR["HyperHDR Ambilight Daemon"]
        PiDiag["Pi SRE Telemetry & Diagnostics"]
    end

    subgraph Nodex86 ["Layer 3: Local Compute & Edge AI (x86 Node)"]
        direction TB
        MCPGate["MCP Voice AI Gateway (FastAPI :8030)"]
        OllamaLocal["Ollama: Qwen-2.5 1.5B (RAM-locked / AVX-512)"]
        TTSProxy["Kokoro / Piper TTS Streaming Proxy"]
        DockerApps["Docker Container Workloads (WebUI, Utilities)"]
    end

    subgraph StorageNet ["Layer 4: Ingress & Storage (Synology NAS)"]
        direction LR
        SynologyProxy["Synology DSM Reverse Proxy / ACL"]
        NASStorage["Shared NFS/SMB Storage & Backups"]
        AdGuard["AdGuard Home DNS"]
    end

    subgraph Actuators ["Actuator & Multimedia Endpoints"]
        GoogleNest["Google Nest Audio Cluster"]
        LGTV["Smart TV & LED Edge Matrix"]
        ClimateHVAC["Smart Thermostats & AC Units"]
    end

    %% Network & Ingress Flow
    Cloudflare --> SynologyProxy
    SynologyProxy --> HA
    SynologyProxy --> DockerApps
    AdGuard -. DNS Filtering .-> EdgeSensors & NodePi & Nodex86

    %% Edge to Controller
    AtomEcho -- "Microphone Stream (UDP/TCP)" --> MCPGate
    ZigbeeNodes -- "Zigbee/Matter" --> HA
    SmartAppliances -- "Status Telemetry" --> HA

    %% Core Event Mesh
    HA <--> MQTT
    MQTT --> HyperHDR
    HyperHDR --> WLED

    %% AI Pipeline
    MCPGate <--> OllamaLocal
    MCPGate -. Low-confidence query .-> AzureAI
    MCPGate --> TTSProxy
    TTSProxy -- "Chunked MP3 Stream (<1.2s TTFB)" --> GoogleNest

    %% Automations Output
    HA -- "TTS Broadcast" --> GoogleNest
    HA -- "Push Alert" --> NtfyPush
    HA -- "Relay Command" --> ClimateHVAC
    HA -- "State Trigger" --> HyperHDR
```

---

## 2. Automation Engine & Event Mesh

This diagram illustrates how physical, temporal, and user-initiated state changes are ingested, evaluated by policy constraints, and dispatched across actuation endpoints.

```mermaid
flowchart LR
    subgraph Ingestion ["1. Event Ingestion (Triggers)"]
        T1["Presence: Geo-fence / Network Probe"]
        T2["Environmental: Window Contact Open"]
        T3["Appliance: Power Draw (Dishwasher)"]
        T4["Temporal / Solar: Schedule Calculations"]
        T5["Voice Intent: ESP32 Wake-word Event"]
    end

    subgraph Engine ["2. State Machine & Policy Engine"]
        direction TB
        Bus["Event Bus (State Change Evaluator)"]
        Conditions{"Policy Engine (Thresholds & Mode Check)"}
        
        Bus --> Conditions
    end

    subgraph Dispatch ["3. Decision Matrix"]
        A_Presence["Welcome / Departure Orchestration"]
        A_HVAC["HVAC Energy Optimization Loop"]
        A_Reminder["Incomplete Household Task Alert"]
        A_Schedule["Calendar & Schedule Sync"]
        A_AI["Real-time Intent Parsing"]
    end

    subgraph Execution ["4. Execution & Actuators"]
        Act_TTS["Pipelined TTS to Multi-room Speakers"]
        Act_HVAC["Shut down AC compressor"]
        Act_Ntfy["Encrypted Ntfy Push Notification"]
        Act_Lights["Ambilight / Scene Adjustment"]
    end

    %% Connect Ingestion to Engine
    T1 & T2 & T3 & T4 & T5 --> Bus

    %% Connect Conditions to Dispatch
    Conditions -- "User enters zone" --> A_Presence
    Conditions -- "Window open > 3m" --> A_HVAC
    Conditions -- "Night & cycle not started" --> A_Reminder
    Conditions -- "Schedule match" --> A_Schedule
    Conditions -- "Audio payload received" --> A_AI

    %% Connect Dispatch to Execution
    A_Presence --> Act_TTS & Act_Lights
    A_HVAC --> Act_HVAC & Act_Ntfy
    A_Reminder --> Act_Ntfy
    A_Schedule --> Act_TTS
    A_AI --> Act_TTS
```

---

## 3. Sub-Second Streaming Voice AI Pipeline (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Mic as ESP32 (Atom Echo)
    participant Gateway as MCP Voice Gateway (:8030)
    participant LLM as Ollama Qwen-2.5 (RAM-locked)
    participant TTS as Kokoro TTS Streaming Proxy
    participant Speaker as Google Nest Audio

    User->>Mic: Speak query ("Hey Assistant, what's next on schedule?")
    Mic->>Gateway: Raw Audio Stream (UDP/TCP)
    Gateway->>LLM: Prompt Context + Token Generation Request
    LLM-->>Gateway: Streaming tokens (AVX-512 accelerated)
    Gateway->>TTS: Sentence 1 ("You have a meeting in 15 minutes...")
    Note over TTS: Synthesize chunk 1 in ~400ms
    TTS-->>Speaker: HTTP Chunked MP3 Stream (First chunk plays in ~1.2s)
    Gateway->>TTS: Sentence 2 ("...followed by the project review.")
    TTS-->>Speaker: Seamlessly append chunk 2 to stream buffer
    Speaker-->>User: Complete audible response with zero user-perceptible delay
```

---

## 4. Architectural Decision Records (ADRs)

| Architectural Decision | Chosen Strategy | Technical Rationale |
| :--- | :--- | :--- |
| **Workload Partitioning** | Tiered (Microcontrollers $\rightarrow$ SBC $\rightarrow$ x86) | Isolate low-jitter real-time I/O from heavy compute; prevents LLM inference workloads from locking Home Assistant core events. |
| **Local Model Serving** | In-Memory Locked Ollama (`qwen2.5:1.5b`) | Eliminates cold-start disk swapping latency; satisfies sub-1.5s voice turnaround budget. |
| **Audio Latency Budget** | Sentence-chunked MP3 HTTP streaming proxy | Eliminates the need to wait for complete paragraph synthesis before beginning audio playback on target endpoints. |
| **Zero-Trust Ingress** | Synology DSM Proxy + Cloudflare Access | Restricts internal management consoles and status metrics behind authenticated proxy layers with strict subnet ACLs. |
| **Event Messaging** | MQTT + Decoupled Ntfy | Asynchronous publish-subscribe model decouples producers from consumers, eliminating cascading network failures. |
