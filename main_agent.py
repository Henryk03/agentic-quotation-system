
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
    model="gemini-2.5-flash",
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
            "You are an assistant that helps the user prepare quotations "
            "by searching for and collecting the requested items from the web.\n"
            "When you identify a product code (even if it consists only of numbers), "
            "do not add, modify, or append anything to it - reproduce it exactly as it "
            "appears, without articles, extra words, or unnecessary punctuation.\n"
            "If the user writes item names in the plural form, convert them to singular "
            "form before processing or searching for them.\n"
            "All responses must be written in Italian."
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
        "Use the following scraped information to answer the question.\n"
        "If you cannot extract the required information to answer, simply "
        "say that the scraped items do not contain enough elements to answer.\n\n"
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
        "Classify the request strictly as one of:\n"
        "- 'question': the user is asking for information about one or more items, "
        "e.g. price, availability, features, comparisons, instructions, or the text "
        "contains an interrogative word/phrase (e.g. 'how', 'what', 'where', 'when', "
        "'why', 'who', 'which', 'quanto', 'dove', 'perché', 'quanto costa', 'che prezzo') "
        "OR the sentence uses a question structure even if there is no question mark "
        "(e.g. verbs like 'costare', 'avere', 'funzionare', 'posso', 'puoi', 'come faccio').\n"
        "- 'command': the user is giving an instruction to perform a task such as "
        "searching, scraping, or listing products, without asking for information.\n"
        "Important rules:\n"
        "1. Treat numeric tokens (e.g. '14000') as part of the utterance — DO NOT assume "
        "that a numeric token alone makes the request a command. If an interrogative word "
        "or question-like verb co-occurs with numbers, classify as 'question'.\n"
        "2. If the request contains a clear imperative verb (e.g. 'find', 'scrape', 'show me', "
        "'cerca', 'mostrami'), classify as 'command'.\n"
        "3. If uncertain, err on the side of 'command'.\n"
        "Return only one word exactly: 'question' or 'command'.\n"
    )

    # the response is a pydantic object
    response = await classifier_model.with_structured_output(
        ClassifyRequest
    ).ainvoke(
        [{"role": "user", "content": prompt}]
    )

    request_class = getattr(response, "request_class", None)
    print(request_class)

    match request_class:
        case "question":
            return "question"
        case "command":
            return "end"
        case _:
            return "command"



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