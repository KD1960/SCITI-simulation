import pandas as pd, numpy as np, openpyxl
d=pd.read_pickle('demand.pkl')
r=d.R1C/d.R1A
print("R1C/R1A within-year ratio mean/sd:", r.groupby(d.Year).agg(['mean','std','min','max']).round(4))
print("corr R1A,R1B", np.corrcoef(d.R1A,d.R1B)[0,1].round(3), "corr R1A,R1C", np.corrcoef(d.R1A,d.R1C)[0,1].round(3))
y=d[d.Year==2024]
print("CV 2024:", {c: round(y[c].std()/y[c].mean(),4) for c in ['R1A','R2A','R6A','R8A','R1B','R5A','R7A']})
print("R5 A==B==C all rows:", ((d.R5A==d.R5B)&(d.R5B==d.R5C)).all(), " R7A/R7C const:", (d.R7A/d.R7C).round(6).unique())
X="/Users/kevindooley/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"
ws=openpyxl.load_workbook(X,read_only=True)["Shipment_CM_MFG_DC_Retailers"]
row=next(ws.iter_rows(min_row=2,max_row=2))
print("Ship_Date cell types:", type(row[1].value), row[1].data_type, type(row[16].value), type(row[31].value))
b=pd.read_pickle('ship2_cm_mfg.pkl'); print("cm_mfg lead=38 rows:", b[b['Lead Time (days)']==38].iloc[:,:10].to_dict('records'))
print("exact doc rows: 6893/4:", b[(b['Distance (Miles)']==6893)].iloc[:, [0,2,4,7,8,9]].to_dict('records'), "501:", b[b['Distance (Miles)']==501].iloc[:, [0,2,4,7,8,9]].to_dict('records'))
m=pd.read_pickle('ship2_mfg_dc.pkl'); dr=pd.read_pickle('ship2_dc_retail.pkl')
print("max lead by block:", b['Lead Time (days)'].max(), m['Lead Time (days)'].max(), dr['Lead Time (days)'].max())
print("MFG_US ids in cm_mfg:", b['Manufacturer'].unique(), " mfg_dc MFG ids:", m['MFG'].unique())
