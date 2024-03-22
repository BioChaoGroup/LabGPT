import asyncio
from metagpt.team import Team
from bigpt.roles.OSS import SubscriptionAssistant, CrawlerEngineer, BlogPublisher

team = Team()
team.hire([SubscriptionAssistant(), CrawlerEngineer(), BlogPublisher()])
#team.run_project("从36kr创投平台https://pitchhub.36kr.com/financing-flash爬取所有初创企业融资的信息，获取标题，链接， 时间，总结今天的融资新闻，然后在14:39发送给我")
#team.run_project("从36kr创投平台https://pitchhub.36kr.com/financing-flash爬取所有初创企业融资的信息，获取标题，链接， 时间，总结今天的融资新闻")
team.run_project("""从以下网站上爬取最近一周内发表的有文章，获取杂志名称，标题，时间, 链接，内容。然后总结科研新进展,并排版成博客文章内容。
Nature: https://www.nature.com/nature.rss;
Nature biotechnology: https://www.nature.com/nbt.rss
Nature Microbiology: https://www.nature.com/nmicrobiol.rss
""")
#Nature biotechnology: https://www.nature.com/nbt.rss
#Nature Microbiology: https://www.nature.com/nmicrobiol.rss
#Nature Communications: https://www.nature.com/ncomms.rss
#Cell期刊(http://www.cell.com/cell/current.rss

asyncio.run(team.run())