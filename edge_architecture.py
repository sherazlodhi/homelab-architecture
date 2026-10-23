"""
Distributed Edge & Local AI Homelab Platform Architecture as Code
Generates high-resolution topology diagram using mingrammer/diagrams.
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.network import Nginx, Internet
from diagrams.onprem.iot import Mqtt
from diagrams.generic.device import Mobile

graph_attr = {
    "fontsize": "20",
    "bgcolor": "#FAFAFA",
    "pad": "0.5",
    "splines": "spline",
}

with Diagram(
    "Distributed Edge & Local AI Homelab Platform",
    show=False,
    graph_attr=graph_attr,
    filename="platform_architecture",
):
    user_mobile = Mobile("Mobile Client / Ntfy")

    with Cluster("Edge Ingress & DMZ (Synology Node)"):
        ingress = Nginx("Reverse Proxy & ACL")
        dns_guard = Server("AdGuard Home DNS")

    with Cluster("Edge Core & Message Broker (Raspberry Pi Node)"):
        ha_core = Server("Home Assistant Core\n(Event State Machine)")
        mqtt_bus = Mqtt("Mosquitto MQTT Broker")
        hyper_hdr = Server("HyperHDR Service")

        ha_core - Edge(color="orange", style="bold") - mqtt_bus
        ha_core >> Edge(label="Sync") >> hyper_hdr

    with Cluster("Layer 1: Sensor & Voice Satellites (Microcontrollers)"):
        m5_voice = Server("ESP32 Voice Satellite\n(Atom Echo / ESPHome)")
        wled_controller = Server("WLED Addressable Controller")
        sensors = Server("Zigbee / Matter Sensor Mesh")

    with Cluster("Layer 3: Local Compute & Edge AI (x86 Mini PC)"):
        mcp_gateway = Server("FastAPI MCP Voice Gateway\n(:8030)")
        local_llm = Server("Ollama: Qwen-2.5 (1.5B)\n(AVX-512 / RAM Locked)")
        tts_engine = Server("Kokoro / Piper TTS Proxy\n(Streaming MP3)")

        mcp_gateway - Edge(color="blue") - local_llm
        mcp_gateway >> Edge(label="Generate Audio") >> tts_engine

    with Cluster("Hybrid Cloud Failover"):
        azure_ai = Internet("Azure OpenAI Fallback")

    with Cluster("Audio / Output Endpoints"):
        smart_speakers = Server("Google Nest Multi-room")

    # Ingress & Network Flows
    user_mobile >> Edge(label="Zero-Trust Access") >> ingress
    ingress >> ha_core

    # Sensors to Core
    sensors >> Edge(label="Events") >> ha_core
    hyper_hdr >> Edge(label="LED Palette") >> wled_controller

    # Voice AI Pipeline
    m5_voice >> Edge(color="red", label="Audio Stream") >> mcp_gateway
    mcp_gateway -. Edge(style="dashed", label="Fallback") .-> azure_ai
    tts_engine >> Edge(color="green", label="<1.2s TTFB Stream") >> smart_speakers

    # HA Automations Output
    ha_core >> Edge(label="Broadcast / Alert") >> smart_speakers
    ha_core >> Edge(label="Push Notification") >> user_mobile

if __name__ == "__main__":
    print("Architecture diagram generated as platform_architecture.png")
