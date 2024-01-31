from metagpt.logs import logger
from metagpt.actions.action import Action
from metagpt.config import CONFIG

import aiohttp
from bs4 import BeautifulSoup

from datetime import datetime, timedelta, date

import subprocess

import json


##### A Document writer realized by action nodes

DIRECTORY_STRUCTION = """
    You are now a seasoned technical professional in the field of the internet. 
    We need you to write a technical tutorial".
    您现在是互联网领域的经验丰富的技术专业人员。
    我们需要您撰写一个技术教程。
    """

# 实例化一个ActionNode，输入对应的参数
DIRECTORY_WRITE = ActionNode(
    # ActionNode的名称
    key="directory",
    # 期望输出的格式
    expected_type=dict,
    # 命令文本
    instruction=DIRECTORY_STRUCTION,
    # 例子输入，在这里我们可以留空
    example="",
 )