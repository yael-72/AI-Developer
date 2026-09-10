from dataclasses import dataclass

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.tools import tool

import os
from firecrawl import FirecrawlApp

from core.store import SourceStore, store
from core.sources import format_docs

firecrawl = FirecrawlApp(
    api_key=os.getenv("FIRECRAWL_API_KEY")
)


@dataclass
class Answer:
    text: str
    sources: list[str]
    interrupt: dict | None = None

MODEL = "anthropic:claude-sonnet-4-6"

CHECKPOINTER = InMemorySaver()

SYSTEM_PROMPT = """
You are an AI assistant for a NotebookLM-style application.

Your job is to answer questions using uploaded source documents.

Rules:

1. For questions related to uploaded documents:
   - ALWAYS call search_sources first.
   - Use only information returned from search_sources.

2. If the retrieved documents contain a direct answer:
   - Answer only using those documents.
   - Mention the source.

3. If the retrieved documents only contain related keywords
   but do not directly answer the question:
   - Treat it as not found.
   - Call web_search.

4. Available tools:
   - search_sources
   - list_sources
   - get_source
   - generate_search_queries
   - web_search
   - scrape_url
   - crawl_url

5. Language:
   - Always answer in the same language as the user's question.

6. Do not invent information.
"""


def _make_tools(store: SourceStore):

    @tool
    def search_sources(query: str) -> str:
        """
        Find passages in uploaded sources relevant to a query.
        """

        docs = store.search(query=query)

        if not docs:
            return "No relevant documents found."

        return format_docs(docs)


    @tool
    def list_sources() -> str:
        """
        List all available source documents.
        """

        sources = store.list()

        if not sources:
            return "No sources are available."

        return "\n".join(
            f"- {source.name} (id: {source.id})"
            for source in sources
        )


    @tool
    def get_source(source_id: str) -> str:
        """
        Get a source document by id.
        """

        source = store.get(source_id)

        if source is None:
            return f"Source {source_id} not found."

        return (
            f"Source: {source.name}\n\n"
            f"{source.content}"
        )


    @tool
    def generate_search_queries(topic: str) -> list[str]:
        """
        Generate several search queries from different angles.
        """

        prompt = f"""
Generate 4 different web search queries for this topic:

{topic}

Rules:
- One general query.
- One official documentation query.
- One recent updates/news query.
- One tutorial or guide query.

Return only the queries, one per line.
"""

        response = create_agent(
            model=MODEL,
            system_prompt="You generate search queries only.",
        ).invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )


        text = response["messages"][-1].text

        return [
            q.strip("- ").strip()
            for q in text.splitlines()
            if q.strip()
        ]


    @tool
    def web_search(query: str) -> str:
        """
        Search the web, ask the user to select sources,
        then scrape selected sources and add them to the store.
        """

        print(f"🌐 WEB SEARCH TOOL CALLED: {query}")

        queries = generate_search_queries.invoke(
            {"topic": query}
        )

        all_results = []

        for search_query in queries:
            print(f"🔎 SEARCH QUERY: {search_query}")

            results = firecrawl.search(search_query)

            if results and results.web:
                all_results.extend(results.web)

        if not all_results:
            return "No web results found."

        sources = []

        for index, result in enumerate(all_results[:5], start=1):
            if result.url:
                sources.append(
                    {
                        "id": index,
                        "url": result.url
                    }
                )

        selected = interrupt(
            {
                "type": "source_selection",
                "sources": sources
            }
        )

        texts = []

        for item in selected:

            if isinstance(item, str):
                url = item
            else:
                url = item["url"]

            print(f"📄 SCRAPING SELECTED: {url}")

            try:
                page = firecrawl.scrape_url(url)

                if page:
                    content = str(page)

                    store.add(
                        name=url,
                        content=content
                    )

                    texts.append(content[:1000])

            except Exception as e:
                print(
                    f"⚠️ Failed scraping {url}: {e}"
                )

        if not texts:
            return "No useful sources selected."

        return "\n\n".join(texts)

    @tool
    def scrape_url(url: str) -> str:
        """
        Extract content from a webpage.
        """

        result = firecrawl.scrape_url(url)

        if not result:
            return "Could not scrape URL."

        return str(result)


    @tool
    def crawl_url(url: str) -> str:
        """
        Crawl multiple pages from a website.
        """

        result = firecrawl.crawl_url(url)

        if not result:
            return "Could not crawl URL."

        return str(result)



    return [
        search_sources,
        list_sources,
        get_source,
        generate_search_queries,
        web_search,
        scrape_url,
        crawl_url
    ]

LAST_AGENT = None


def answer(question: str, thread_id: str) -> Answer:

    agent = create_agent(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=CHECKPOINTER,
        tools=_make_tools(store)
    )

    global LAST_AGENT
    LAST_AGENT = agent

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    print("🚦 HITL ENABLED")

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        },
        config=config,
    )

    if "__interrupt__" in result:
        return Answer(
            text="",
            sources=[],
            interrupt=result["__interrupt__"][0].value
        )

    text = result["messages"][-1].text

    return Answer(
        text=text,
        sources=[]
    )

def resume(thread_id: str, decision):

    print("========== RESUME DECISION ==========")
    print(type(decision))
    print(decision)
    print("=====================================")

    if LAST_AGENT is None:
        raise Exception("No active agent session")

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = LAST_AGENT.invoke(
        Command(resume=decision),
        config=config
    )

    text = result["messages"][-1].text

    return Answer(
        text=text,
        sources=[]
    )