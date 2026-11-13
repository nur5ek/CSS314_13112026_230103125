import argparse, ctypes, json, multiprocessing as mp
from multiprocessing import shared_memory
from harness import run_benchmark, emit_verify_tag
M=24_000_000

def fs_worker(name,slot_idx,iters):
    shm=shared_memory.SharedMemory(name=name)
    arr=(ctypes.c_uint64*512).from_buffer(shm.buf)
    acc=arr[slot_idx]; mask=0xFFFFFFFFFFFFFFFF; mult=6364136223846793005
    for i in range(iters):
        acc=(acc*mult+(i|1))&mask
        arr[slot_idx]=acc
    del arr
    shm.close()

def trial(p,stride,steps):
    if (p-1)*stride>=512: raise ValueError('Shared memory slot out of bounds; increase buffer size')
    shm=shared_memory.SharedMemory(create=True,size=4096)
    try:
        jobs=[mp.Process(target=fs_worker,args=(shm.name,t*stride,steps//p+(t<steps%p))) for t in range(p)]
        for job in jobs:job.start()
        for job in jobs:job.join()
        if any(job.exitcode!=0 for job in jobs):raise RuntimeError('A worker failed')
    finally:
        shm.close();shm.unlink()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--id',type=int,required=True);ap.add_argument('--physical',type=int,required=True);ap.add_argument('--steps',type=int,default=M);ap.add_argument('--quick',action='store_true');a=ap.parse_args()
    logical=mp.cpu_count();steps=24000 if a.quick else a.steps
    def bench(p,stride):
        s=run_benchmark(lambda:trial(p,stride,steps),0 if a.quick else 2,2 if a.quick else 7)
        return {'p':p,'stride':stride,'offset_bytes':8*stride,'median_ms':s.median_ms,'iqr_ms':s.iqr_ms,'mops':steps/s.median_ms/1000}
    strides=[1,2,4,8,16,32]
    row_a=[bench(a.physical,s) for s in strides]
    counts=sorted(set([1]+[2**i for i in range(1,logical.bit_length()) if 2**i<=logical]+[logical]))
    baseline={}
    series=[]
    for stride in [1,16]:
        for p in counts:
            r=bench(p,stride)
            if p==1:baseline[stride]=r['median_ms']
            speedup=baseline[stride]/r['median_ms'];r.update(speedup=speedup,efficiency=speedup/p,karp_flatt=(1/speedup-1/p)/(1-1/p) if p>1 else None)
            series.append(r)
    result={'student_id':a.id,'steps':steps,'quick':a.quick,'stride_sweep':row_a,'scaling':series,'verify':emit_verify_tag('PHASE1',a.id,row_a[0]['median_ms'],row_a[4]['median_ms'])}
    open('phase1.json','w').write(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':mp.freeze_support();main()
