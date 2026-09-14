import openpyxl, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',200)
X="/Users/kevindooley/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"
wbf=openpyxl.load_workbook(X,read_only=True)
ws=wbf["Supplier Data"]
print("G502 formula:", [c.value for c in next(ws.iter_rows(min_row=502,max_row=502))][:12])
print("G250001:", [c.value for c in next(ws.iter_rows(min_row=250001,max_row=250001))][:12])
# right-side table formulas rows 1-40
for r in ws.iter_rows(min_row=1,max_row=40,min_col=13,max_col=28):
    v=[(c.coordinate,c.value) for c in r if c.value is not None]
    if v: print(v)
df=pd.read_excel(X,sheet_name="Supplier Data",nrows=500)
tx=df.iloc[:, :12]
par=df.iloc[:30, 16:28]
print(par)
print(tx.head())
print(tx.dtypes)
print("Sales order unique:", tx['Sales Order'].nunique(), tx['Sales Order'].iloc[[0,-1]].tolist())
print("dates:", tx['Date'].min(), tx['Date'].max(), tx['Date'].dt.year.value_counts().to_dict(), "weekday counts", tx['Date'].dt.dayofweek.value_counts().to_dict())
print("Geography:", tx['Geography'].value_counts().to_dict())
print("Suppliers:", tx['Supplier'].value_counts().to_dict())
print(pd.crosstab(tx['Product Name'], tx['Supplier']))
print(pd.crosstab(tx['Product Name'], tx['Product Family']))
print(pd.crosstab(tx['Product Name'], tx['Contract Mfg']))
g=tx.groupby('Supplier').agg(n=('Lead Time','size'),lead_mean=('Lead Time','mean'),lead_sd=('Lead Time','std'),lead_min=('Lead Time','min'),lead_max=('Lead Time','max'),price_mean=('Unit Price','mean'),price_sd=('Unit Price','std'),price_min=('Unit Price','min'),price_max=('Unit Price','max'),qty_min=('Order Qty','min'),qty_max=('Order Qty','max'),neg=('Sentiment Score',lambda s:(s==1).mean()))
pp=par.rename(columns=lambda c:str(c)).set_index('Suppliers')
g=g.join(pp[['Lead Time.1','Price/Unit','Units','Order Qty.1']] if 'Lead Time.1' in pp.columns else pp, how='left')
print(g)
print("Order qty values:", tx['Order Qty'].value_counts().to_dict())
print("Sentiment:", tx['Sentiment Score'].value_counts().to_dict())
fb=tx.groupby(['Feedback','Sentiment Score']).size()
print(fb)
# sampling probabilities: P col cumulative
print("negative/zero price or lead:", (tx['Unit Price']<=0).sum(), (tx['Lead Time']<=0).sum())
tx.to_pickle('tx.pkl'); par.to_pickle('par.pkl')
