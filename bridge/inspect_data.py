import pandas as pd

# ============ 路径 ============
DATA = r"F:\TsukiBrain\repos\fly-brain\data"

# ============ 1. 神经元列表 ============
print("=" * 60)
print("神经元列表 (2025_Completeness_783.csv)")
print("=" * 60)
neurons = pd.read_csv(f"{DATA}/2025_Completeness_783.csv")
print(f"行数: {len(neurons)}")
print(f"列名: {list(neurons.columns)}")
print()
print("前5行:")
print(neurons.head(5).to_string())
print()

# ============ 2. 连接表 ============
print("=" * 60)
print("连接表 (2025_Connectivity_783.parquet)")
print("=" * 60)
conn = pd.read_parquet(f"{DATA}/2025_Connectivity_783.parquet")
print(f"行数: {len(conn)}")
print(f"列名: {list(conn.columns)}")
print()
print("前5行:")
print(conn.head(5).to_string())
print()

# ============ 3. 看有没有脑区/类型列 ============
print("=" * 60)
print("各列唯一值数量（判断哪些是分类列）")
print("=" * 60)
for col in neurons.columns:
    try:
        n_unique = neurons[col].nunique()
        print(f"  {col}: {n_unique} 唯一值")
        if n_unique < 50:
            print(f"    值: {list(neurons[col].unique()[:20])}")
    except:
        print(f"  {col}: (无法计数)")