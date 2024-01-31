#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from bigpt.roles.oss_academic import AcademicOssWatcher

async def main():
    msg = "Grab papers for this week!"
    TimeToReadPaper = AcademicOssWatcher()
    await TimeToReadPaper.run(msg)


asyncio.run(main())