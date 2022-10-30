import pandas as pd

pdObj = pd.read_json('export.json', orient='index')
print(pdObj)