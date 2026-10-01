"""
FAFB v783 + Brian2 LIF + 降频输出 + 降噪 + 投喂信号
"""
import os, json, time, math
import numpy as np
import pandas as pd
from scipy import sparse
import brian2 as b

# ============ 路径 ============
DATA_DIR = r"F:\TsukiBrain\repos\fly-brain\data"
CONN_FILE = os.path.join(DATA_DIR, "2025_Connectivity_783.parquet")
OUT_FILE = r"F:\TsukiBrain\output\flybrain_output.json"
FEED_FILE = r"F:\TsukiBrain\output\feed_signal.json"
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

# ============ 参数 ============
DT = 0.1 * b.ms
N_PER_GROUP = 200
TOP_K_COMMUNITIES = 15
GROUP_NAMES = ["hs", "vs", "pam", "ppl1", "dna01", "dna02", "odon1", "adn", "kc", "mbon"]

# ============ 加载连接表 ============
print("加载连接表...")
t0 = time.time()
conn = pd.read_parquet(CONN_FILE)
print(f"  连接数: {len(conn)} | {time.time()-t0:.1f}s")

print("建稀疏邻接矩阵...")
t0 = time.time()
pre_counts = conn['Presynaptic_ID'].value_counts()
post_counts = conn['Postsynaptic_ID'].value_counts()
total_counts = (pre_counts + post_counts).fillna(0).sort_values(ascending=False)
top_ids = total_counts.head(N_PER_GROUP * TOP_K_COMMUNITIES).index.values
id_to_idx = {nid: i for i, nid in enumerate(top_ids)}

mask_pre = conn['Presynaptic_ID'].isin(top_ids)
mask_post = conn['Postsynaptic_ID'].isin(top_ids)
conn_filtered = conn[mask_pre & mask_post].copy()

rows = [id_to_idx[nid] for nid in conn_filtered['Presynaptic_ID']]
cols = [id_to_idx[nid] for nid in conn_filtered['Postsynaptic_ID']]
weights = conn_filtered['Connectivity'].values
weights_norm = weights / weights.max() * 0.5
adj = sparse.csr_matrix((weights_norm, (rows, cols)),
                        shape=(len(top_ids), len(top_ids)))
print(f"  邻接矩阵: {adj.shape}, 非零: {adj.nnz} | {time.time()-t0:.1f}s")

# ============ 社区检测 ============
print("社区检测...")
row_sums = np.array(adj.sum(axis=1)).flatten()
sorted_indices = np.argsort(row_sums)[::-1]
communities = {}
for i in range(TOP_K_COMMUNITIES):
    start = i * N_PER_GROUP
    end = start + N_PER_GROUP
    communities[i] = list(sorted_indices[start:end])

group_to_nodes = {}
for i, name in enumerate(GROUP_NAMES):
    if i < len(communities):
        group_to_nodes[name] = communities[i]
    else:
        group_to_nodes[name] = communities[i % len(communities)]

for name, nodes in group_to_nodes.items():
    print(f"  {name}: {len(nodes)} 神经元")

# ============ Brian2 网络 ============
print("建 Brian2 LIF 网络...")
lif_eqs = '''
dv/dt = (I_ext - v) / (20*ms) : volt (unless refractory)
I_ext : volt
'''

groups = {}
for name in GROUP_NAMES:
    n = len(group_to_nodes[name])
    grp = b.NeuronGroup(n, lif_eqs, threshold='v > 20*mV',
                        reset='v = 0*mV', refractory=2*b.ms, name=name)
    grp.v = '10*mV + rand()*10*mV'
    grp.I_ext = '5*mV + randn()*1.5*mV'
    groups[name] = grp

# 突触连接
print("  建群间突触连接...")
synapses = {}
for name in GROUP_NAMES:
    src_nodes = group_to_nodes[name]
    src_len = len(src_nodes)
    for target_name in GROUP_NAMES:
        if name == target_name:
            continue
        tgt_nodes = group_to_nodes[target_name]
        tgt_len = len(tgt_nodes)
        sub_adj = adj[src_nodes][:, tgt_nodes]
        if sub_adj.nnz == 0:
            continue
        avg_weight = max(sub_adj.data.mean() * 2.0, 0.01)
        syn = b.Synapses(groups[name], groups[target_name],
                         'w : volt', on_pre='v_post += w')
        p_val = min(0.1, sub_adj.nnz / (src_len * tgt_len * 10))
        syn.connect(p=p_val)
        syn.w = f'{avg_weight:.3f}*mV'
        synapses[f"{name}->{target_name}"] = syn

print(f"  突触组: {len(synapses)}")

# ============ 仿真 ============
b.defaultclock.dt = DT
print(f"\n仿真启动！输出: {OUT_FILE}")
print("按 Ctrl+C 停止\n")

step = 0
feed_type = "none"
feed_intensity = 0.0
feed_timer = 0

def group_out(grp):
    v_mean = np.mean(grp.v / b.mV)
    return min(max((v_mean - 5) / 20, 0.0), 1.0)

try:
    while True:
        step += 1
        t = step * 0.1

        # 读投喂
        if os.path.exists(FEED_FILE):
            try:
                with open(FEED_FILE, 'r') as f:
                    feed_sig = json.load(f)
                if feed_sig.get("type", "none") != "none" and feed_sig.get("duration", 0) > 0:
                    feed_type = feed_sig["type"]
                    feed_intensity = feed_sig.get("intensity", 1.0)
                    feed_timer = feed_sig["duration"]
                    with open(FEED_FILE, 'w') as f:
                        json.dump({"type": "none", "intensity": 0, "duration": 0}, f)
            except:
                pass

        if feed_timer > 0:
            feed_timer -= 1
        else:
            feed_type = "none"
            feed_intensity = 0.0

        visual = (np.sin(t * 0.3) + 1) * 0.5
        sugar = feed_intensity if feed_type == "sugar" else 0.0
        water = feed_intensity if feed_type == "water" else 0.0
        bitter = feed_intensity if feed_type == "bitter" else 0.0
        shock = feed_intensity if feed_type == "shock" else 0.0

        # 注入电流（降噪版）
        groups["hs"].I_ext = f'{10 + visual*15 + np.random.uniform(0,3)}*mV + randn()*1.5*mV'
        groups["vs"].I_ext = f'{10 + visual*10 + np.random.uniform(0,3)}*mV + randn()*1.5*mV'
        groups["kc"].I_ext = '3*mV + randn()*1.0*mV'
        groups["mbon"].I_ext = '3*mV + randn()*1.0*mV'
        groups["pam"].I_ext = f'{5 + sugar*20 + water*5}*mV + randn()*0.8*mV'
        groups["ppl1"].I_ext = f'{5 + bitter*20 + shock*30}*mV + randn()*0.8*mV'
        groups["odon1"].I_ext = f'{5 + (1 if step%300>250 else 0)*15}*mV + randn()*2.0*mV'
        groups["adn"].I_ext = f'{5 + (np.sin(t*0.1)+1)*5}*mV + randn()*1.2*mV'
        groups["dna01"].I_ext = f'{5 + visual*8}*mV + randn()*1.5*mV'
        groups["dna02"].I_ext = f'{5 + visual*6}*mV + randn()*1.5*mV'

        b.run(DT)

        # ★ 每 10 步写一次 JSON（降频，不再抽搐）
        if step % 10 == 0:
            state = {
                "hs": round(group_out(groups["hs"]), 3),
                "vs": round(group_out(groups["vs"]), 3),
                "pam": round(group_out(groups["pam"]), 3),
                "ppl1": round(group_out(groups["ppl1"]), 3),
                "dna01": round(group_out(groups["dna01"]), 3),
                "dna02": round(group_out(groups["dna02"]), 3),
                "odon1": round(group_out(groups["odon1"]), 3),
                "adn": round(group_out(groups["adn"]), 3),
                "kc": round(group_out(groups["kc"]), 3),
                "mbon": round(group_out(groups["mbon"]), 3),
                "sugar": round(sugar, 3),
                "water": round(water, 3),
                "bitter": round(bitter, 3),
                "shock": round(shock, 3),
                "feed_type": feed_type,
                "grooming": bool(group_out(groups["odon1"]) > 0.4),
                "step": step // 10
            }
            try:
                with open(OUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(state, f, ensure_ascii=False)
            except:
                pass

        if step % 200 == 0:
            feed_str = f" FEED={feed_type}" if feed_type != "none" else ""
            print(f"[{step:5d}] HS={group_out(groups['hs']):.2f} VS={group_out(groups['vs']):.2f} "
                  f"PAM={group_out(groups['pam']):.2f} KC={group_out(groups['kc']):.2f}{feed_str}")

except KeyboardInterrupt:
    print("\n停止。")