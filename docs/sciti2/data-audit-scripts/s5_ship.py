import pandas as pd, numpy as np, openpyxl, math
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',300)
X="/Users/kevindooley/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"
geo=pd.read_excel(X,sheet_name="Supplier Data",nrows=500,usecols="C",keep_default_na=False)
print("Geography raw:", geo.iloc[:,0].value_counts().to_dict())
sh=pd.read_excel(X,sheet_name="Shipment_CM_MFG_DC_Retailers",header=None,keep_default_na=False,na_values=[''])
print("shape",sh.shape)
blocks={}
for name,start in {"cm_mfg":0,"mfg_dc":15,"dc_retail":30}.items():
    b=sh.iloc[1:,start:start+14].copy(); b.columns=list(sh.iloc[0,start:start+14]); b=b.dropna(how='all')
    b.index=b.index+1  # excel row
    blocks[name]=b
    print("=====",name,len(b), "last excel row", b.index.max())
    print(b.isna().sum()[b.isna().sum()>0].to_dict())
for name,b in blocks.items(): b.to_pickle(f'ship_{name}.pkl')
# check rows 502-503
print(sh.iloc[500:503].dropna(axis=1,how='all'))
