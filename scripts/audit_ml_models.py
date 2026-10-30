import os
import re
import sys

# Set output to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

root_dir = r"c:\Users\aouti\Desktop\PS-3\FarmerHelp"

ignore_dirs = {"node_modules", ".git", "dist", "build", "__pycache__", ".venv", "venv", "env"}
model_extensions = {".pkl", ".pickle", ".joblib", ".pt", ".pth", ".onnx", ".h5", ".keras", ".safetensors", ".bin"}
model_keywords = {"model", "classifier", "regressor", "vectorizer", "encoder", "scaler", "pipeline", "tfidf", "embedding", "weights", "checkpoint"}

found_files = []

for dirpath, dirnames, filenames in os.walk(root_dir):
    dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
    for filename in filenames:
        ext = os.path.splitext(filename)[1].lower()
        name_lower = filename.lower()
        
        is_ext_match = ext in model_extensions
        is_name_match = any(kw in name_lower for kw in model_keywords)
        
        if is_ext_match or is_name_match:
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
            size_bytes = os.path.getsize(full_path)
            found_files.append({
                "filename": filename,
                "rel_path": rel_path,
                "full_path": full_path,
                "extension": ext or "none",
                "size_bytes": size_bytes
            })

print("=== ALL FOUND MATCHING FILES ===")
for f in found_files:
    print(f"{f['filename']} | {f['rel_path']} | {f['extension']} | {f['size_bytes']} bytes ({f['size_bytes']/1024/1024:.2f} MB)")

print("\n=== SEARCHING CODE FOR RELEVANT REFERENCES ===")

code_patterns = [
    r"joblib\.load",
    r"pickle\.load",
    r"torch\.load",
    r"onnxruntime",
    r"keras\.models",
    r"load_model",
    r"load_weights",
    r"from_pretrained",
    r"\.pkl",
    r"\.joblib",
    r"\.pth",
    r"\.pt",
    r"\.onnx",
    r"\.safetensors",
    r"predict\.py",
    r"crop_recommendation_model",
    r"document_matrix",
    r"tfidf_vectorizer"
]

code_matches = []

for dirpath, dirnames, filenames in os.walk(root_dir):
    dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
    for filename in filenames:
        if filename.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".env", ".example")):
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for idx, line in enumerate(lines):
                        for pat in code_patterns:
                            if re.search(pat, line, re.IGNORECASE):
                                code_matches.append((rel_path, idx + 1, pat, line.strip()))
            except Exception as e:
                pass

print(f"\nFound {len(code_matches)} code match lines:")
for m in code_matches:
    print(f"{m[0]}:{m[1]} [{m[2]}] -> {m[3]}")
