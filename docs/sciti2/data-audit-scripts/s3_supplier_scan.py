import openpyxl, collections, re, pickle
X="/Users/kevindooley/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"
res={}
for mode in (False, True):
    wb=openpyxl.load_workbook(X,read_only=True,data_only=mode)
    ws=wb["Supplier Data"]
    kinds=collections.Counter(); first={}; last={}
    rows=[]
    colsets=collections.Counter()
    n=0
    for r in ws.iter_rows(min_row=2, values_only=True):
        n+=1
        rowi=n+1
        a=r[:12]
        nonnull=tuple(i for i,v in enumerate(r) if v is not None)
        # classify A:L
        def k(v):
            if v is None: return 'None'
            if isinstance(v,str) and v.startswith('='): return 'formula'
            if isinstance(v,str) and v.strip()=='' : return 'blankstr'
            if isinstance(v,str) and v.startswith('#'): return 'err:'+v
            return type(v).__name__
        sig=tuple(k(v) for v in a)
        kinds[sig]+=1
        first.setdefault(sig,rowi); last[sig]=rowi
        if mode and rowi<=600: rows.append((rowi,r))
        colsets[tuple(sorted(set(i for i in nonnull if i>=12)))] +=0
    res[mode]=(n,kinds,first,last,rows)
    print("data_only=",mode,"rows scanned",n)
    for sig,c in kinds.most_common(15):
        print(c, first[sig], last[sig], sig)
pickle.dump(res[True][4], open('sup_rows600.pkl','wb'))
