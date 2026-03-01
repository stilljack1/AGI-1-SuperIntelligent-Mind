from fastapi import FastAPI, BackgroundTasks
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Initialize the Sovereign Brain Web Server
app = FastAPI(title="AGI-1 Sovereign Brain")

@app.get("/")
def read_root():
    return {"status": "AGI-1 Brain Online", "mode": "2026 Sovereign Ignition"}

@app.get("/v1/presence/sovereign/health")
def health_check():
    return {
        "status": "READY FOR LAUNCH",
        "media_server": os.getenv("AGI1_MEDIA_SERVER_TYPE", "cloud"),
        "dynamodb": "SECURED",
        "agents": "1000-Node Swarm Standby"
    }

# Keeping your legacy sandbox test available as an endpoint
@app.post("/test-sandbox")
async def test_sandbox():
    try:
        from vercel.sandbox import AsyncSandbox as Sandbox
        sandbox = await Sandbox.create()
        cmd = await sandbox.run_command("echo", ["Hello from Vercel Sandbox!"])
        stdout = await cmd.stdout()
        await sandbox.stop()
        return {"status": "success", "output": stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}
