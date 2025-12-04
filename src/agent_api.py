
import asyncio
import uvicorn
from fastapi import FastAPI
from utils import ChatCompletionRequest, ChatMessage
from main_agent import graph


app = FastAPI(title="OpenAI-compatible API")


@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [
            {
                "id": "mio-modello",
                "object": "model",
                "owned_by": "local"
            }
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    
    user_message = request.messages[-1].content

    result = await graph.ainvoke(
        {
            "messages": [
                {"role": "user", "content": user_message}
            ]
        },
        {
            "configurable": {"thread_id": 1}
        }
    )

    result = result["messages"][-1].content

    if isinstance(result, list):
        result = result[0].get("text")


    return {
        "id": "1",
        "object": "chat.completion",
        "model": "mio-modello",
        "choices": [
            {
            "index": 0,
            "message": ChatMessage(role="assistant", content=result),
            "finish_reason": "stop"
            }
  ]
}


async def main():
    config = uvicorn.Config("agent_api:app", host="0.0.0.0", port=8080)
    server = uvicorn.Server(config)

    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())