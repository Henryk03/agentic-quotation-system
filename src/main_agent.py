
import asyncio
from prompts import SYSTEM_PROMPT
from agent_tools import search_products, search_products_with_computer_use
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver       # mettere uno persistente


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3
)


async def agent_node(state: MessagesState):
    """
    Call the model to generate a response based on the current state.
    Given the request, it will decide to scrape the asked products
    using the scraping tool, or simply respond to the user. If the
    tool is used, then the agent could:

    * Answer the user's question using the tool's returned informations.
    * Simply return the results from the tool as they are.
    """

    system_message = SystemMessage(content=SYSTEM_PROMPT)

    messages = [system_message] + state["messages"]

    response = await llm.bind_tools(
        [search_products]
    ).ainvoke(
        messages
    )

    return {"messages": [response]}


# graph assembly
workflow = StateGraph(MessagesState)

workflow.add_node("agent", agent_node)

workflow.add_node(
    "supported_website_search",
    ToolNode([search_products])
)

# workflow.add_node(
#     "user_specified_website_seach",
#     ToolNode([search_products_with_computer_use])
# )

workflow.add_edge(START, "agent")

workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "supported_website_search", 
        # "tools": "user_specified_website_seach",
        END: END
    }
)

workflow.add_edge("supported_website_search", "agent")
# workflow.add_edge("user_specified_website_seach", "agent")

graph = workflow.compile(checkpointer=InMemorySaver())


async def run_agent(
        message: str,
        session_id: str,
        on_login_required: callable | None = None
    ):
    """"""

    response = await graph.ainvoke(
        input={
            "messages": [
                {"role": "user", "content": message}
            ]
        },
        config={
            "configurable": {
                "thread_id": session_id,
                "on_login_required": on_login_required
            }
        }
    )

    response_content = response["messages"][-1].content

    if isinstance(response_content, list):
        return response_content[0]["text"]
    
    return response_content



async def main():

    while True:

        print(f"{"=" * 34} User Message {"=" * 34}\n")
        user_input = input().strip().lower()
        print("\n")

        if user_input == "stop":
            print(f"{"=" * 34} System Message {"=" * 34}\n")
            print("Terminando l'esecuzione...")
            print("\n")
            break

        async for chunk in graph.astream(
            {
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            },
            {
                "configurable": {"thread_id": 1}
            }
        ):
            for _, update in chunk.items():

                response = update["messages"][-1].content

                if isinstance(response, list):
                    print(f"{"=" * 34} Ai Message {"=" * 34}\n")
                    print(response[0].get("text"))
                    print("\n")
                else:
                    update["messages"][-1].pretty_print()
                    print("\n")


if __name__ == "__main__":
    asyncio.run(main())