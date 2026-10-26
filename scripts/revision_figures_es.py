"""Scientific manuscript figures generated from saved numeric evidence."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'docs/q1_artifacts'
OUT=ART/'revision_20261026/figures_es'


def save(fig,name):
    fig.savefig(OUT/f'{name}.png',dpi=300,bbox_inches='tight',facecolor='white')
    fig.savefig(OUT/f'{name}.svg',bbox_inches='tight',facecolor='white')
    plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
                         'axes.spines.right':False,'savefig.dpi':300})
    external=pd.read_csv(ART/'bushland/field_season_predictions.csv')
    pairs=pd.read_csv(ART/'bushland/state_observation_pairs.csv')
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.1))
    for year,marker,color in [(2016,'o','#246a73'),(2018,'s','#b66a35')]:
        y=external[external.year==year]
        axes[0].scatter(y.dry_grain_observed/1000,y.calibrated_coupled_process/1000,label=str(year),marker=marker,color=color)
        b=pairs[(pairs.year==year)&(pairs.endpoint=='biomass_kg_ha')]
        axes[1].scatter(b.observed/1000,b.predicted/1000,marker=marker,color=color,s=18,alpha=.75)
    for ax,title,upper in zip(axes,['(a) Grano seco: 8 parcela-campañas','(b) Biomasa: 49 parcela-días'],[16,32]):
        ax.plot([0,upper],[0,upper],color='#777777',ls='--',lw=1)
        ax.set(xlim=(0,upper),ylim=(0,upper),xlabel='Observado (t/ha)',ylabel='Predicho (t/ha)',title=title)
    axes[0].legend(frameon=False,fontsize=8);fig.tight_layout();save(fig,'figure7_external_states')
    fig,ax=plt.subplots(figsize=(6.7,3.6));ax.set(xlim=(0,10),ylim=(0,6));ax.axis('off')
    boxes=[(.2,4.1,4.1,1.2,'22 160 registros de rendimiento\n36 medianas nacionales anuales'),
           (5.2,4.1,4.5,1.2,'Resúmenes y plantillas climáticas\nTres copias de escenario por año\nUn rendimiento anual compartido'),
           (2.3,2.15,5.5,1.1,'108 filas escenario-año; 36 años independientes\nCada año pertenece a una sola partición'),
           (.1,.1,4.8,1.1,'Partición original: 28 años de ajuste\ny 8 de prueba; interpolación histórica'),
           (5.1,.1,4.8,1.1,'Nueva auditoría: 5 bloques temporales\n20 años de prueba: 2006-2025')]
    for x,y,w,h,t in boxes:
        ax.add_patch(Rectangle((x,y),w,h,facecolor='#f3f5f5',edgecolor='#4c5b61',lw=1))
        ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=7.5)
    for start,end in [((2.3,4.1),(4,3.25)),((7.4,4.1),(6.2,3.25)),((4,2.15),(2.5,1.2)),((6,2.15),(7.5,1.2))]:
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=12,color='#4c5b61'))
    save(fig,'figure1_lineage')

    d=pd.read_csv(ART/'hindcast_independent_years.csv')
    fig,ax=plt.subplots(figsize=(5.7,3.7));y=d.observed_kg_ha;p=d.predicted_kg_ha
    ax.scatter(y,p,c='#246a73',s=38)
    bounds=[min(y.min(),p.min())-300,max(y.max(),p.max())+300]
    ax.plot(bounds,bounds,ls='--',color='#777',lw=1)
    for _,r in d.iterrows():ax.annotate(str(int(r.year)),(r.observed_kg_ha,r.predicted_kg_ha),xytext=(4,4),textcoords='offset points',fontsize=7)
    ax.set(xlabel='Rendimiento observado (kg/ha)',ylabel='Rendimiento predicho (kg/ha)',xlim=bounds,ylim=bounds)
    ax.grid(alpha=.16);fig.tight_layout();save(fig,'figure2_hindcast')

    d=pd.read_csv(ART/'extended/multiseed_neural_results.csv')
    fig,ax=plt.subplots(figsize=(5.7,3.1))
    for pos,(name,g) in enumerate(d.groupby('model',sort=False)):
        vals=g.rmse_kg_ha.to_numpy();ax.scatter(np.full(len(vals),pos)+np.linspace(-.1,.1,len(vals)),vals,color=['#246a73','#a85d34'][pos],s=25)
        ax.errorbar(pos,vals.mean(),yerr=vals.std(ddof=1),fmt='k_',capsize=7,ms=18)
    ax.set(xticks=[0,1],xticklabels=['Regularizada por monotonicidad','MLP sin regularización'],ylabel='RMSE (kg/ha)')
    ax.grid(axis='y',alpha=.16);fig.tight_layout();save(fig,'figure3_multiseed')

    water=pd.read_excel(ROOT/'output/cerespinn_reporte_balance_hidrico.xlsx')
    bio=pd.read_excel(ROOT/'output/cerespinn_reporte_biomasa_lai.xlsx')
    fig,axes=plt.subplots(2,1,figsize=(6.4,5.3),sharex=True)
    ax=axes[0];ax.plot(water.iloc[:,0],water.iloc[:,3],label='ET de referencia',color='#8b5837',lw=1)
    ax.bar(water.iloc[:,0],water.iloc[:,1],label='Precipitación',color='#6994bb',width=.8)
    ax.step(water.iloc[:,0],water.iloc[:,2],label='Riego',color='#246a73',lw=1.4)
    ax.set(ylabel='Flujo de agua (mm/día)');ax.legend(frameon=False,ncol=3,fontsize=8);ax.text(.01,.84,'(a)',transform=ax.transAxes)
    ax=axes[1];ax.plot(bio.iloc[:,0],bio.iloc[:,1],color='#246a73',label='Biomasa',lw=1.5)
    right=ax.twinx();right.plot(bio.iloc[:,0],bio.iloc[:,2],color='#8b5837',ls='--',label='LAI',lw=1.4)
    ax.set(xlabel='Días después de la siembra',ylabel='Biomasa (kg/ha)');right.set_ylabel('Índice de área foliar (m²/m²)')
    ax.text(.01,.84,'(b)',transform=ax.transAxes);ax.grid(alpha=.16);fig.tight_layout();save(fig,'figure4_daily_demonstration')

    oof=pd.read_csv(ART/'revision_20261026/rolling_origin_predictions.csv')
    fig,ax=plt.subplots(figsize=(6.5,3.5))
    for col,label,color in [('observed','Observado','#222'),('ridge_all','Ridge','#246a73'),
                            ('monotonic_all','Red regularizada','#a85d34'),
                            ('detrended_monotonic_climate','Red climática sin tendencia','#6e6986')]:
        ax.plot(oof.year,oof[col],label=label,lw=1.35,marker='o' if col=='observed' else None,ms=3,color=color)
    for yr in [2010,2014,2018,2022]:ax.axvline(yr-.5,color='#999',lw=.5,ls=':')
    ax.set(xlabel='Año futuro de prueba',ylabel='Rendimiento anual (kg/ha)');ax.legend(frameon=False,fontsize=7.8,ncol=2)
    ax.grid(alpha=.15);fig.tight_layout();save(fig,'figure5_rolling_origin')

    corr=pd.read_csv(ART/'revision_20261026/correlations_initial_training_only.csv',index_col=0)
    labels=['Año','Temperatura','Anomalía de precip.','CO₂','Riesgo de calor','Lluvia estacional']
    corr=corr.iloc[:6,:6]
    fig,ax=plt.subplots(figsize=(6.1,4.1));im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r')
    ax.set(xticks=range(6),yticks=range(6),xticklabels=labels,yticklabels=labels)
    plt.setp(ax.get_xticklabels(),rotation=35,ha='right',fontsize=8)
    for i in range(6):
        for j in range(6):ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',fontsize=8,color='white' if abs(corr.iloc[i,j])>.6 else 'black')
    fig.colorbar(im,ax=ax,shrink=.75,label='Correlación de Pearson');fig.tight_layout();save(fig,'figure6_confounding')
    print('Seven figures generated from frozen evidence')


if __name__=='__main__':main()
