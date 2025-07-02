import pandas as pd

data = {
    'Planning': ['Planning', 'Define Project Scope', 'Set objectives and goals', 'resource planning', ''],
    'Defining Requirements': ['Defining', 'functional requirements', 'technical requirements', 'Requirements reviewed and approved', ''],
    'Designing': ['Design', 'Low-level Design', 'High-level Design', '', ''],
    'Development': ['Development', 'coding standard', 'scalable coding', 'version control', 'code review'],
    'Testing': ['Unit testing', 'Manual Testing', 'Automated Testing', '', ''],
    'Deployment and Maintainence': ['Deployment and Maintainence', 'Release planEXITning', 'Deployment Automation', 'Maintainence', 'Feedback']
}

df = pd.DataFrame(data)

def display_stage(stage_name):
    print(f"\nThe stage is {stage_name}:")
    for i, value in enumerate(df[stage_name], start=1):
        if value.strip():
            print(f"{i}. {value}")

while True:
    print("\nEnter the stage number (1–6) or type 'exit' to quit:")
    user_input = input().strip().lower()

    if user_input == 'exit':
        print("Exiting...")
        break

    match user_input:
        case '1' | 'one':
            display_stage('Planning')
        case '2' | 'two':
            display_stage('Defining Requirements')
        case '3' | 'three':
            display_stage('Designing')
        case '4' | 'four':
            display_stage('Development')
        case '5' | 'five':
            display_stage('Testing')
        case '6' | 'six':
            display_stage('Deployment and Maintainence')
        case _:
            print("❌ Invalid input, try again!")
