def K(p):
    s=str(p.get('source'))
    return s+'|'+str(p.get('call_number')) if 'npm' in s or s.startswith('NDL') else s
