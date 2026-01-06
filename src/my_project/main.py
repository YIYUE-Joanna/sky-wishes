import sys
from my_project.crew import MyProjectCrew

def run():
    print("--- 欢迎来到天灯广场 ---")
    user_wish = input("请输入你的新年愿望: ")
    
    inputs = {
        'wish': user_wish
    }
    
    # 启动 Crew
    result = MyProjectCrew().crew().kickoff(inputs=inputs)
    
    # 打印最终生成的 JSON (供前端渲染)
    print("\n--- 架构师生成的方案 (JSON) ---")
    print(result.raw) 

if __name__ == "__main__":
    run()