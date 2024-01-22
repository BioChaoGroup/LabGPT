from metagpt.logs import logger
from metagpt.schema import Message
from bigpt.actions.oss_nature_recent import CrawlNatureArticles, AnalysisOSSTrending, pushOSS_to_hexo
from metagpt.roles.role import Role, RoleReactMode
#from metagpt.provider.zhipuai_api import ZhiPuAILLM
from pydantic import BaseModel, Field
from metagpt.provider.base_llm import BaseLLM

class AcademicOssWatcher(Role):
    name: str ="铙博客(Knowledge Broker)"
    profile: str ="Knowledge Broker"
    #llm: BaseLLM = Field(default_factory=lambda: LLM(LLMProviderEnum.ZHIPUAI), exclude=True)  # Feel free to try ZHIPUAI :)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._init_actions([CrawlNatureArticles, AnalysisOSSTrending,pushOSS_to_hexo])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")

        todo = self.rc.todo

        msg = self.get_memories(k=1)[0] # find the most k recent messages
        result = await todo.run(msg.content)

        msg = Message(content=str(result), role=self.profile, cause_by=type(todo))

        self.rc.memory.add(msg)
        return msg
    
    
