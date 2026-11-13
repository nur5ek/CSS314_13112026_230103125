import argparse, multiprocessing as mp, platform, sys, time, json
from harness import emit_verify_tag

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--id',type=int,required=True);parser.add_argument('--reads',type=int,default=1_000_000)
    a=parser.parse_args()
    begin=time.perf_counter_ns()
    for _ in range(a.reads): time.perf_counter_ns()
    latency=(time.perf_counter_ns()-begin)/a.reads
    result={'student_id':a.id,'cpu_count':mp.cpu_count(),'clock_reads':a.reads,'clock_latency_ns':latency,'python':sys.version.split()[0],'os':platform.platform()}
    result['verify']=emit_verify_tag('PHASE0',a.id,mp.cpu_count(),latency)
    print(json.dumps(result,indent=2));open('phase0.json','w').write(json.dumps(result,indent=2))
if __name__=='__main__':main()

