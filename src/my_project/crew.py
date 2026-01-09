from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel
from typing import List
import os

# 定义输出结构
class WishPlan(BaseModel):
    is_prohibited: bool
    response: str        # 存储温暖、感性的总结
    lantern_name: str = ""
    strategy: str = ""   # 存储内部策略
    steps: List[str] = [] # 存储具体的行动步骤

@CrewBase
class MyProjectCrew():
    """Wish Architect Crew - 愿望架构师团队"""

    # 修改：增加初始化方法来接收动态模型 ID
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name
        # 动态初始化 LLM，增加重试配置提高稳定性
        self.gemini_llm = LLM(
            model=f"gemini/{self.model_name}", 
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.8,
            max_retries=1 # 遇到临时网络问题自动重试一次
        )

    @agent
    def wish_guard(self) -> Agent:
        return Agent(
            config=self.agents_config['wish_guard'],
            llm=self.gemini_llm, 
            verbose=True
        )

    @agent
    def wish_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['wish_architect'],
            llm=self.gemini_llm,
            verbose=True
        )

    @task
    def intercept_task(self) -> Task:
        return Task(config=self.tasks_config['intercept_task'])

    @task
    def architecture_task(self) -> Task:
        return Task(
            config=self.tasks_config['architecture_task'],
            output_pydantic=WishPlan 
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
        )