import os
import re

file_path = "backend/training/package_model.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """def hash_dataframe(df):
    return hashlib.sha256(df.to_csv(index=False).encode('utf-8')).hexdigest()"""

replacement = """def hash_dataframe(df):
    import pandas as pd
    if isinstance(df, pd.DataFrame):
        return hashlib.sha256(df.to_csv(index=False).encode('utf-8')).hexdigest()
    else:
        return hashlib.sha256(str(df).encode('utf-8')).hexdigest()"""

target = target.replace('\n', '\r\n') if '\r\n' in content else target
if target in content:
    content = content.replace(target, replacement)
else:
    target = target.replace('\r\n', '\n')
    if target in content:
        content = content.replace(target, replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated package_model.py")
