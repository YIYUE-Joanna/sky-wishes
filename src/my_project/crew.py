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
    strategy: str = ""   # 存储内部策略（可选，不在 Kanban 显示）
    steps: List[str] = [] # 存储具体的行动步骤，用于 Kanban 展示

@CrewBase
class MyProjectCrew():
    """Wish Architect Crew - 愿望架构师团队"""

    # 使用你指定的 Gemini 2.5 Flash
    gemini_llm = LLM(
        model="gemini/gemini-2.5-flash", 
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.8, # 稍微调高，增加语言的灵动性和感性
        verbose=True
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
            output_pydantic=WishPlan # 强制输出结构化数据
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
        )