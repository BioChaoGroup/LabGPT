#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bigpt.roles.oss_academic import AcademicOssWatcher

async def main():
    TimeToReadPaper = AcademicOssWatcher()
    await TimeToReadPaper.run()