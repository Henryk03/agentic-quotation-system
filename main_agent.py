
import asyncio
from utils import ClassifyRequest
from agent_tools import search_products
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.5
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

    system_message = SystemMessage(
        content=(
            "You are an assistant that helps the user prepare quotations "
            "by searching for and collecting the requested items from the "
            "web.\nWhen you identify a product code - that can appear in "
            "various formats, sometimes made only of numbers (e.g. '14000'), "
            "or a mix of letters, numbers and symbols (e.g. 'A.B1 23', 'XW-200') "
            "- handle it exactly as written — do not modify, translate, "
            "or add words to it. If the user mentions both a product name and "
            "a product code in the same request (e.g., 'switch 14000' or 'switch "
            "with code 14000'), prioritize the code over the name. In such cases, "
            "use only the product code (e.g., 14000) to identify or search the item, "
            "and ignore the descriptive word (e.g., 'switch'). Furthermore, ignore "
            "filler words like 'with' and 'and' in product descriptions. Focus only "
            "on meaningful identifiers, codes, or specifications. For example, in "
            "'Mac Mini with M4 and 512GB of storage', extract only 'M4' and '512GB', "
            "or in 'Mac Mini with M4 Pro and 24GB of RAM', extract 'M4 Pro' and '24GB' "
            "only (do NOT include words like 'storage' or 'ram')."
            "\n\n"
            "If the user writes item names in the plural form, convert them to singular "
            "form before processing or searching for them (do NOT mention this skill of "
            "yours to the user, it is only to be able to use the scraping tool correctly)."
            "\nIf the tool raises an exception, explain clearly what happened to the user "
            "and how to solve the problem."
            "\n\n"
            "All responses MUST be written in Italian."
            "\n\n"
            "Before answering the user's request, analyze it to determine whether "
            "the user message is a question or a command about one or more products."
            "\n\n"
            "A **question** typically:\n"
            "- Contains a question mark (?).\n"
            "- Starts with interrogative words (who, what, when, where, why, how).\n"
            "- Asks for information, comparison, clarification or availability.\n"
            "- Could also contain BOTH an action request AND a question about the "
            "result(s) of that action (e.g. the scraped product availability, price, "
            "etc.)."
            "\n\n"
            "A **command** typically:\n"
            "- Is an instruction or request to perform an action (like 'find', 'search', "
            "'show').\n"
            "- Contains lists, product codes, or directives."
            "\n\n"
            "IMPORTANT:\n"
            "- If the request contains BOTH a command AND a question (e.g. find X and tell "
            "me...) ALWAYS consider it a question.\n"
            "- If the user's message is a question, use the scraped informations to give a "
            "clear and concise answer. If the informations are not enough to answer, then "
            "say it explicitly.\n"
            "- If the user's message is a command or a list/sequence of product "
            "names/codes, format the scraped information as a readable product card. "
            "Include all available details returned by the tool, such as provider, price, "
            "specifications, or any other data — do NOT omit or remove any information. "
            "If no information or results are found, clearly notify the user that nothing "
            "was retrieved."
            "\n\n"
            "Before performing a web search using the tool, check whether the item has already "
            "been searched for previously. If the item was already retrieved or exists in the "
            "current context, do not perform another search for it."
        )
    )

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

graph = workflow.compile(checkpointer=InMemorySaver())  # short-term memory



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

        # response = await graph.ainvoke(
        #     {"messages": [{"role": "user", "content": user_input}]}
        # )

        # print(response)

asyncio.run(main())