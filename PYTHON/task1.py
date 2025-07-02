import pandas as pd

data = {
    'Planning': ['Planning', 'Define Project Scope', 'Set objectives and goals', 'resource planning', ''],
    'Defining Requirements': ['Defining', 'functional requirements', 'technical requirements', 'Requirements reviewed and approved', ''],
    'Designing': ['Design', 'Low-level Design', 'High-level Design', '', ''],
    'Development': ['Development', 'coding standard', 'scalable coding', 'version control', 'code review'],
    'Testing': ['Unit testing', 'Manual Testing', 'Automated Testing', '', ''],
    'Deployment and Maintainence': ['Deployment and Maintainence', 'Release planning', 'Deployment Automation', 'Maintainence', 'Feedback']
}

df = pd.DataFrame(data)

while True:
    print("\nEnter the stage number (1–6) or type 'exit' to quit:")
    user_input = input().strip().lower()

    if user_input == 'exit':
        print("Exiting...")
        break
    elif user_input in ['1', 'one']:
        print("\nThe first stage is Planning:")
        for i, value in enumerate(df['Planning'], start=1):
            if value.strip():
                print(f"{i}. {value}")
    elif user_input in ['2', 'two']:
        print("\nThe second stage is Defining Requirements:")
        for i, value in enumerate(df['Defining Requirements'], start=1):
            if value.strip():
                print(f"{i}. {value}")
    elif user_input in ['3', 'three']:
        print("\nThe third stage is Designing:")
        for i, value in enumerate(df['Designing'], start=1):
            if value.strip():
                print(f"{i}. {value}")
    elif user_input in ['4', 'four']:
        print("\nThe fourth stage is Development:")
        for i, value in enumerate(df['Development'], start=1):
            if value.strip():
                print(f"{i}. {value}")
    elif user_input in ['5', 'five']:
        print("\nThe fifth stage is Testing:")
        for i, value in enumerate(df['Testing'], start=1):
            if value.strip():
                print(f"{i}. {value}")
    elif user_input in ['6', 'six']:
        print("\nThe sixth stage is Deployment and Maintenance:")
        for i, value in enumerate(df['Deployment and Maintainence'], start=1):
            if value.strip():
                print(f"{i}. {value}")
    else:
        print("❌ Invalid input, try again!")
