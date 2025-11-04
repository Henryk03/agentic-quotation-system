
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
    temperature=0
)

classifier_model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0
)


async def scrape_items_or_respond(state: MessagesState):
    """
    Call the model to generate a response based on the current state.
    Given the question, it will decide to scrape the asked products
    using the scraping tool, or simply respond to the user.
    """

    system_message = SystemMessage(
        content=(
            "You are an assistant that helps the user "
            "preparing quotations, scraping the requesting "
            "items off the web. Always respond in Italian "
            "and never include words into the tool call with "
            "what may appear to be a product code in your web search."
        )
    )

    messages = [system_message] + state["messages"]
    response = await response_model.bind_tools([scrape_products]).ainvoke(messages)

    return {"messages": [response]}


async def generate_answer(state: MessagesState):
    """
    Generate an answer based on what the user is asking about
    the retrieved item(s).
    """

    question = state["messages"][1]     # not [0] cause it's the SystemMessage
    scraped_info = state["messages"][2]

    prompt = (
        "Use the following scraped informations to answer the "
        "question. If you cannot extract the required informations "
        "to answer, just say that the scraped items do not contain "
        "enough elements to answer.\n"
        f"Question: {question}\n"
        f"Scraped informations: {scraped_info}\n"
    )

    response = await response_model.ainvoke([{"role": "user", "content": prompt}])

    return {"messages": [response]}


async def classify_request(state: MessagesState) -> Literal["question", "end"]:
    """"""

    request = state["messages"][1]

    prompt = (
        "You are a classifier of user requests.\n"
        f"Here is the user request: '{request}'.\n"
        "If the request contains a question mark or it seems like "
        "a question, classify it as 'question', otherwise as 'command'."
    )

    response = await classifier_model.with_structured_output(
        ClassifyRequest
    ).ainvoke(
        [{"role": "user", "content": prompt}]
    )

    match response:
        case "question":
            return "question"
        case "command":
            return "end"



# graph assembly
workflow = StateGraph(MessagesState)

workflow.add_node(scrape_items_or_respond)
workflow.add_node("scrape_tool", ToolNode([scrape_products]))
workflow.add_node(generate_answer)

workflow.add_edge(START, "scrape_items_or_respond")

workflow.add_conditional_edges(
    "scrape_items_or_respond",
    tools_condition,
    {"tools": "scrape_tool", END: END}
)

workflow.add_conditional_edges(
    "scrape_tool",
    classify_request,
    {"question": "generate_answer", "end": END}
)

workflow.add_edge("generate_answer", END)
workflow.add_edge("scrape_tool", END)

graph = workflow.compile()



async def main():

    while True:

        user_input = input().strip().lower()

        if user_input == "stop":
            break

        async for chunk in graph.astream(
            {
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            }
        ):
            for _, update in chunk.items():
                update["messages"][-1].pretty_print()

asyncio.run(main())