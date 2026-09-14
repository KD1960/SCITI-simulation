import pandas as pd, numpy as np, math
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',400)
B={n:pd.read_pickle(f'ship_{n}.pkl') for n in ['cm_mfg','mfg_dc','dc_retail']}
X="/Users/kevindooley/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"
import openpyxl
ws=openpyxl.load_workbook(X,read_only=True)["Shipment_CM_MFG_DC_Retailers"]
print("A503:", next(ws.iter_rows(min_row=503,max_row=503,values_only=True))[:3])
B['cm_mfg']=B['cm_mfg'][B['cm_mfg']['Mode'].notna()]
F={"Air":2.1,"Road":0.163,"Rail":0.028,"Ship":0.037}
COORD={"Taipei, Taiwan":(25.03,121.57),"Bangalore, India":(12.97,77.59),"Guadalajara, Mexico":(20.67,-103.35),"Munich, Germany":(48.14,11.58),
"Los Angeles, CA":(34.05,-118.24),"Shenzhen, China":(22.54,114.06),"Houston, TX":(29.76,-95.37),"Dubai, UAE":(25.20,55.27),"Shanghai, China":(31.23,121.47),"Sofia, Bulgaria":(42.70,23.32),
"Columbus, OH":(39.96,-83.0),"Sao Paulo, Brazil":(-23.55,-46.63),"Barcelona, Spain":(41.39,2.17),"Nairobi, Kenya":(-1.29,36.82),"Mumbai, India":(19.08,72.88),"Singapore":(1.35,103.82),"Tokyo, Japan":(35.68,139.69),"Melbourne, Australia":(-37.81,144.96)}
def gc(a,b):
    (la1,lo1),(la2,lo2)=COORD[a],COORD[b]
    p1,p2=math.radians(la1),math.radians(la2); dp=p2-p1; dl=math.radians(lo2-lo1)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 3958.8*2*math.asin(math.sqrt(x))
spec={'cm_mfg':('Component Manufacturer','Location','Manufacturer','MFG_Location'),
      'mfg_dc':('MFG','MFG_Location','Dist_Center','Dist_Location'),
      'dc_retail':('Dist_Center','DC_Location','Retailer','Retail_Location')}
for n,b in B.items():
    o,ol,d,dl=spec[n]
    for c in ['Distance (Miles)','Lead Time (days)','Quantity','Shipping Cost/Unit','Total_Cost','CO2 Emissions (kg)']:
        b[c]=pd.to_numeric(b[c])
    print("\n\n########",n,len(b))
    print("IDs unique:",b.iloc[:,0].nunique(), "dates:",b.iloc[:,1].min(),b.iloc[:,1].max(), "years", pd.to_datetime(b.iloc[:,1]).dt.year.value_counts().to_dict())
    print("origin ids->loc:", b.groupby([o,ol]).size().to_dict())
    print("dest ids->loc:", b.groupby([d,dl]).size().to_dict())
    print("Product types:", b.iloc[:,6].value_counts().to_dict())
    print("Mode mix:", (b['Mode'].value_counts(normalize=True).round(3)).to_dict(), b['Mode'].value_counts().to_dict())
    print(pd.crosstab([b[ol]],b[dl],margins=True))
    ct=pd.crosstab([b[ol],b[dl]],b['Mode'],margins=True); print(ct)
    b['gc']=[gc(x,y) for x,y in zip(b[ol],b[dl])]
    g=b.groupby([ol,dl,'Mode']).agg(n=('Mode','size'),dmin=('Distance (Miles)','min'),dmax=('Distance (Miles)','max'),gc=('gc','first'),lt_mean=('Lead Time (days)','mean'),lt_min=('Lead Time (days)','min'),lt_max=('Lead Time (days)','max'),c_min=('Shipping Cost/Unit','min'),c_max=('Shipping Cost/Unit','max'),c_mean=('Shipping Cost/Unit','mean'),q_mean=('Quantity','mean'))
    print(g.round(2))
    gm=b.groupby('Mode').agg(n=('Mode','size'),dmin=('Distance (Miles)','min'),dmax=('Distance (Miles)','max'),lt_mean=('Lead Time (days)','mean'),lt_min=('Lead Time (days)','min'),lt_max=('Lead Time (days)','max'),c_min=('Shipping Cost/Unit','min'),c_max=('Shipping Cost/Unit','max'),c_mean=('Shipping Cost/Unit','mean'))
    print(gm.round(2))
    for m,gg in b.groupby('Mode'):
        if len(gg)>2:
            sl=np.polyfit(gg['Distance (Miles)'],gg['Lead Time (days)'],1)[0]; cs=np.polyfit(gg['Distance (Miles)'],gg['Shipping Cost/Unit'],1)[0]
            r=np.corrcoef(gg['Distance (Miles)'],gg['Lead Time (days)'])[0,1]
            print(f"  {m}: lead slope {sl:.5f}/mile r={r:.3f}; cost slope {cs:.6f}/mile")
    print("cost/unit overall range", b['Shipping Cost/Unit'].min(), b['Shipping Cost/Unit'].max())
    # distance vs great-circle
    b['ratio']=b['Distance (Miles)']/b['gc']
    print("distance/greatcircle ratio by mode:", b.groupby('Mode')['ratio'].describe().round(2))
    # total cost check
    tc=(b['Quantity']*b['Shipping Cost/Unit']).round(2)
    print("Total_Cost mismatches:", (abs(tc-b['Total_Cost'])>0.011).sum())
    co2=(b['Quantity']*0.05*b['Distance (Miles)']*b['Mode'].map(F)).round(1)
    diff=(co2-b['CO2 Emissions (kg)'])
    print("CO2 mismatches >0.1:", (abs(diff)>0.11).sum(), "max abs diff", diff.abs().max())
    print("CO2 total kg", b['CO2 Emissions (kg)'].sum(), "per unit-mile by mode", (b.groupby('Mode')['CO2 Emissions (kg)'].sum()/b.assign(um=b['Quantity']*b['Distance (Miles)']).groupby('Mode')['um'].sum()).round(4).to_dict())
    print("Quantity total", b['Quantity'].sum(), "by product", b.groupby(b.columns[6])['Quantity'].sum().to_dict(), "qty range", b['Quantity'].min(), b['Quantity'].max())
    print("neg/zero lead", (b['Lead Time (days)']<=0).sum(), "zero/neg distance", (b['Distance (Miles)']<=0).sum())
    b.to_pickle(f'ship2_{n}.pkl')
