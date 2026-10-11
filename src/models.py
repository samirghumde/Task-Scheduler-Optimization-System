"""
Task Scheduler Optimization System
===================================
src/models.py - Data models for Tasks and Resources
"""

import csv
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    """Represents a schedulable task with all constraints."""
    task_id: str
    duration_h: int          # Execution time in hours
    deadline_h: int          # Deadline (hours from t=0)
    priority: int            # 1 (low) to 5 (high)
    skill: str               # Required skill
    depends_on: List[str]    # List of task IDs this depends on
    profit: int              # Importance/profit score

    # Scheduled fields (filled after scheduling)
    start_h: Optional[int] = None
    end_h: Optional[int] = None
    assigned_resource: Optional[str] = None
    is_late: bool = False
    lateness_h: int = 0
    is_missed: bool = False

    def __repr__(self):
        return (f"Task({self.task_id}, prio={self.priority}, "
                f"ddl={self.deadline_h}h, dur={self.duration_h}h, profit={self.profit})")


@dataclass
class Resource:
    """Represents a worker/machine with skills and shift windows."""
    res_id: str
    skills: set
    shift_start_h: int       # Shift start (hours, repeated each day)
    shift_end_h: int         # Shift end
    max_hours_per_day: int

    # Scheduling state
    current_time_h: int = 0
    total_hours_assigned: int = 0

    def can_handle(self, skill: str) -> bool:
        return skill in self.skills

    def __repr__(self):
        return f"Resource({self.res_id}, skills={self.skills})"


def load_tasks(path: str = "data/tasks.csv") -> List[Task]:
    """Load tasks from CSV file."""
    tasks = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            deps = [d.strip() for d in (row.get("depends_on") or "").split("|") if d.strip()]
            task = Task(
                task_id=row["task_id"].strip(),
                duration_h=int(row["duration_h"]),
                deadline_h=int(row["deadline_h"]),
                priority=int(row["priority"]),
                skill=row["skill"].strip(),
                depends_on=deps,
                profit=int(row.get("profit", 100))
            )
            tasks.append(task)
    return tasks


def load_resources(path: str = "data/resources.csv") -> List[Resource]:
    """Load resources from CSV file."""
    resources = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills = set(s.strip() for s in (row["skills"] or "").split("|") if s.strip())
            res = Resource(
                res_id=row["res_id"].strip(),
                skills=skills,
                shift_start_h=int(row["shift_start_h"]),
                shift_end_h=int(row["shift_end_h"]),
                max_hours_per_day=int(row["max_hours_per_day"])
            )
            resources.append(res)
    return resources