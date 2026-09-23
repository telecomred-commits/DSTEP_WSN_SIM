import argparse, copy, csv, json, os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from wsn_sim.simulator import Simulator
from wsn_sim.metrics.collector import summarize

ROOT = Path(__file__).parent
BASE = json.loads((ROOT / 'config.json').read_text())
OUT = ROOT / 'results_v050_final_campaign'
OUT.mkdir(exist_ok=True)

POLICIES = ['periodic','event_driven','send_on_delta','teen_like','distributed_edge','voi_baseline','dstep','dstep_payoff']
EVENTS = ['deterministic','physical_pulse','absent']
NODES = [20,50,100]
BASE_SEED = 6_000_000


def worker(task):
    event_model, n, policy, run, seed = task
    cfg = copy.deepcopy(BASE)
    cfg['event']['model'] = event_model
    sim = Simulator(cfg, n, policy, seed)
    sim.run()
    m = summarize(sim)
    m.update({'event_model': event_model, 'run': run, 'seed': seed})
    return m


def write_csv(path, rows):
    keys, seen = [], set()
    for row in rows:
        for k in row:
            if k not in seen:
                seen.add(k); keys.append(k)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, required=True)
    ap.add_argument('--stop', type=int, required=True)
    ap.add_argument('--workers', type=int, default=min(8, os.cpu_count() or 1))
    args = ap.parse_args()
    tasks = []
    for event_i, event_model in enumerate(EVENTS):
        for n in NODES:
            for run in range(args.start, args.stop):
                # Same event/N/run seed for every policy: paired comparison.
                seed = BASE_SEED + event_i*100_000 + n*1_000 + run
                for policy in POLICIES:
                    tasks.append((event_model, n, policy, run, seed))
    with ProcessPoolExecutor(max_workers=max(1,args.workers)) as ex:
        rows = list(ex.map(worker, tasks, chunksize=1))
    path = OUT / f'final_raw_{args.start:02d}_{args.stop-1:02d}.csv'
    write_csv(path, rows)
    print(path)
    print(f'rows={len(rows)}')

if __name__ == '__main__':
    main()
