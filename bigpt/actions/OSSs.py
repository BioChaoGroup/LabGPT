# Oringinal code copyed from 《MetaGPT智能体开发入门》教程

import datetime
import sys
from typing import Optional
from uuid import uuid4

from aiocron import crontab
from metagpt.actions import UserRequirement
from metagpt.actions.action import Action
from metagpt.actions.action_node import ActionNode
from metagpt.schema import Message
from metagpt.tools.web_browser_engine import WebBrowserEngine
from bigpt.tools.web_xml_engine import WebXmlEngine # support Xml
from metagpt.utils.common import CodeParser, any_to_str
from pytz import BaseTzInfo
from metagpt.logs import logger

# 先写NODES
LANGUAGE = ActionNode(
    key="Language",
    expected_type=str,
    instruction="Provide the language used in the project, typically matching the user's requirement language.",
    example="en_us",
)

CRON_EXPRESSION = ActionNode(
    key="Cron Expression",
    expected_type=str,
    instruction="If the user requires scheduled triggering, please provide the corresponding 5-field cron expression. "
    "Otherwise, leave it blank.",
    example="",
)

CRAWLER_URL_LIST = ActionNode(
    key="Crawler URL List",
    expected_type=list[str],
    instruction="List the URLs user want to crawl. Leave it blank if not provided in the User Requirement.",
    example=["https://example1.com", "https://example2.com","https://example2.com/rss"],
)

PAGE_CONTENT_EXTRACTION = ActionNode(
    key="Page Content Extraction",
    expected_type=str,
    instruction="Specify the requirements and tips to extract from the crawled web pages based on User Requirement.",
    example="Retrieve the titles and content of articles published today.",
)

CRAWL_POST_PROCESSING = ActionNode(
    key="Crawl Post Processing",
    expected_type=str,
    instruction="Specify the processing to be applied to the crawled content, such as summarizing today's news.",
    example="Generate a summary of today's news articles.",
)

INFORMATION_SUPPLEMENT = ActionNode(
    key="Information Supplement",
    expected_type=str,
    instruction="If unable to obtain the Cron Expression, prompt the user to provide the time to receive subscription "
    "messages. If unable to obtain the URL List Crawler, prompt the user to provide the URLs they want to crawl. Keep it "
    "blank if everything is clear",
    example="",
)

NODES = [
    LANGUAGE,
    CRON_EXPRESSION,
    CRAWLER_URL_LIST,
    PAGE_CONTENT_EXTRACTION,
    CRAWL_POST_PROCESSING,
    INFORMATION_SUPPLEMENT,
]

PARSE_SUB_REQUIREMENTS_NODE = ActionNode.from_children("ParseSubscriptionReq", NODES)

PARSE_SUB_REQUIREMENT_TEMPLATE = """
### User Requirement
{requirements}
"""

SUB_ACTION_TEMPLATE = """
## Requirements
Answer the question based on the provided context {process}. If the question cannot be answered, please summarize the context.

## context
{data}"
"""

TRENDING_ANALYSIS_PROMPT = """# 任务要求
你是一位文献调研员. 你被要求基于{process}提供的内容回答问题。如果无法回答，则总结内容。

从如下提供的「文章内容汇总」中,基于各大杂志擅长领域和其近期发表的文献,筛选与"宏基因组学、环境微生物、测序技术、生物信息学"有关的内容,汇总生成一篇报告,向用户提供其中的亮点和个性化推荐. 

内容风格请参考以下大纲:
# 「本周顶刊」 标题 (取一个生动的标题、突出本周消息的新颖性)
## 热点领域：汇总热点研究！（探索研究热点领域，并发现吸引学者注意的关键领域。从**到**，以前所未有的方式见证顶级研究.列出3～5条）
## 列表亮点：（聚焦文献标题, 为用户提供独特且引人注目的内容。.列出3～5条）


报告内容请严格按照以下格式生成:

# 「本周顶刊」 T2T组装新算法取得重大进展
## 热点领域
1. 代谢通路新突破
    - **magazine** | published date
      [title1](url)
      summary ...
    - **magazine** | published date
      [title1](url)
      summary ...
2. ...
...

## 热点文章
1. **magazine** | published date
      [title1](url)
      摘要: summary ...
      点评: 提供推荐此项目的具体原因
2. **magazine** | published date
      [title1](url)
      摘要: summary ...
      点评: 提供推荐此项目的具体原因
3. ...
...

# 总结
概括主要内容,形成结论.

资料来源: 
 - [list the main domains from provided urls]
 
小编: *请给出你的大模型名称(版本号)*
主编: *CIAO*


附:
「文章内容汇总」:
{data}
"""


PROMPT_TEMPLATE = """Please complete the web page crawler parse function to achieve the User Requirement. The parse \
function should take a BeautifulSoup object as input, which corresponds to the HTML outline provided in the Context.

```python
from bs4 import BeautifulSoup

# only complete the parse function
def parse(soup: BeautifulSoup):
    ...
    # Return the object that the user wants to retrieve, don't use print
```

## User Requirement
{requirement}

## Context

The outline of the web page to scrabe is show like below:

```tree
{outline}
```
"""

PROMPT_TEMPLATE_XML = """Please complete the xml formated page crawler parse function to achieve the User Requirement. The parse \
function should take a BeautifulSoup object as input, which corresponds to the outline provided in the Context.

```python
from bs4 import BeautifulSoup

# only complete the parse function
def parse(soup: BeautifulSoup):
    ...
    # Return the object that the user wants to retrieve, don't use print
```

## User Requirement
{requirement}

## Context

The outline of the xml page to scrabe is show like below:

```tree
{outline}
```
"""


# 辅助函数: 获取html css大纲视图
def get_html_outline(page):
    from metagpt.utils.parse_html import _get_soup
    soup = _get_soup(page.html)
    outline = []

    def process_element(element, depth):
        name = element.name
        if not name:
            return
        if name in ["script", "style"]:
            return

        element_info = {"name": element.name, "depth": depth}

        if name in ["svg"]:
            element_info["text"] = None
            outline.append(element_info)
            return

        element_info["text"] = element.string
        # Check if the element has an "id" attribute
        if "id" in element.attrs:
            element_info["id"] = element["id"]

        if "class" in element.attrs:
            element_info["class"] = element["class"]
        outline.append(element_info)
        for child in element.children:
            process_element(child, depth + 1)

    for element in soup.body.children:
        process_element(element, 1)

    return outline

# 辅助函数: 获取XML css大纲视图
def get_xml_outline(page):
    from bigpt.utils.parse_xml import _get_soup
    soup = _get_soup(page.inner_text)
    outline = []

    # Recursively process each element
    def process_element(element, depth):
        name = element.name
        if not name:
            return

        # Simplify element info to name and depth
        element_info = {"name": name, "depth": depth, "text":""}
            
        # Optional: Fetch text content for specific tags

        if name in ["publicationName", "publicationDate","content","date","Date"]:
            element_info['text'] = element.get_text(strip=True)

        # Add element info to outline
        outline.append(element_info)

        # Process child elements recursively
        for child in element.children:
            process_element(child, depth + 1)
            
    # Start processing from the root element
    process_element(soup, 0)

    return outline


# 触发器：crontab
class CronTrigger:
    def __init__(self, spec: str, tz: Optional[BaseTzInfo] = None) -> None:
        segs = spec.split(" ")
        if len(segs) == 6:
            spec = " ".join(segs[1:])
        self.crontab = crontab(spec, tz=tz)

    def __aiter__(self):
        return self

    async def __anext__(self):
        await self.crontab.next()
        return Message(datetime.datetime.now().isoformat())

# 写爬虫代码的Action
class WriteCrawlerCode(Action):
    async def run(self, requirement):
        requirement: Message = requirement[-1]
        data = requirement.instruct_content.dict()
        urls = data["Crawler URL List"]
        query = data["Page Content Extraction"]

        codes = {}
        for url in urls:
            if url.endswith('rss'):
                codes[url] = await self._write_code4xml(url, query)
            else:
                codes[url] = await self._write_code4html(url, query)
        return "\n".join(f"# {url}\n{code}" for url, code in codes.items())

    async def _write_code4html(self, url, query):
        page = await WebBrowserEngine().run(url)
        outline = get_html_outline(page)
        outline = "\n".join(
            f"{' '*i['depth']}{'.'.join([i['name'], *i.get('class', [])])}: {i['text'] if i['text'] else ''}"
            for i in outline
        )
        code_rsp = await self._aask(PROMPT_TEMPLATE.format(outline=outline, requirement=query))
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def _write_code4xml(self, url, query):
        page = await WebXmlEngine().run(url)
        outline = get_xml_outline(page)
        outline2 = "\n".join(
            f"{' '*i['depth']}{'.'.join([i['name'], *i.get('class', [])])}: {i['text'] if i['text'] else ''}"
            for i in outline
        )
        code_rsp = await self._aask(PROMPT_TEMPLATE_XML.format(outline=outline2, requirement=query))
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code
    
    
# 分析订阅需求的Action
class ParseSubRequirement(Action):
    async def run(self, requirements):
        requirements = "\n".join(i.content for i in requirements)
        context = PARSE_SUB_REQUIREMENT_TEMPLATE.format(requirements=requirements)
        node = await PARSE_SUB_REQUIREMENTS_NODE.fill(context=context, llm=self.llm)
        return node

# 运行订阅智能体的Action
class RunSubscription(Action):
    async def run(self, msgs):
        from metagpt.roles.role import Role
        from metagpt.subscription import SubscriptionRunner

        code = msgs[-1].content
        req = msgs[-2].instruct_content.dict()
        urls = req["Crawler URL List"]
        process = req["Crawl Post Processing"]
        spec = req["Cron Expression"]
        SubAction = self.create_sub_action_cls(urls, code, process)
        SubRole = type("SubRole", (Role,), {})
        role = SubRole()
        role.set_actions([SubAction])
        runner = SubscriptionRunner()

        async def callback(msg):
            print(msg)

        await runner.subscribe(role, CronTrigger(spec), callback)
        await runner.run()


    @staticmethod
    def create_sub_action_cls(urls: list[str], code: str, process: str):
        modules = {}
        for url in urls[::-1]:
            code, current = code.rsplit(f"# {url}", maxsplit=1)
            name = uuid4().hex
            module = type(sys)(name)
            exec(current, module.__dict__)
            modules[url] = module

        class SubAction(Action):
            async def run(self, *args, **kwargs):
                pages = await WebBrowserEngine().run(*urls)
                if len(urls) == 1:
                    pages = [pages]

                data = []
                for url, page in zip(urls, pages):
                    data.append(getattr(modules[url], "parse")(page.soup))
                return await self.llm.aask(SUB_ACTION_TEMPLATE.format(process=process, data=data))

        return SubAction
    
    
class RunSubscriptionImmediantlyOneTime(Action):
    async def run(self, msgs):
        from metagpt.roles.role import Role
#        from metagpt.subscription import SubscriptionRunner

        # 原有代码逻辑
        code = msgs[-1].content
        req = msgs[-2].instruct_content.dict()
        urls = req["Crawler URL List"]
        process = req["Crawl Post Processing"]
        # spec = req["Cron Expression"]  # 不再需要定时表达式
        SubAction = self.create_sub_action_cls(urls, code, process)

        # 创建 SubRole 和绑定动作
        SubRole = type("SubRole", (Role,), {})
        role = SubRole()
        role.set_actions([SubAction])
        
        msg = Message(content="直接执行")
        # 直接运行一次 SubRole 的任务，不使用 SubscriptionRunner
        # 假设直接运行的逻辑和callback处理方式相同
        return await role.run(msg)
        
    @staticmethod
    def create_sub_action_cls(urls: list[str], code: str, process: str):
        modules = {}
        for url in urls[::-1]:
            code, current = code.rsplit(f"# {url}", maxsplit=1)
            name = uuid4().hex
            module = type(sys)(name)
            exec(current, module.__dict__)
            modules[url] = module
        
        class SubAction(Action):
            async def run(self, *args, **kwargs):
                from bigpt.utils.parse_xml import _get_soup
                #pages = await WebBrowserEngine().run(*urls)
                #if len(urls) == 1:
                #    pages = [pages]

                articles = []
                for url in urls[::-1]:
                    if url.endswith('rss'):
                        page = await WebXmlEngine().run(url)
                        soup = _get_soup(page.inner_text)
                        try:
                            articles.append(getattr(modules[url], "parse")(soup))
                        except:
                            logger.info(f"Data from url not found")
                    else:
                        page = await WebBrowserEngine().run(url)
                        try:
                            articles.append(getattr(modules[url], "parse")(page.soup))
                        except:
                            logger.info(f"Data from url not found")
                str_articles = '\n'.join(str(x) for x in articles)
                FORMAT_PROMPT = TRENDING_ANALYSIS_PROMPT.format(process=process, data=str_articles)
                logger.info(f"Asking:\n{FORMAT_PROMPT}")
                return await self.llm.aask(FORMAT_PROMPT)
        return SubAction