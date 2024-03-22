# Oringinal code copyed from 《MetaGPT智能体开发入门》教程

import datetime
import sys
from typing import Optional
from uuid import uuid4

from aiocron import crontab
from metagpt.actions import UserRequirement
from metagpt.roles import Role
from metagpt.schema import Message
#from metagpt.tools.web_browser_engine import WebBrowserEngine
#from bigpt.tools.web_xml_engine import WebXmlEngine # support Xml

from metagpt.utils.common import CodeParser, any_to_str
from metagpt.utils.parse_html import _get_soup
from pytz import BaseTzInfo
from metagpt.logs import logger

from bigpt.actions.OSSs import WriteCrawlerCode, ParseSubRequirement, RunSubscription , RunSubscriptionImmediantlyOneTime
from bigpt.actions.oss_nature_recent import pushOSS_to_hexo

# 定义博客发布员
class BlogPublisher(Role):
    name: str ="铙博客(Knowledge Broker)"
    profile: str ="Knowledge Broker"

    goal: str = "Save reports into markdown files and prepare to publish in blog."
    constraints: str = "utilize the same language as the User Requirement"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.set_actions([pushOSS_to_hexo])
        self._watch([RunSubscriptionImmediantlyOneTime])
        
        
# 定义爬虫工程师角色
class CrawlerEngineer(Role):
    name: str = "John"
    profile: str = "Crawling Engineer"
    goal: str = "Write elegant, readable, extensible, efficient code"
    constraints: str = "The code should conform to standards like PEP8 and be modular and maintainable"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.set_actions([WriteCrawlerCode])
        self._watch([ParseSubRequirement])

# 定义订阅助手角色
class SubscriptionAssistant(Role):
    """Analyze user subscription requirements."""

    name: str = "Grace"
    profile: str = "Subscription Assistant"
    goal: str = "analyze user subscription requirements to provide personalized subscription services."
    constraints: str = "utilize the same language as the User Requirement"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        #self._init_actions([ParseSubRequirement, RunSubscription])
        self.set_actions([ParseSubRequirement, RunSubscriptionImmediantlyOneTime])
        self._watch([UserRequirement, WriteCrawlerCode])

    async def _think(self) -> bool:
        cause_by = self.rc.history[-1].cause_by
        if cause_by == any_to_str(UserRequirement):
            state = 0
        elif cause_by == any_to_str(WriteCrawlerCode):
            state = 1

        if self.rc.state == state:
            self.rc.todo = None
            return False
        self._set_state(state)
        return True

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        response = await self.rc.todo.run(self.rc.history)
        msg = Message(
            content=response.content,
            instruct_content=response.instruct_content,
            role=self.profile,
            cause_by=self.rc.todo,
            sent_from=self,
        )
        self.rc.memory.add(msg)
        return msg