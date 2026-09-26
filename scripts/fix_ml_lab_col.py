import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("Value_kg_ha", "yield_kg_ha")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Replaced column names")
