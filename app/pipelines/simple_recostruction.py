from prefect import flow, task
from core.context_keeper import PMContext
from core.git_reverse_analyst import GitReverseAnalyst

@task
def load_context():
    context = PMContext()
    logs = context.get_logs()
    return context, logs

@task
def filter_commits(logs):
    return logs[logs['title'] != 'initial commit']

@task
def analyze_commits(logs, etalon_tasks):
    analyst = GitReverseAnalyst(etalon_tasks, project_title="nodis_project")
    all_tasks = []
    for tasks, _ in analyst.analyze_git_logs(logs):
        all_tasks += tasks
    return all_tasks

@task
def save_tasks(tasks):
    with open("all_predicted_tasks.txt", 'w') as f:
        for t in tasks:
            f.write(str(t) + "\n")
    return len(tasks)

@flow
def git_to_tasks_pipeline():
    context, logs = load_context()
    logs_filtered = filter_commits(logs)
    tasks = analyze_commits(logs_filtered, context.get_tasks())
    count = save_tasks(tasks)
    print(f"Pipeline completed. {count} tasks saved.")
    return tasks
