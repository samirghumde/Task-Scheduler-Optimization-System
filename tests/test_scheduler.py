"""
Task Scheduler Optimization System
====================================
tests/test_schedulers.py - Unit Tests

Run: python -m pytest tests/ -v
or:  python tests/test_schedulers.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Task, Resource
from src.greedy_scheduler import GreedyScheduler
from src.priority_scheduler import PriorityQueueScheduler
from src.dp_scheduler import DPScheduler


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_tasks():
    return [
        Task('T1', 4, 24, 3, 'backend',  [],       300),
        Task('T2', 6, 32, 2, 'frontend', ['T1'],   200),
        Task('T3', 2, 20, 5, 'qa',       ['T1'],   500),
        Task('T4', 8, 40, 1, 'backend',  [],       100),
        Task('T5', 3, 28, 4, 'frontend', [],       400),
    ]

def make_resources():
    return [
        Resource('R1', {'backend', 'qa'},       0, 8, 8),
        Resource('R2', {'frontend', 'qa'},      0, 8, 8),
        Resource('R3', {'backend', 'frontend'}, 0, 8, 8),
    ]


# ─── Dependency Tests ─────────────────────────────────────────────────────────

def assert_dependencies_respected(results):
    end_times = {}
    for t in results:
        if not t.is_missed:
            end_times[t.task_id] = t.end_h

    for t in results:
        if not t.is_missed:
            for dep in t.depends_on:
                dep_end = end_times.get(dep, 0)
                assert t.start_h >= dep_end, \
                    f"FAIL: {t.task_id} starts at {t.start_h} but dep {dep} ends at {dep_end}"
    print("  ✓ Dependency ordering respected")


def assert_skills_matched(results, resources):
    skill_map = {r.res_id: r.skills for r in resources}
    for t in results:
        if not t.is_missed:
            assert t.skill in skill_map[t.assigned_resource], \
                f"FAIL: {t.task_id} skill '{t.skill}' not in {skill_map[t.assigned_resource]} for {t.assigned_resource}"
    print("  ✓ Skill constraints satisfied")


def assert_no_overlap(results):
    from collections import defaultdict
    res_intervals = defaultdict(list)
    for t in results:
        if not t.is_missed:
            res_intervals[t.assigned_resource].append((t.start_h, t.end_h, t.task_id))

    for rid, intervals in res_intervals.items():
        intervals.sort()
        for i in range(len(intervals) - 1):
            _, e1, t1 = intervals[i]
            s2, _, t2 = intervals[i+1]
            assert e1 <= s2, f"FAIL: Overlap on {rid}: {t1} ends at {e1}, {t2} starts at {s2}"
    print("  ✓ No resource overlaps")


def assert_lateness_correct(results):
    for t in results:
        if not t.is_missed:
            expected = max(0, t.end_h - t.deadline_h)
            assert t.lateness_h == expected, \
                f"FAIL: {t.task_id} lateness should be {expected}, got {t.lateness_h}"
    print("  ✓ Lateness calculations correct")


# ─── Test Cases ───────────────────────────────────────────────────────────────

def test_greedy():
    print("\n[TEST] Greedy Scheduler")
    tasks = make_tasks()
    resources = make_resources()
    s = GreedyScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    results = summary['tasks']
    assert_dependencies_respected(results)
    assert_skills_matched(results, resources)
    assert_no_overlap(results)
    assert_lateness_correct(results)
    assert summary['total_tasks'] == 5
    print(f"  ✓ Greedy: {summary['on_time_count']}/{summary['total_tasks']} on-time, profit={summary['total_profit']}")


def test_priority_queue():
    print("\n[TEST] Priority Queue Scheduler")
    tasks = make_tasks()
    resources = make_resources()
    s = PriorityQueueScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    results = summary['tasks']
    assert_dependencies_respected(results)
    assert_skills_matched(results, resources)
    assert_no_overlap(results)
    assert_lateness_correct(results)
    assert summary['total_tasks'] == 5
    print(f"  ✓ PQ: {summary['on_time_count']}/{summary['total_tasks']} on-time, profit={summary['total_profit']}")


def test_dp():
    print("\n[TEST] Dynamic Programming Scheduler")
    tasks = make_tasks()
    resources = make_resources()
    s = DPScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    results = summary['tasks']
    assert_skills_matched(results, resources)
    assert_lateness_correct(results)
    assert summary['total_tasks'] == 5
    print(f"  ✓ DP: {summary['on_time_count']}/{summary['total_tasks']} on-time, profit={summary['total_profit']}")


def test_empty_tasks():
    print("\n[TEST] Empty task list")
    resources = make_resources()
    s = GreedyScheduler([], resources, horizon=72)
    summary = s.get_summary()
    assert summary['total_tasks'] == 0
    print("  ✓ Empty task list handled correctly")


def test_single_task():
    print("\n[TEST] Single task")
    tasks = [Task('T1', 3, 24, 5, 'backend', [], 500)]
    resources = make_resources()
    s = GreedyScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    assert summary['scheduled_count'] == 1
    assert summary['total_profit'] == 500
    print("  ✓ Single task scheduled correctly")


def test_impossible_task():
    print("\n[TEST] Task with no compatible resource")
    tasks = [Task('T1', 3, 24, 5, 'devops', [], 500)]  # no devops resource
    resources = make_resources()
    s = GreedyScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    # Should be missed since no resource has 'devops'
    assert summary['missed_count'] == 1 or summary['scheduled_count'] == 0
    print("  ✓ Incompatible skill handled (task missed)")


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  TASK SCHEDULER TEST SUITE")
    print("="*50)
    tests = [test_greedy, test_priority_queue, test_dp,
             test_empty_tasks, test_single_task, test_impossible_task]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
    print(f"\n  {'='*50}")
    print(f"  Results: {passed}/{len(tests)} tests passed")
    print("="*50 + "\n")