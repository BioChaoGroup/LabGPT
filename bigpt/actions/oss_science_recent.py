from metagpt.logs import logger
from metagpt.actions.action import Action
from metagpt.config import CONFIG

import aiohttp
from bs4 import BeautifulSoup

from datetime import datetime, timedelta, date

import subprocess

import json

async def fetch(session, url,proxy_url):
    async with session.get(url,proxy=proxy_url) as response:
        return await response.text()

async def fetch_each(url: str = "https://www.nature.com/nature/reviews-and-analysis", timeframe: str = "daily",journal_name: str="None"):
    # Get today's date
    today = date.today()
    start_date = None
    if timeframe == 'daily':
        start_date = today
    elif timeframe == 'weekly':
        # Set start_date to 7 days before today
        start_date = today - timedelta(days=7)
        
    
    async with aiohttp.ClientSession() as session:
        html_content = await fetch(session, url, "http://127.0.0.1:7897")
        soup = BeautifulSoup(html_content, 'html.parser')
        #soup = souphtml
        articles_list = soup.find_all('li', class_='app-article-list-row__item')

        articles = []

        for article_item in articles_list:
            title_element = article_item.find('h3', class_='c-card__title')
            title = title_element.text.strip() if title_element else None

            summary_element = article_item.find('div', class_='c-card__summary')
            summary = summary_element.p.text.strip() if summary_element else None

            url_element = title_element.find('a') if title_element else None
            url = url_element['href'].strip() if url_element and url_element.has_attr('href') else None

            # Since the provided HTML does not contain a DOI, url is used in its place.
            # In real-world applications, make sure to locate and extract the actual DOI.
            #doi = url

            publish_date_element = article_item.find('time')
            publish_date = publish_date_element.text.strip() if publish_date_element else None

            article_type_element = article_item.find('span', class_='c-meta__type')
            article_type = article_type_element.text.strip() if article_type_element else None

            # The provided HTML does not contain a publish magazine field.
            # In real-world applications, locate and extract it if it exists.
            publish_magazine = journal_name

            article_data = {
                'article_type': article_type,
                'title': title,
                'summary': summary,
                'url': f"https://www.nature.com{url}",
                'publish_date': publish_date,
                'publish_magazine': publish_magazine
            }
            check_date = False
            try:
                article_date = datetime.strptime(publish_date, '%d %b %Y')
                check_date = start_date <= article_date.date()
            except ValueError:
                # If there is an issue with parsing the date, we'll consider it not matching
                check_date = False
                
            if check_date and "News" not in article_data['article_type']:
                articles.append(article_data)

        return articles  

class CrawlNatureArticles(Action):
        
    async def run(self, url: str="https://www.nature.com"):
        url = url # not needed.
        logger.info(f"[CrawlNatureArticles]: ready to fetch from nature")
        nature = await fetch_each('https://www.nature.com/nature/reviews-and-analysis','weekly',"Nature")
        logger.info(f"[CrawlNatureArticles]: ready to fetch from Nature biotechnology")
        nbt = await fetch_each('https://www.nature.com/nbt/research-articles','weekly',"Nature biotechnology")
        logger.info(f"[CrawlNatureArticles]: ready to fetch from Nature Communications")
        ncomms = await fetch_each('https://www.nature.com/ncomms/research-articles','weekly',"Nature Communications")
        logger.info(f"[CrawlNatureArticles]: ready to fetch from Nature Microbiology")
        nmicrobiol = await fetch_each('https://www.nature.com/nmicrobiol/research-articles','weekly',"Nature Microbiology")
        logger.info(f"[CrawlNatureArticles]: ready to fetch from Nature Methods")
        nmeth = await fetch_each('https://www.nature.com/nmeth/research-articles','weekly',"Nature Methods")
        logger.info(f"[CrawlNatureArticles]: all fetched")
        resps = nature + nbt + ncomms + nmicrobiol + nmeth
        resps_json = json.dumps(resps,indent=4)
        return resps_json
        

from typing import Any
from metagpt.actions.action import Action


TRENDING_ANALYSIS_PROMPT = """# 任务要求
你是一位文献调研员. 你被要求从如下提供的「文章内容汇总」中,基于各大杂志擅长领域和其近期发表的文献,筛选与"宏基因组学、环境微生物、测序技术、生物信息学"有关的内容,汇总生成一篇报告,向用户提供其中的亮点和个性化推荐. 

内容风格请参考以下大纲:
# 「本周顶刊」 标题 (取一个生动的标题、突出亮点)
## 热点领域：汇总热点研究！探索研究热点领域，并发现吸引学者注意的关键领域。从**到**，以前所未有的方式见证顶级研究。
## 列表亮点：聚焦文献标题, 为用户提供独特且引人注目的内容。


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

# 总结:
概括主要内容,形成结论.

资料来源: 
 - [list the main domains from provided urls]
 
小编: *请给出你的大模型名称(版本号)*
主编: *CIAO*


附:
「文章内容汇总」:
{articles}
"""

class AnalysisOSSTrending(Action):

    async def run(
        self,
        articles: Any
    ):
        return await self._aask(TRENDING_ANALYSIS_PROMPT.format(articles=articles))
    
    
    
class pushOSS_to_hexo(Action):

    name: str = "pushOSS_to_hexo"

    async def run(self, article: str ):
        # get today's date with format like 2024-01-22
        repo = CONFIG.get("HEXO_LOCAL_DIR")

        today = date.today().strftime("%Y-%m-%d")
        # Run bash command : hexo new block "Daily highlight"
        command = f"cd {repo} && hexo new post 'Top Paper weekly'"
        logger.info(f"bash: {command}")
        subprocess.run(command, shell=True, cwd=repo)
        
        # write {article} into source/_posts/2024-01-22_Top_Paper_weekly.md
        with open(f"{repo}/source/_posts/{today}-Top-Paper-weekly.md", "a") as f:
            f.write(article)
        logger.info(f"hexo blog written!")
        
        # Automatically deploy to remote 
        # BUT NOT RECOMMENDED. Review the content before you release anything generated by AI.
        subprocess.run('hexo d -g', shell=True, cwd=repo)
