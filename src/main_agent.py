
import asyncio
from prompts import SYSTEM_PROMPT
from agent_tools import search_products
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.5,
    max_tokens=2048
).with_config(
    {"tags": ["nostream"]}
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
workflow.add_node("search_tool", ToolNode([search_products]))

workflow.add_edge(START, "agent")

workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "search_tool", END: END}
)

workflow.add_edge("search_tool", "agent")

checkpointer = InMemorySaver()

graph = workflow.compile(checkpointer)



# async def main():

#     while True:

#         print(f"{"=" * 34} User Message {"=" * 34}\n")
#         user_input = input().strip().lower()
#         print("\n")

#         if user_input == "stop":
#             print(f"{"=" * 34} System Message {"=" * 34}\n")
#             print("Terminando l'esecuzione...")
#             print("\n")
#             break

#         async for chunk in graph.astream(
#             {
#                 "messages": [
#                     {"role": "user", "content": user_input}
#                 ]
#             },
#             {
#                 "configurable": {"thread_id": 1}
#             }
#         ):
#             for _, update in chunk.items():

#                 response = update["messages"][-1].content

#                 if isinstance(response, list):
#                     print(f"{"=" * 34} Ai Message {"=" * 34}\n")
#                     print(response[0].get("text"))
#                     print("\n")
#                 else:
#                     update["messages"][-1].pretty_print()
#                     print("\n")

# asyncio.run(main())
