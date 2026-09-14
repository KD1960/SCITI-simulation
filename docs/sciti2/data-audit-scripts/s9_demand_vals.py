import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
pd.set_option('display.width',250); pd.set_option('display.max_columns',60); pd.set_option('display.max_rows',100)
X="/Users/kevindooley/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"
raw=pd.read_excel(X,sheet_name="Demand_Retailer",header=None)
print("summary cells AE5:BB6, AE8:AE11 cached:"); print(raw.iloc[4:6,30:54].round(1).to_string()); print(raw.iloc[7:11,29:31])
d=raw.iloc[4:264,:27].copy(); d.columns=['Year','Wk','QTR']+[f'R{r}{p}' for r in range(1,9) for p in 'ABC']
for c in d.columns:
    if c!='QTR': d[c]=pd.to_numeric(d[c])
print("years", d.Year.value_counts().sort_index().to_dict(), "weeks", d.Wk.min(), d.Wk.max())
print("QTR by week mapping:", d.groupby('QTR')['Wk'].agg(['min','max','count']).to_dict())
print("non-integer values:", {c:int((d[c]%1!=0).sum()) for c in d.columns[3:] if (d[c]%1!=0).any()})
ann=d.groupby('Year')[d.columns[3:]].sum()
print(ann.round(0).T)
doc={1:(129239,89268,64354),2:(64620,44634,32177),3:(90467,62488,45048),4:(25848,17854,12871),5:(71414,71414,71414),6:(12924,8927,6435),7:(51483,32177,25742),8:(116315,80341,57919)}
print("2024 vs doc Table 5:")
for r,v in doc.items():
    print(r,[ (round(ann.loc[2024,f'R{r}{p}']), v[i], round(ann.loc[2024,f'R{r}{p}']/v[i],4)) for i,p in enumerate('ABC')])
print("growth yoy R1:"); g=ann[['R1A','R1B','R1C']].pct_change().round(3); print(g)
# log-linear annual growth fit on weekly
t=np.arange(len(d))/52
for c in ['R1A','R1B','R1C']:
    b=np.polyfit(t,np.log(d[c]),1)[0]; print(c,"loglinear growth/yr", round(np.exp(b)-1,4))
print("R1 A==C rows:", (d.R1A==d.R1C).sum(), "of", len(d))
print((d[['R1A','R1C']].head(10)).T)
# where do A and C differ?
diff=d[d.R1A!=d.R1C]; print("first differing rows", diff[['Year','Wk','R1A','R1C']].head())
# SD by retailer, weekly, per year and overall
sd=d.groupby('Year')[d.columns[3:]].std(); print("weekly SD by year:"); print(sd.round(0).T)
# ratios check scale factors (actual cached)
for r,(fa,fb,fc) in {2:(.5,.5,.5),3:(.7,.7,.7),4:(.2,.2,.2),5:(.8,.8,.8),6:(.1,.1,.1),7:(.8,.5,.4),8:(.9,.9,.9)}.items():
    print(r, "ratio to R1 A,B,C:", round((d[f'R{r}A']/d.R1A).mean(),3), round((d[f'R{r}B']/d.R1B).mean(),3), round((d[f'R{r}C']/d.R1C).mean(),3))
# seasonality: mean index by week-of-quarter (1..13) and by week
d['wq']=((d.Wk-1)%13)+1
tot=d[[f'R{r}{p}' for r in range(1,9) for p in 'ABC']].sum(axis=1)
# detrend by year mean
idx=tot/tot.groupby(d.Year).transform('mean')
print("season index by week-of-quarter:", idx.groupby(d.wq).mean().round(3).to_dict())
for p in 'ABC':
    s=d[f'R1{p}']/d[f'R1{p}'].groupby(d.Year).transform('mean')
    print(p,"R1 by week-of-quarter", s.groupby(d.wq).mean().round(3).to_dict())
    print(p,"R1 by quarter", s.groupby(d.QTR).mean().round(3).to_dict())
    top=s.groupby(d.Wk).mean().sort_values(ascending=False).head(6).round(3).to_dict(); print("  top weeks", top)
# min values / zeros
print("min demand per series:", d[d.columns[3:27]].min().to_dict())
d.to_pickle('demand.pkl')
