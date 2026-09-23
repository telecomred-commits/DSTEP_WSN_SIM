"""Reproduce the v0.41 TEST002 censored RSSI/PDR calibration.

Requires numpy/scipy/pandas (see requirements-calibration.txt).  The simulator
runtime itself does not require these packages.
"""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from numpy.polynomial.hermite import hermgauss

HERE=Path(__file__).resolve().parent
RAW=HERE/'raw'


def parse_rx(path):
    rows=[]
    for line in Path(path).read_text(errors='ignore').splitlines():
        p=line.strip().split(',')
        if len(p)==9:
            try: rows.append(list(map(int,p)))
            except ValueError: pass
    return rows


def segments(rows):
    if not rows: return []
    out=[]; start=0
    for i in range(1,len(rows)):
        if rows[i][1] < rows[i-1][1]:
            out.append(rows[start:i]); start=i
    out.append(rows[start:]); return out


def load_runs():
    runs={('1m',1):np.array([r[4] for r in parse_rx(RAW/'RX_1m_R1.txt')],float)}
    old=segments(parse_rx(RAW/'RX_10_20_30m_R1_plus_mobile.txt'))
    for key,seg in zip([('10m',1),('20m',1),('30m',1)],old[:3]):
        runs[key]=np.array([r[4] for r in seg],float)
    new=segments(parse_rx(RAW/'RX_R2_R3_and_25m.txt'))
    mapping=[('1m',2),('1m',3),('10m',2),('10m',3),('20m',2),('20m',3),('30m',2),('30m',3),('25m',1),('25m',2),('25m',3)]
    for key,seg in zip(mapping,new): runs[key]=np.array([r[4] for r in seg],float)
    return runs


def fit():
    runs=load_runs(); distance={'1m':1.,'10m':10.,'20m':20.,'25m':25.,'30m':30.}
    keys=sorted([k for k in runs if k[1] in (1,2)], key=lambda k:(distance[k[0]],k[1]))
    hx,hw=hermgauss(40); hw=hw/np.sqrt(np.pi); root2=np.sqrt(2.)
    init=[]
    for k in keys:
        a=runs[k]; p=len(a)/1000.; init.append(a.mean()-(1-p)*5 if p<.95 else a.mean())
    x0=np.array(init+[np.log(4.),-91.5,np.log(.8)])
    def nll(z):
        mus=z[:len(keys)]; sigma=np.exp(z[len(keys)]); T=z[len(keys)+1]; slope=np.exp(z[len(keys)+2]); total=0.
        for i,k in enumerate(keys):
            a=runs[k]; nf=1000-len(a); mu=mus[i]; zz=(a-mu)/sigma
            total-=np.sum(-.5*zz*zz-np.log(sigma)-.5*np.log(2*np.pi)+np.log(expit(slope*(a-T))+1e-300))
            if nf:
                rr=mu+root2*sigma*hx; ps=np.sum(hw*expit(slope*(rr-T)))
                total-=nf*np.log(max(1e-12,1-ps))
        return total
    bounds=[(-120,-40)]*len(keys)+[(np.log(.2),np.log(20)),(-110,-70),(np.log(.02),np.log(5))]
    res=minimize(nll,x0,method='L-BFGS-B',bounds=bounds,options={'maxiter':3000,'ftol':1e-10})
    if not res.success: raise RuntimeError(res.message)
    z=res.x; mus=z[:len(keys)]; sigma=float(np.exp(z[len(keys)])); T=float(z[len(keys)+1]); slope=float(np.exp(z[len(keys)+2]))
    x=np.array([math.log10(distance[k[0]]) for k in keys]); X=np.c_[np.ones_like(x),x]
    beta=np.linalg.lstsq(X,mus,rcond=None)[0]; residual=mus-X@beta
    tau=float(residual.std(ddof=2))
    return {
        'fit_split':'Runs 1-2 at each distance',
        'mean_rssi_d0_dbm':float(beta[0]),
        'tx_power_reference_dbm':20.0,
        'pl_d0_db':float(20.0-beta[0]),
        'path_loss_exponent':float(-beta[1]/10.0),
        'link_shadow_sigma_db':tau,
        'fast_fading_sigma_db':sigma,
        'decoder_midpoint_dbm':T,
        'decoder_logistic_slope_per_db':slope,
        'optimizer_nll':float(res.fun),
        'optimizer_success':bool(res.success),
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--write',action='store_true'); args=ap.parse_args()
    out=fit(); text=json.dumps(out,indent=2); print(text)
    if args.write: (HERE/'calibrated_parameters_refit.json').write_text(text+'\n')

if __name__=='__main__': main()
