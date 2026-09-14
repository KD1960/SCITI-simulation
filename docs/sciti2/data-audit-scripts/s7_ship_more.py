import pandas as pd, numpy as np
B={n:pd.read_pickle(f'ship2_{n}.pkl') for n in ['cm_mfg','mfg_dc','dc_retail']}
m,d=B['mfg_dc'].reset_index(drop=True),B['dc_retail'].reset_index(drop=True)
print("same product type row-by-row:", (m['Product_Type']==d['Product_Type']).mean())
r=m['Quantity']/d['Quantity']; print("qty ratio mfg_dc/dc_retail by row:", r.describe().round(3).to_dict())
print("corr qty", np.corrcoef(m['Quantity'],d['Quantity'])[0,1])
print("MFG/DC total ratio", m['Quantity'].sum()/d['Quantity'].sum())
for p in ['Product A','Product B','Product C']:
    print(p, m.loc[m.Product_Type==p,'Quantity'].sum()/d.loc[d.Product_Type==p,'Quantity'].sum())
doc={'cm_mfg':(1.20,16.00),'mfg_dc':(1.80,18.00),'dc_retail':(1.89,14.87)}
for n,b in B.items():
    lo,hi=doc[n]; c=b['Shipping Cost/Unit']
    print(n,"doc range",lo,hi,"data",c.min(),c.max(),"below",(c<lo).sum(),"above",(c>hi).sum(), "outside share", ((c<lo)|(c>hi)).mean().round(3))
    print("   below by mode", b[c<lo]['Mode'].value_counts().to_dict(), "above by mode", b[c>hi]['Mode'].value_counts().to_dict())
    lt=b['Lead Time (days)']; print("   lead range", lt.min(), lt.max())
    # ship distance shorter than great-circle (impossible)
    for mode in ['Ship','Air','Road','Rail']:
        s=b[b.Mode==mode]
        if len(s): print(f"   {mode}: rows with distance < 0.95*greatcircle: {(s['Distance (Miles)']<0.95*s['gc']).sum()} of {len(s)}; > 1.4*gc: {(s['Distance (Miles)']>1.4*s['gc']).sum()}")
    # same OD, same mode: CV of distance
# ID prefixes
for n,b in B.items(): print(n, b.iloc[:,0].str[:4].value_counts().to_dict(), b.iloc[:3,0].tolist())
# cm_mfg vs BOM: sub-component units needed
prod=B['mfg_dc']['Quantity'].sum(); print("MFG->DC products", prod, "needs sub-component units", prod*160, "CM->MFG units", B['cm_mfg']['Quantity'].sum(), "ratio", prod*160/B['cm_mfg']['Quantity'].sum())
b=B['cm_mfg']; print(b.groupby(['Component Manufacturer','Product_Type'])['Quantity'].agg(['size','sum','mean']))
print("Elastomer/Plastic needed per product 110 vs steel 10; data ratio CM3/CM2 qty:", b[b['Component Manufacturer']=='CM_3']['Quantity'].sum()/b[b['Component Manufacturer']=='CM_2']['Quantity'].sum())
# Dubai outbound air share; per-retailer air share
d=B['dc_retail']
print("DC outbound air share:", d.groupby('DC_Location')['Mode'].apply(lambda s:(s=='Air').mean()).round(3).to_dict())
print("Retailer inbound air share:", d.groupby('Retail_Location')['Mode'].apply(lambda s:(s=='Air').mean()).round(3).to_dict())
# doc assigned pairs
assign={('Houston, TX','Columbus, OH'),('Houston, TX','Sao Paulo, Brazil'),('Dubai, UAE','Barcelona, Spain'),('Dubai, UAE','Nairobi, Kenya'),('Dubai, UAE','Mumbai, India'),('Sofia, Bulgaria','Barcelona, Spain'),('Shanghai, China','Mumbai, India'),('Shanghai, China','Singapore'),('Shanghai, China','Tokyo, Japan'),('Shanghai, China','Melbourne, Australia')}
ok=d.apply(lambda r:(r['DC_Location'],r['Retail_Location']) in assign,axis=1)
print("DC->Retail rows on doc-assigned pairs:", ok.sum(), "of", len(d), "qty share", d.loc[ok,'Quantity'].sum()/d['Quantity'].sum())
print("Retailer 1 (Columbus) inbound by DC:", d[d.Retail_Location=='Columbus, OH'].groupby('DC_Location')['Quantity'].agg(['size','sum']).to_dict())
# retail shipment qty vs doc scale
print(d.groupby('Retail_Location')['Quantity'].sum().sort_values())
m=B['mfg_dc']; print("MFG->DC qty by DC:", m.groupby('Dist_Location')['Quantity'].sum().to_dict(), "DC->Retail qty by DC:", d.groupby('DC_Location')['Quantity'].sum().to_dict())
print("MFG_US inbound Houston modes:", m[(m.MFG_Location=='Los Angeles, CA')&(m.Dist_Location=='Houston, TX')]['Mode'].value_counts().to_dict())
# Taiwan modes
c=B['cm_mfg']
print("CM_1 mode by dest", pd.crosstab(c[c['Component Manufacturer']=='CM_1']['MFG_Location'], c['Mode']).to_dict())
print("CM_1 lead range", c[c['Component Manufacturer']=='CM_1']['Lead Time (days)'].agg(['min','max']).to_dict())
print("CM_2 mode by dest", pd.crosstab(c[c['Component Manufacturer']=='CM_2']['MFG_Location'], c['Mode']).to_dict())
print("CO2 per shipment range", {n:(b['CO2 Emissions (kg)'].min(),b['CO2 Emissions (kg)'].max()) for n,b in B.items()})
