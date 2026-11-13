from dataclasses import dataclass
import multiprocessing as mp
import time
from statistics import median

@dataclass
class BenchStats:
    min_ms: float
    median_ms: float
    iqr_ms: float
    max_ms: float

def fnv1a_hash(s: str) -> int:
    h = 14695981039346656037
    for b in s.encode('utf-8'):
        h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h

def run_benchmark(fn, warmup_runs=3, timed_runs=9):
    for _ in range(warmup_runs): fn()
    samples=[]
    for _ in range(timed_runs):
        start=time.perf_counter_ns(); fn()
        samples.append((time.perf_counter_ns()-start)/1e6)
    samples.sort(); n=len(samples)
    return BenchStats(samples[0],median(samples),samples[(3*n)//4]-samples[n//4],samples[-1])

def emit_verify_tag(task_id, student_seed, primary_metric, secondary_metric):
    hw=mp.cpu_count()
    payload=f'{task_id}|{student_seed}|{hw}|{primary_metric:.4f}|{secondary_metric:.4f}'
    return f'VERIFY_HASH[{task_id}]: {fnv1a_hash(payload):016X} (P_log={hw})'
