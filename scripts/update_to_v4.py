import os

file_path = "backend/inference.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("cerespinn_ridge_v3.joblib", "cerespinn_spatial_v4.joblib")
content = content.replace("cerespinn_ridge_v3_metadata.json", "cerespinn_spatial_v4_metadata.json")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

file_path = "backend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()
    
content = content.replace("v3.0.0", "v4.0.0")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated pointers to v4")
