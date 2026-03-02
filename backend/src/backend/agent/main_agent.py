
import asyncio

from langchain_core.messages import (
    AnyMessage,
    HumanMessage, 
    SystemMessage
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import (
    END, 
    START, 
    MessagesState, 
    StateGraph
)
from langgraph.prebuilt import ToolNode, tools_condition

from backend.agent.agent_tools import search_products
from backend.agent.prompts import SYSTEM_PROMPT
from backend.config import settings


llm: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    temperature = 0.3
)


async def agent_node(
        state: MessagesState
    ) -> dict:
    """
    Execute the agent node responsible for model invocation 
    and tool selection.

    The function prepends a system-level instruction to the 
    current conversation state and invokes the language model 
    with the `search_products` tool bound. The model may decide to:

    - Produce a direct response to the user.
    - Call the scraping tool.
    - Call the tool and then synthesize a response using its output.

    The returned value is structured to be compatible with the
    LangGraph state format.

    Parameters
    ----------
    state : MessagesState
        The current graph state containing a `"messages"` key
        with the ongoing conversation history.

    Returns
    -------
    dict
        A dictionary with a single `"messages"` key containing
        the model's response message.

    Raises
    ------
    None
        Exceptions are propagated to the caller unless handled
        externally by the graph runtime.

    Notes
    -----
    The language model instance must already be configured
    with the appropriate provider, temperature, and credentials.
    Tool binding occurs dynamically at invocation time.
    """

    system_message: SystemMessage = SystemMessage(
        content = SYSTEM_PROMPT
    )

    messages: list[AnyMessage] = [system_message] + state["messages"]

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
    "website_search",
    ToolNode([search_products])
)

workflow.add_edge(START, "agent")

workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "website_search", 
        END: END
    }
)

workflow.add_edge("website_search", "agent")

graph = workflow.compile(
    checkpointer = InMemorySaver() if settings.CLI_MODE else None
)



async def main():
    """
    Entry point used only for local testing and debugging.

    This function allows running the agent interactively 
    from the terminal, without starting the full backend 
    or frontend services. It is intended to quickly test 
    the agent's behavior, prompts, and tool execution in 
    an isolated environment.

    The function is meant to be executed as a module, for 
    example:

        python3 -m src.main_agent

    and should not be used in production or as part of 
    the deployed system.
    """

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
                "messages": [HumanMessage(content = user_input)]
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