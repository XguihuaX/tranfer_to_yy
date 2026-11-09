"""会议通知 → 地点、人数。配合03-03 §3.1–4.1阅读。

沿用lab已有依赖。运行前在本机环境变量中填写：
LLM_API_KEY、LLM_BASE_URL、LLM_MODEL。
实际运行会请求模型服务；本例需要入口支持所用结构化输出方式。
"""

import os

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# 1. 定义我们要提取的两个要素，此处尚未填写任何会议的实际信息。
class MeetingInfo(BaseModel):
    # str：地点是文字；description：说明这个字段要存什么。
    location: str = Field(description="会议举行的地点")

    # int：人数按整数校验；ge=1：人数必须大于等于1，并非默认值为1。
    people: int = Field(ge=1, description="参加会议的人数")


def main():
    # 2. 创建模型客户端。三个实际值从本机运行配置中读取。
    llm = ChatOpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ["LLM_BASE_URL"],
        model=os.environ["LLM_MODEL"],
    )

    # 3. 配置按MeetingInfo的结构返回结果；这一行尚未请求模型。
    extractor = llm.with_structured_output(MeetingInfo)

    # 4. 给出本次原文，发起提取。这里只提供两个字段，不需要提取时间。
    notice = "会议定于周五下午举行，地点在北京，共有8人参加。"
    result = extractor.invoke("请从下面的通知中提取会议信息：\n" + notice)

    # 5. 成功返回的result是一份MeetingInfo对象，可直接读取字段。
    print("会议地点：", result.location)  # 预期：北京
    print("参会人数：", result.people)    # 预期：8


if __name__ == "__main__":
    main()
