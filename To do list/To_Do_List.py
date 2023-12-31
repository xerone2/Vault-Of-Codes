import os
import json
from datetime import datetime, date
from json.decoder import JSONDecodeError
from prettytable import PrettyTable

# Function to load tasks from file
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)
def load_tasks():
    tasks = []
    if os.path.exists("tasks.json"):
        try:
            with open("tasks.json", "r") as file:
                tasks = json.load(file)
        except json.decoder.JSONDecodeError:
            # Handle the case when the file is empty or contains invalid JSON
            print("Error decoding JSON. The file may be empty or contain invalid JSON.")
    return tasks


# Function to save tasks to file
def save_tasks(tasks):
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, indent=2, cls=DateEncoder)

# Function to display tasks
def display_tasks(tasks):
    if not tasks:
        print("No tasks found.")
        return
    #Table format
    bold = "\033[1m"
    reset = "\033[0m"
    table = PrettyTable()
    table.field_names = [f"{bold}Task No.{reset}", f"{bold}Title{reset}", f"{bold}Created on{reset}", f"{bold}Due Date{reset}", f"{bold}Completed{reset}"]

    for index, task in enumerate(tasks, start=1):
        completed = "Yes" if task.get("completed") else "No"
        table.add_row([index, task["title"], task["due_date"],task["date_assigned"], completed])

    print(table)

# Function to add a task
def add_task(tasks):
    title = input("Enter task title: ")
    date_assigned = datetime.now().date()
    due_date_str = input("Enter due date (YYYY-MM-DD): ")
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None

    new_task = {"title": title, "date_assigned": date_assigned, "due_date": due_date}
    tasks.append(new_task)
    save_tasks(tasks)
    print("Task added successfully.")

# Function to delete a task
def delete_task(tasks):
    display_tasks(tasks)
    try:
        task_index = int(input("Enter the task number to delete: ")) - 1
        if 0 <= task_index < len(tasks):
            del tasks[task_index]
            save_tasks(tasks)
            print("Task deleted successfully.")
        else:
            print("Invalid task number.")
    except ValueError:
        print("Invalid input. Please enter a valid task number.")

# Function to mark a task as completed
def mark_completed(tasks):
    display_tasks(tasks)
    try:
        task_index = int(input("Enter the task number to mark as completed: ")) - 1
        if 0 <= task_index < len(tasks):
            tasks[task_index]["completed"] = True
            save_tasks(tasks)
            print("Task marked as completed.")
        else:
            print("Invalid task number.")
    except ValueError:
        print("Invalid input. Please enter a valid task number.")

# Main function
def main():
    tasks = load_tasks()

    while True:
        print("\nMenu:")
        print("1. Display Tasks")
        print("2. Add Task")
        print("3. Delete Task")
        print("4. Mark Task as Completed")
        print("5. Quit")

        choice = input("Enter your choice (1-5): ")

        if choice == "1":
            display_tasks(tasks)
        elif choice == "2":
            add_task(tasks)
        elif choice == "3":
            delete_task(tasks)
        elif choice == "4":
            mark_completed(tasks)
        elif choice == "5":
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()
