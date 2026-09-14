import pandas as pd, numpy as np
rng=np.random.default_rng(0)
def fstat(groups):
    allv=np.concatenate(groups); gm=allv.mean(); k=len(groups); n=len(allv)
    ssb=sum(len(g)*(g.mean()-gm)**2 for g in groups); ssw=sum(((g-g.mean())**2).sum() for g in groups)
    return (ssb/(k-1))/(ssw/(n-k))
def perm_anova(vals, labels, B=5000):
    labs=np.asarray(labels); v=np.asarray(vals,float); u=np.unique(labs)
    f0=fstat([v[labs==x] for x in u]); c=0
    for _ in range(B):
        p=rng.permutation(labs); c+= fstat([v[p==x] for x in u])>=f0
    return f0,(c+1)/(B+1)
def chi2(ct):
    o=ct.values.astype(float); e=o.sum(1,keepdims=True)*o.sum(0,keepdims=True)/o.sum(); return ((o-e)**2/e).sum()
def perm_chi2(a,b,B=5000):
    a=np.asarray(a); b=np.asarray(b); x0=chi2(pd.crosstab(a,b)); c=0
    for _ in range(B):
        c+= chi2(pd.crosstab(a,rng.permutation(b)))>=x0
    return x0,(c+1)/(B+1)
tx=pd.read_pickle('tx.pkl'); par=pd.read_pickle('par.pkl')
nom=dict(zip(par['Suppliers'],par['Lead Time.1'])); pr=dict(zip(par['Suppliers'],par['Price/Unit']))
tx['dev']=tx['Lead Time']-tx['Supplier'].map(nom); tx['pdev']=tx['Unit Price']-tx['Supplier'].map(pr)
g=tx.groupby('Supplier').agg(n=('dev','size'),mean_dev=('dev','mean'),sd=('dev','std'),late_share=('dev',lambda s:(s>0).mean()),late2=('dev',lambda s:(s>=3).mean()),price_dev=('pdev','mean'))
g['t']=g.mean_dev/(g.sd/np.sqrt(g.n)); print(g.round(3))
print("perm ANOVA lead deviation across suppliers (F,p)=", perm_anova(tx["dev"],tx["Supplier"],2000))
ct=pd.crosstab(tx['Supplier'],tx['Sentiment Score']); print(ct); print("perm chi2 supplier x sentiment (chi2,p)=",perm_chi2(tx["Supplier"],tx["Sentiment Score"],1000))
geo=pd.read_excel("/Users/kevindooley/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx",sheet_name="Supplier Data",nrows=500,usecols="C",keep_default_na=False).iloc[:,0]
print("perm chi2 supplier x geography (chi2,p)=", perm_chi2(tx["Supplier"],geo,1000))
print("Lead time <=0 rows:", tx.loc[tx['Lead Time']<=0, ['Sales Order','Supplier','Lead Time']].assign(row=lambda d:d.index+2).to_dict('records'))
# implied supply vs requirement
D=1285372.4
units={'SR_MCU':10,'SR_MOS_KIT':10,'AL_Sheet':5,'HSS_Coil':5,'PP_Resin':15,'Poly_F_EU':15,'EPDM':40,'NR_201':40,'LGS_4_W':10,'TGP_5_Q':10}
s=tx.groupby('Product Name')['Order Qty'].agg(['size','sum']); s['need2024']=[D*units[k] for k in s.index]; s['ratio']=s['sum']/s['need2024']; print(s.round(3))
# ship lead bias from using great-circle instead of data distance
for n in ['cm_mfg','mfg_dc','dc_retail']:
    b=pd.read_pickle(f'ship2_{n}.pkl')
    for m in ['Ship','Air']:
        x=b[b.Mode==m]; bb,aa=np.polyfit(x['Distance (Miles)'],x['Lead Time (days)'],1)
        pred=(aa+bb*x['gc']).mean(); print(n,m,"data mean lead",round(x['Lead Time (days)'].mean(),2),"pred at gc",round(pred,2),"ratio",round(pred/x['Lead Time (days)'].mean(),3), "mean dist/gc", round((x['Distance (Miles)']/x['gc']).mean(),3))
