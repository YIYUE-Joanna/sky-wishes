from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel
from typing import List
import os

# 定义输出结构，方便前端展示
class WishPlan(BaseModel):
    is_prohibited: bool
    response: str
    lantern_name: str = ""
    strategy: str = ""
    steps: List[str] = []

@CrewBase
class MyProjectCrew():
    """Wish Architect Crew - 天灯愿望架构师团队"""

    # --- 核心修复：使用更具体的模型版本名称 ---
    # 按照 2026 年初的建议，gemini-1.5-flash-001 比简写版更稳健
    # 如果运行后依然报 404，请将下方 model 改为 "gemini/gemini-1.0-pro"
    gemini_llm = LLM(
    model="gemini-2.5-flash", # 主要推荐：快速且免费
    # 如果上面失败的备选："gemini-2.0-flash" 或 "gemini-2.5-pro"
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7,
    verbose=True
)
    @agent
    def wish_guard(self) -> Agent:
        return Agent(
            config=self.agents_config['wish_guard'],
            llm=self.gemini_llm, 
            verbose=True,
            allow_delegation=False
        )

    @agent
    def wish_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['wish_architect'],
            llm=self.gemini_llm,
            verbose=True,
            allow_delegation=False
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