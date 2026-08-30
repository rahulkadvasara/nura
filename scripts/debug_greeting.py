import sys
import os
import asyncio
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

async def main():
    try:
        from app.core.dependencies import get_greeting_agent
        from app.agents.base.context import AgentContext
        agent = get_greeting_agent()
        ctx = AgentContext(patient_id="test-123")
        res = await agent.run("Hello", ctx)
        print("RES:", res)
    except Exception as e:
        print("EXC:", e)
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
