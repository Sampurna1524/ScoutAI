from agents.job_agent import JobAgent

query = "Python AI jobs in Mumbai"

session = JobAgent.search_jobs(query)

print("\n==================== JOBS ====================\n")

for job in session.jobs:
    print(job.model_dump())
    print("-" * 80)
