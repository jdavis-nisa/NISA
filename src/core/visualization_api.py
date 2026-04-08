from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import json
import os
from datetime import datetime
from openai import OpenAI

app = FastAPI(title="NISA Visualization API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

class ChartRequest(BaseModel):
    chart_type: str
    title: str
    data: dict
    options: Optional[dict] = {}

class NaturalChartRequest(BaseModel):
    prompt: str
    context: Optional[str] = ""

@app.get("/health")
def health():
    return {"status": "online", "system": "NISA Visualization API v0.1.0"}

@app.post("/chart")
def generate_chart(req: ChartRequest):
    """Generate a Plotly chart from structured data"""
    import plotly.graph_objects as go
    import plotly.express as px

    try:
        chart_type = req.chart_type.lower()
        data = req.data

        if chart_type == "bar":
            fig = go.Figure(data=[
                go.Bar(x=data.get("x", []), y=data.get("y", []),
                       marker_color="#C9A84C")
            ])
        elif chart_type == "line":
            fig = go.Figure(data=[
                go.Scatter(x=data.get("x", []), y=data.get("y", []),
                          mode="lines+markers", line=dict(color="#C9A84C", width=2))
            ])
        elif chart_type == "pie":
            fig = go.Figure(data=[
                go.Pie(labels=data.get("labels", []), values=data.get("values", []),
                      marker=dict(colors=["#C9A84C", "#00FF88", "#00AAFF", "#FF4444", "#FF6B35"]))
            ])
        elif chart_type == "scatter":
            fig = go.Figure(data=[
                go.Scatter(x=data.get("x", []), y=data.get("y", []),
                          mode="markers", marker=dict(color="#C9A84C", size=8))
            ])
        elif chart_type == "heatmap":
            fig = go.Figure(data=[
                go.Heatmap(z=data.get("z", []), x=data.get("x", []), y=data.get("y", []),
                          colorscale="Viridis")
            ])
        elif chart_type == "radar":
            fig = go.Figure(data=[
                go.Scatterpolar(r=data.get("r", []), theta=data.get("theta", []),
                               fill="toself", line=dict(color="#C9A84C"))
            ])
        elif chart_type == "histogram":
            fig = go.Figure(data=[
                go.Histogram(x=data.get("x", []), marker_color="#C9A84C")
            ])
        elif chart_type == "waveform":
            import numpy as np
            t = data.get("t", list(range(100)))
            y = data.get("y", [0]*100)
            fig = go.Figure(data=[
                go.Scatter(x=t, y=y, mode="lines",
                          line=dict(color="#00FF88", width=1.5))
            ])
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type: {chart_type}")

        fig.update_layout(
            title=dict(text=req.title, font=dict(color="#C9A84C", size=16)),
            paper_bgcolor="#0D1117",
            plot_bgcolor="#0D1117",
            font=dict(color="#8B9BAA"),
            xaxis=dict(gridcolor="#1E2D3D", color="#8B9BAA"),
            yaxis=dict(gridcolor="#1E2D3D", color="#8B9BAA"),
            margin=dict(t=50, l=50, r=30, b=50),
        )

        chart_json = fig.to_json()
        return {"status": "ok", "chart": json.loads(chart_json), "title": req.title}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/natural")
def natural_language_chart(req: NaturalChartRequest):
    """Generate chart from natural language description using Nisaba"""
    try:
        completion = llm.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": """You are a data visualization expert.
When given a description, respond ONLY with a JSON object:
{
  "chart_type": "bar|line|pie|scatter|heatmap|radar|histogram|waveform",
  "title": "chart title",
  "data": {appropriate data structure for chart type},
  "explanation": "brief explanation of what this shows"
}
For bar/line/scatter/histogram: data has "x" and "y" arrays
For pie: data has "labels" and "values" arrays  
For heatmap: data has "x", "y", "z" arrays
For radar: data has "r" and "theta" arrays
For waveform: data has "t" and "y" arrays
Use realistic sample data if no specific data provided.
Return ONLY valid JSON."""},
                {"role": "user", "content": f"Create a visualization for: {req.prompt}\nContext: {req.context}"}
            ],
            max_tokens=1000,
            temperature=0.1
        )

        response = completion.choices[0].message.content.strip()
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]

        chart_spec = json.loads(response)
        chart_req = ChartRequest(
            chart_type=chart_spec["chart_type"],
            title=chart_spec["title"],
            data=chart_spec["data"]
        )
        result = generate_chart(chart_req)
        result["explanation"] = chart_spec.get("explanation", "")
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prebuilt/{chart_name}")
def get_prebuilt_chart(chart_name: str):
    """Get pre-built NISA-specific charts"""
    import psycopg2
    import chromadb

    try:
        if chart_name == "audit_events":
            conn = psycopg2.connect(host="localhost", port=5432, dbname="nisa",
                                    user="nisa_user", password="nisa_secure_2026")
            cur = conn.cursor()
            cur.execute("""
                SELECT event_type, COUNT(*) as count
                FROM audit_log2
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            labels = [r[0] for r in rows]
            values = [r[1] for r in rows]
            return generate_chart(ChartRequest(
                chart_type="bar",
                title="NISA Audit Events by Type",
                data={"x": labels, "y": values}
            ))

        elif chart_name == "model_routing":
            conn = psycopg2.connect(host="localhost", port=5432, dbname="nisa",
                                    user="nisa_user", password="nisa_secure_2026")
            cur = conn.cursor()
            cur.execute("""
                SELECT model_used, COUNT(*) as count
                FROM audit_log2
                WHERE model_used IS NOT NULL AND model_used != ''
                GROUP BY model_used
                ORDER BY count DESC
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            labels = [r[0].split("/")[-1] for r in rows]
            values = [r[1] for r in rows]
            return generate_chart(ChartRequest(
                chart_type="pie",
                title="Model Routing Distribution",
                data={"labels": labels, "values": values}
            ))

        elif chart_name == "memory_growth":
            client = chromadb.HttpClient(host="localhost", port=8000)
            col = client.get_collection("nisa_memory")
            results = col.get(limit=1000, include=["metadatas"])
            dates = {}
            for meta in results["metadatas"]:
                ts = meta.get("timestamp", "")[:10]
                if ts:
                    dates[ts] = dates.get(ts, 0) + 1
            sorted_dates = sorted(dates.items())
            x = [d[0] for d in sorted_dates]
            y = [d[1] for d in sorted_dates]
            return generate_chart(ChartRequest(
                chart_type="line",
                title="Nisaba Memory Growth Over Time",
                data={"x": x, "y": y}
            ))

        elif chart_name == "security_scores":
            return generate_chart(ChartRequest(
                chart_type="radar",
                title="NISA Security Assessment Scores",
                data={
                    "r": [100, 88, 9, 95, 90, 85],
                    "theta": ["PyRIT", "OWASP", "Garak", "Auth", "Encryption", "Monitoring"]
                }
            ))

        else:
            raise HTTPException(status_code=404, detail=f"Unknown chart: {chart_name}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)
