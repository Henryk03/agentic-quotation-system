
import asyncio

from typing import Literal
from utils import ClassifyRequest
from agent_tools import scrape_products
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition


response_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.5
)

classifier_model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0.5
)


async def scrape_items_or_respond(state: MessagesState):
    """
    Call the model to generate a response based on the current state.
    Given the request, it will decide to scrape the asked products
    using the scraping tool, or simply respond to the user.
    """

    system_message = SystemMessage(
        content=(
            "You are an assistant that helps the user prepare quotations "
            "by searching for and collecting the requested items from the web.\n"
            "When you identify a product code - that can appear in various formats, sometimes "
            "made only of numbers (e.g. '14000'), or a mix of letters, numbers and symbols "
            "(e.g. 'A.B1 23', 'XW-200') - handle it exactly as written — do not modify, translate, "
            "or add words to it.\n\nIf the user writes item names in the plural form, convert them "
            "to singular form before processing or searching for them (do not mention this skill of "
            "yours to the user, it is only to be able to use the scraping tool correctly).\n"
            "If the tool raises an exception, explain clearly what happened to the user and "
            "how to solve the problem.\n\n"
            "All responses MUST be written in Italian."
        )
    )

    messages = [system_message] + state["messages"]
    
    response = await response_model.bind_tools(
        [scrape_products]
    ).ainvoke(
        messages
    )

    return {"messages": [response]}


async def __is_question(message: str) -> bool:
    """
    Analyze the given message and return `True` if it is
    is a question, `False` otherwise.
    """

    system_message = SystemMessage(
        content=(
            "You are a message intent classifier.\n"
            "Your task is to determine whether a user message is a question or a command.\n\n"
            "A **question** typically:\n"
            "- contains a question mark (?).\n"
            "- starts with interrogative words (who, what, when, where, why, how).\n"
            "- asks for information, comparison, clarification or availability.\n"
            "- could also contain a command, but it's still asking you something about one or more products.\n"
            "A **command** typically:\n"
            "- is an instruction or request to perform an action (like 'find', 'search', 'show').\n"
            "- contains lists, product codes, or directives.\n\n"
            "You must respond only with one of these two labels: 'question' or 'command'."
        )
    )

    response = await classifier_model.with_structured_output(
        ClassifyRequest
    ).ainvoke(
        [system_message, {"role": "user", "content": message}]
    )

    result = getattr(response, "request_class", None)

    return str(result).strip().lower() == "question"


async def generate_answer(state: MessagesState):
    """
    Interpret the user's message and generate a response based
    on the user's request.
    """

    request = state["messages"][0].content
    scraped_info = state["messages"][-1].content

    if await __is_question(request):
        instructions = (
            "The user's message is a question. Use the scraped informations "
            "to give a clear and concise answer. If the informations are not "
            "enough to answer, then say it explicitly."
        )
    else:
        instructions = (
            "The user's message is a command or a list/sequence of products. "
            "Show the scraped informations as they are - without modifing, rewriting "
            "or summarizing them. If there is nothing or no result has been found, "
            "notify it to the user."
        )

    prompt = (
        f"{instructions}\n\n"
        f"User message: {request}\n"
        f"Scraped information:\n{scraped_info}\n"
    )

    response = await response_model.ainvoke([{"role": "user", "content": prompt}])

    return {"messages": [response]}


# graph assembly
workflow = StateGraph(MessagesState)

workflow.add_node("scrape_items_or_respond", scrape_items_or_respond)
workflow.add_node("scrape_tool", ToolNode([scrape_products]))
workflow.add_node("generate_answer", generate_answer)

workflow.add_edge(START, "scrape_items_or_respond")

workflow.add_conditional_edges(
    "scrape_items_or_respond",
    tools_condition,
    {"tools": "scrape_tool", END: END}
)

workflow.add_edge("scrape_tool", "generate_answer")
workflow.add_edge("generate_answer", END)

graph = workflow.compile()



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