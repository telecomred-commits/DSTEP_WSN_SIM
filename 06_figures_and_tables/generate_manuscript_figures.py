from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
DATA=HERE/'source_data'
OUT=HERE/'regenerated_figures'
OUT.mkdir(exist_ok=True)
labels={'send_on_delta':'Send-on-Delta','voi_baseline':'VoI baseline','dstep':'D-STEP baseline','dstep_payoff':'PA-DSTEP'}

# Figures 1 and 2
v=pd.read_csv(DATA/'fig1_fig2_holdout_validation.csv')
x=v.distance_m
fig,ax=plt.subplots(figsize=(7,4.5))
ax.plot(x,v.observed_data_pdr,marker='o',label='Held-out hardware Run 3')
ax.plot(x,v.predictive_pdr_median,marker='s',linestyle='--',label='Simulator predictive median')
ax.fill_between(x,v.predictive_pdr_2p5,v.predictive_pdr_97p5,alpha=.2,label='95% predictive interval')
ax.set(xlabel='Distance (m)',ylabel='DATA PDR',ylim=(0,1.05)); ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'Fig1.png',dpi=300); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4.5))
ax.plot(x,v.observed_success_rssi_mean_dbm,marker='o',label='Held-out hardware Run 3')
ax.plot(x,v.predictive_success_rssi_median_dbm,marker='s',linestyle='--',label='Simulator predictive median')
ax.fill_between(x,v.predictive_success_rssi_2p5_dbm,v.predictive_success_rssi_97p5_dbm,alpha=.2,label='95% predictive interval')
ax.set(xlabel='Distance (m)',ylabel='Successful-packet RSSI (dBm)'); ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'Fig2.png',dpi=300); plt.close(fig)

def lineplot(csv,ycol,ylabel,name):
    d=pd.read_csv(DATA/csv)
    fig,ax=plt.subplots(figsize=(7,4.5))
    styles={'send_on_delta':('s','-'),'voi_baseline':('o','--'),'dstep':('^','-'),'dstep_payoff':('D','-')}
    for p,g in d.groupby('policy',sort=False):
        m,ls=styles.get(p,('o','-'))
        ax.plot(g.nodes,g[ycol],marker=m,linestyle=ls,label=labels.get(p,p))
    ax.set(xlabel='Nodes',ylabel=ylabel); ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/name,dpi=300); plt.close(fig)

lineplot('fig3_deterministic_energy.csv','energy_mj_mean','Modeled energy (mJ)','Fig3.png')
lineplot('fig4_physical_pulse_dcr.csv','dcr_mean','Deadline compliance ratio','Fig4.png')
lineplot('fig5_physical_pulse_f1.csv','confirmation_f1_mean','Policy-decision F1','Fig5.png')
lineplot('fig6_absent_false_alarm.csv','network_false_alarm_mean','Network false-alarm incidence','Fig6.png')

d=pd.read_csv(DATA/'fig7_relative_energy_reduction.csv')
fig,ax=plt.subplots(figsize=(7,4.5))
for ev,g in d.groupby('event_model',sort=False):
    ax.plot(g.nodes,g.relative_energy_reduction_pct,marker='o',label=ev.replace('_',' '))
ax.set(xlabel='Nodes',ylabel='Modeled-energy reduction vs D-STEP (%)'); ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'Fig7.png',dpi=300); plt.close(fig)
print(f'Wrote 7 figures to {OUT}')
