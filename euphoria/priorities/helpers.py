def calculate_average_completion_time(completed: list) -> str:
    total_days = sum(task.days_to_complete for task in completed)
    average_days = total_days / len(completed)
    weeks, days = divmod(average_days, 7)
    return f'{int(weeks)} weeks, {int(days)} days'
