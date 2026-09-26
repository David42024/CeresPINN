def fix_indentation():
    file_path = "ml_lab/app.py"
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip() == "if search_btn:":
            start_idx = i
        if start_idx != -1 and line.strip() == 'st.success("¡El ganador ha sido guardado como el cerebro de producción de CeresPINN v4!")':
            end_idx = i
            break
            
    if start_idx == -1 or end_idx == -1:
        print("Block not found!")
        return
        
    print(f"Fixing indentation from {start_idx} to {end_idx}")
    
    for i in range(start_idx, end_idx + 1):
        if lines[i].startswith("    "):
            lines[i] = lines[i][4:]
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    print("Indentation fixed!")

fix_indentation()
