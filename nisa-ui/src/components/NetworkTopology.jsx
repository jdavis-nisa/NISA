import { pushContext } from "../SessionContext"
import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import * as d3 from "d3"
import api from "../api"

const SEC_API = "http://localhost:8082"

const SEVERITY_COLORS = {
  critical: "#ff2244",
  high: "#ff6600",
  medium: "#c9a84c",
  low: "#44aaff",
  info: "#44ffaa",
  unknown: "#666688"
}

function getNodeColor(node) {
  if (node.type === "attacker") return "#ff2244"
  if (node.type === "gateway") return "#c9a84c"
  if (node.vulnerabilities > 3) return "#ff2244"
  if (node.vulnerabilities > 1) return "#ff6600"
  if (node.vulnerabilities > 0) return "#c9a84c"
  if (node.openPorts > 5) return "#44aaff"
  return "#44ffaa"
}

function getRiskLevel(ports) {
  const dangerous = ["21", "22", "23", "25", "80", "443", "445", "1433", "3306", "3389", "5432", "6379", "8080", "8443", "27017"]
  const count = ports.filter(p => dangerous.some(d => p.port.startsWith(d))).length
  if (count > 3) return "critical"
  if (count > 1) return "high"
  if (count > 0) return "medium"
  return "low"
}

export default function NetworkTopology({ scanData, standalone = false }) {
  const svgRef = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [target, setTarget] = useState("192.168.1.0/24")
  const [scanType, setScanType] = useState("quick")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [graphData, setGraphData] = useState(null)
  const [stats, setStats] = useState(null)
  const navigate = useNavigate()

  const sendToRemediation = (node, port) => {
    const vuln = `Exposed ${port.service} service on port ${port.port} detected during Nmap scan of host ${node.ip}. Risk level: ${node.risk?.toUpperCase() || 'UNKNOWN'}. Assess for unauthorized access, default credentials, and known CVEs for ${port.service}${port.version ? ' version ' + port.version : ''}. Recommend service hardening, firewall rules, and access controls.`
    navigate('/remediation', { state: {
      prefill: {
        vulnerability: vuln,
        component: `${node.ip}:${port.port} (${port.service})`,
        language: 'bash'
      }
    }})
  }

  const buildGraph = (data) => {
    const nodes = []
    const links = []

    // Scanner node (NISA itself)
    nodes.push({
      id: "nisa",
      label: "NISA",
      type: "scanner",
      ip: "127.0.0.1",
      openPorts: 0,
      ports: [],
      vulnerabilities: 0,
      risk: "info",
      x: 0, y: 0
    })

    // Parse targets from scan
    const hosts = []
    const lines = data.results.split("\n")
    let currentHost = null

    for (const line of lines) {
      if (line.includes("Nmap scan report for")) {
        const match = line.match(/for (.+)/)
        if (match) {
          const raw = match[1].trim()
          // Handle both "hostname (ip)" and plain "ip" formats
          const ipMatch = raw.match(/\((\d+\.\d+\.\d+\.\d+)\)/)
          const ip = ipMatch ? ipMatch[1] : raw
          const label = raw.split(" ")[0]
          currentHost = {
            id: ip,
            label: label,
            type: "host",
            ip: ip,
            ports: [],
            openPorts: 0,
            vulnerabilities: 0,
            risk: "low"
          }
          hosts.push(currentHost)
        }
      } else if (currentHost && line.includes("/tcp") && line.includes("open")) {
        const parts = line.trim().split(/\s+/)
        if (parts.length >= 3) {
          currentHost.ports.push({
            port: parts[0],
            state: parts[1],
            service: parts[2] || "unknown",
            version: parts.slice(3).join(" ")
          })
          currentHost.openPorts++
        }
      }
    }

    // If no hosts parsed from raw output, use the ports data
    if (hosts.length === 0 && data.ports && data.ports.length > 0) {
      const host = {
        id: data.target,
        label: data.target,
        type: "host",
        ip: data.target,
        ports: data.ports,
        openPorts: data.ports.length,
        vulnerabilities: 0,
        risk: "low"
      }
      hosts.push(host)
    }

    // Calculate risk for each host
    for (const host of hosts) {
      host.risk = getRiskLevel(host.ports)
      host.vulnerabilities = host.ports.filter(p => {
        const dangerous = ["21", "23", "445", "1433", "3306", "3389", "5432", "6379", "27017"]
        return dangerous.some(d => p.port.startsWith(d))
      }).length
      nodes.push(host)
      links.push({ source: "nisa", target: host.id, type: "scan" })
    }

    // Stats
    const totalPorts = hosts.reduce((sum, h) => sum + h.openPorts, 0)
    const critical = hosts.filter(h => h.risk === "critical").length
    const high = hosts.filter(h => h.risk === "high").length

    setStats({
      hosts: hosts.length,
      totalPorts,
      critical,
      high,
      analysis: data.analysis
    })

    return { nodes, links }
  }

  const runScan = async () => {
    setLoading(true)
    setError("")
    setSelectedNode(null)
    try {
      const tokenRes = await api.post(`${SEC_API}/token`, { tool: "nmap" })
      const token = tokenRes.data.token
      const res = await api.post(
        `${SEC_API}/scan/nmap?token=${token}`,
        { target, scan_type: scanType }
      )
      const graph = buildGraph(res.data)
      setGraphData(graph)
      pushContext({
        tab: 'Topology',
        operation: `Nmap ${scanType.toUpperCase()} Topology Scan`,
        summary: `Topology scan of ${target} - ${graph.stats?.hosts ?? 0} hosts, ${graph.stats?.openPorts ?? 0} open ports, ${graph.stats?.critical ?? 0} critical`,
        detail: null
      })
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  useEffect(() => {
    if (scanData) {
      const graph = buildGraph(scanData)
      setGraphData(graph)
    }
  }, [scanData])

  useEffect(() => {
    if (!graphData || !svgRef.current) return

    const container = svgRef.current.parentElement
    const width = container.clientWidth || 800
    const height = 500

    d3.select(svgRef.current).selectAll("*").remove()

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)

    // Dark background
    svg.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "#080c14")
      .attr("rx", 4)

    // Grid pattern
    const defs = svg.append("defs")
    const pattern = defs.append("pattern")
      .attr("id", "grid")
      .attr("width", 30)
      .attr("height", 30)
      .attr("patternUnits", "userSpaceOnUse")
    pattern.append("path")
      .attr("d", "M 30 0 L 0 0 0 30")
      .attr("fill", "none")
      .attr("stroke", "#1a2035")
      .attr("stroke-width", 0.5)
    svg.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "url(#grid)")

    // Arrow marker
    defs.append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 20)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#c9a84c44")

    const simulation = d3.forceSimulation(graphData.nodes)
      .force("link", d3.forceLink(graphData.links)
        .id(d => d.id)
        .distance(120))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40))

    // Links
    const link = svg.append("g")
      .selectAll("line")
      .data(graphData.links)
      .join("line")
      .attr("stroke", "#c9a84c33")
      .attr("stroke-width", 1.5)
      .attr("marker-end", "url(#arrow)")
      .attr("stroke-dasharray", d => d.type === "scan" ? "4,2" : "none")

    // Node groups
    const node = svg.append("g")
      .selectAll("g")
      .data(graphData.nodes)
      .join("g")
      .attr("cursor", "pointer")
      .on("click", (event, d) => {
        event.stopPropagation()
        setSelectedNode(d)
      })
      .call(d3.drag()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x; d.fy = d.y
        })
        .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null; d.fy = null
        })
      )

    // Node outer glow ring
    node.append("circle")
      .attr("r", d => d.type === "scanner" ? 28 : 22)
      .attr("fill", "none")
      .attr("stroke", d => getNodeColor(d))
      .attr("stroke-width", 1)
      .attr("opacity", 0.3)

    // Node circle
    node.append("circle")
      .attr("r", d => d.type === "scanner" ? 22 : 18)
      .attr("fill", d => getNodeColor(d) + "22")
      .attr("stroke", d => getNodeColor(d))
      .attr("stroke-width", 2)

    // Node icon text
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("font-size", d => d.type === "scanner" ? "14" : "11")
      .attr("fill", d => getNodeColor(d))
      .attr("font-family", "JetBrains Mono, monospace")
      .text(d => d.type === "scanner" ? "NISA" : d.openPorts.toString())

    // Node label
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("y", d => d.type === "scanner" ? 36 : 32)
      .attr("font-size", "9")
      .attr("fill", "#8899bb")
      .attr("font-family", "JetBrains Mono, monospace")
      .text(d => d.label.length > 16 ? d.label.slice(0, 14) + ".." : d.label)

    // Risk badge for hosts
    node.filter(d => d.type !== "scanner" && d.risk !== "low")
      .append("circle")
      .attr("cx", 14)
      .attr("cy", -14)
      .attr("r", 6)
      .attr("fill", d => SEVERITY_COLORS[d.risk])

    svg.on("click", () => setSelectedNode(null))

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)
      node.attr("transform", d => `translate(${d.x},${d.y})`)
    })

    return () => simulation.stop()
  }, [graphData])

  const GOLD = "var(--accent-gold, #c9a84c)"
  const BORDER = "var(--border, #1e2d4a)"
  const BG2 = "var(--bg-secondary, #0d1526)"
  const BG3 = "var(--bg-tertiary, #111827)"
  const DIM = "var(--text-dim, #4a5568)"

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {standalone && (
        <div>
          <h2 style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "20px",
            fontWeight: 700, letterSpacing: "0.15em", color: GOLD, margin: 0 }}>
            NETWORK TOPOLOGY
          </h2>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
            color: DIM, marginTop: "2px" }}>
            Interactive Network Graph — Nmap Scan Visualization
          </div>
        </div>
      )}

      {standalone && (
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          <input value={target} onChange={e => setTarget(e.target.value)}
            placeholder="Target (e.g. 192.168.1.0/24)"
            style={{ flex: 1, minWidth: "200px", background: BG3,
              border: `1px solid ${BORDER}`, borderRadius: "4px",
              padding: "8px 12px", color: "var(--text-primary, #e2e8f0)",
              fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none" }} />
          <select value={scanType} onChange={e => setScanType(e.target.value)}
            style={{ background: BG3, border: `1px solid ${BORDER}`,
              borderRadius: "4px", padding: "8px 12px",
              color: "var(--text-primary, #e2e8f0)",
              fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none" }}>
            <option value="quick">Quick</option>
            <option value="standard">Standard</option>
            <option value="deep">Deep</option>
          </select>
          <button onClick={runScan} disabled={loading} style={{
            padding: "8px 20px", background: "var(--accent-gold-glow, #c9a84c22)",
            border: `1px solid ${GOLD}`, borderRadius: "4px", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
            fontSize: "12px", letterSpacing: "0.15em", color: GOLD,
            opacity: loading ? 0.6 : 1 }}>
            {loading ? "SCANNING..." : "SCAN & MAP"}
          </button>
        </div>
      )}

      {error && (
        <div style={{ color: "var(--danger, #ff4444)",
          fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>
          {error}
        </div>
      )}

      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px" }}>
          {[
            { label: "HOSTS", value: stats.hosts, color: GOLD },
            { label: "OPEN PORTS", value: stats.totalPorts, color: "#44aaff" },
            { label: "CRITICAL", value: stats.critical, color: "#ff2244" },
            { label: "HIGH RISK", value: stats.high, color: "#ff6600" },
          ].map(s => (
            <div key={s.label} style={{ background: BG2, border: `1px solid ${BORDER}`,
              borderRadius: "4px", padding: "12px", textAlign: "center" }}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "24px",
                fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                color: DIM, letterSpacing: "0.1em" }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ position: "relative", background: BG2,
        border: `1px solid ${BORDER}`, borderRadius: "4px", overflow: "hidden" }}>
        {!graphData && (
          <div style={{ padding: "60px", textAlign: "center",
            fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: DIM }}>
            {loading ? "Scanning network..." : "Run a scan to generate the network topology map"}
          </div>
        )}
        <svg ref={svgRef} style={{ width: "100%", display: graphData ? "block" : "none" }} />

        {selectedNode && (
          <div style={{
            position: "absolute", top: "12px", right: "12px",
            background: "#0a0e1a", border: `1px solid ${BORDER}`,
            borderRadius: "4px", padding: "16px", minWidth: "260px",
            maxWidth: "320px", zIndex: 10
          }}>
            <div style={{ display: "flex", justifyContent: "space-between",
              alignItems: "center", marginBottom: "12px" }}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
                fontSize: "13px", color: GOLD, letterSpacing: "0.1em" }}>
                {selectedNode.label}
              </div>
              <button onClick={() => setSelectedNode(null)}
                style={{ background: "none", border: "none", color: DIM,
                  cursor: "pointer", fontSize: "16px", padding: "0 4px" }}>x</button>
            </div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
              color: "var(--text-secondary, #8899bb)", lineHeight: 1.8 }}>
              <div>IP: <span style={{ color: "var(--text-primary, #e2e8f0)" }}>{selectedNode.ip}</span></div>
              <div>Type: <span style={{ color: "var(--text-primary, #e2e8f0)" }}>{selectedNode.type}</span></div>
              {selectedNode.risk && (
                <div>Risk: <span style={{ color: SEVERITY_COLORS[selectedNode.risk] || DIM,
                  fontWeight: 700, textTransform: "uppercase" }}>{selectedNode.risk}</span></div>
              )}
              {selectedNode.openPorts > 0 && (
                <div>Open Ports: <span style={{ color: "#44aaff" }}>{selectedNode.openPorts}</span></div>
              )}
            </div>
            {selectedNode.ports && selectedNode.ports.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                  color: DIM, letterSpacing: "0.1em", marginBottom: "6px" }}>
                  OPEN PORTS
                </div>
                <div style={{ maxHeight: "150px", overflowY: "auto" }}>
                  {selectedNode.ports.map((p, i) => (
                    <div key={i} style={{ padding: "4px 0",
                      borderBottom: `1px solid ${BORDER}` }}>
                      <div style={{ display: "flex", gap: "8px", alignItems: "center",
                        fontFamily: "JetBrains Mono, monospace", fontSize: "10px" }}>
                        <span style={{ color: GOLD, minWidth: "60px" }}>{p.port}</span>
                        <span style={{ color: "#44ffaa", flex: 1 }}>{p.service}</span>
                        <button
                          onClick={() => sendToRemediation(selectedNode, p)}
                          style={{ padding: "2px 6px", background: "transparent",
                            border: "1px solid #ff6600", borderRadius: "3px",
                            cursor: "pointer", fontFamily: "Rajdhani, sans-serif",
                            fontSize: "9px", fontWeight: 700, color: "#ff6600",
                            letterSpacing: "0.05em", whiteSpace: "nowrap" }}>
                          REMEDIATE
                        </button>
                      </div>
                      {p.version && (
                        <div style={{ color: DIM, fontSize: "9px",
                          fontFamily: "JetBrains Mono, monospace", marginTop: "2px" }}>
                          {p.version}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {stats?.analysis && (
        <div style={{ background: BG2, border: `1px solid ${BORDER}`,
          borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
            color: DIM, letterSpacing: "0.1em", marginBottom: "8px" }}>
            REDSAGE THREAT ANALYSIS
          </div>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px",
            color: "var(--text-secondary, #8899bb)", lineHeight: 1.6,
            whiteSpace: "pre-wrap" }}>
            {stats.analysis}
          </div>
        </div>
      )}
    </div>
  )
}
