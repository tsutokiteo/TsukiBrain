"""
FlyBrain 投喂 GUI v2
- 点击即写 feed_signal.json
- 带时间戳，同类型连点也生效
- 不依赖 Brian2 仿真，纯手动测试
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import time

OUTPUT_DIR = r"F:\TsukiBrain\output"
FEED_FILE = os.path.join(OUTPUT_DIR, "feed_signal.json")

# 确保 output 目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


class FeedGUI:
    def __init__(self, root):
        self.root = root
        root.title("🪰 FlyBrain 投喂面板 v2")
        root.geometry("340x480")
        root.resizable(False, False)

        # ---- 标题 ----
        title = ttk.Label(root, text="🪰 FlyBrain 投喂面板", font=("Arial", 14, "bold"))
        title.pack(pady=(15, 5))

        # ---- 投喂按钮区 ----
        btn_frame = ttk.LabelFrame(root, text="投喂类型", padding=10)
        btn_frame.pack(pady=10, padx=20, fill="x")

        foods = [
            ("🍯 糖", "sugar", "#FFD700", "black"),
            ("💧 水", "water", "#87CEEB", "black"),
            ("☠️ 苦", "bitter", "#8B4513", "white"),
            ("⚡ 电击", "shock", "#FF4500", "white"),
        ]

        for label, ftype, bg, fg in foods:
            btn = tk.Button(
                btn_frame, text=label, width=14, height=2,
                bg=bg, fg=fg,
                font=("Arial", 12, "bold"),
                activebackground=bg, activeforeground=fg,
                command=lambda t=ftype: self.feed(t)
            )
            btn.pack(pady=4)

        # ---- 参数调节 ----
        param_frame = ttk.LabelFrame(root, text="参数", padding=10)
        param_frame.pack(pady=10, padx=20, fill="x")

        self.intensity = tk.DoubleVar(value=1.0)
        self.duration = tk.IntVar(value=50)

        ttk.Label(param_frame, text="强度:").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Scale(param_frame, from_=0.1, to=1.0, variable=self.intensity,
                   orient="horizontal", length=180,
                   command=lambda v: self._update_label(v, "intensity")).grid(row=0, column=1, padx=5)
        self.intensity_label = ttk.Label(param_frame, text="1.0")
        self.intensity_label.grid(row=0, column=2)

        ttk.Label(param_frame, text="持续(帧):").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Scale(param_frame, from_=10, to=120, variable=self.duration,
                   orient="horizontal", length=180,
                   command=lambda v: self._update_label(v, "duration")).grid(row=1, column=1, padx=5)
        self.duration_label = ttk.Label(param_frame, text="50")
        self.duration_label.grid(row=1, column=2)

        # ---- 状态 ----
        self.status = tk.StringVar(value="就绪 - 点击按钮投喂")
        status_label = ttk.Label(root, textvariable=self.status, foreground="green", font=("Arial", 10))
        status_label.pack(pady=(10, 3))

        # ---- 重置 ----
        reset_btn = ttk.Button(root, text="🔄 重置 (none)", command=self.reset)
        reset_btn.pack(pady=3)

        # ---- 快速连发 ----
        burst_frame = ttk.LabelFrame(root, text="快速连发", padding=5)
        burst_frame.pack(pady=5, padx=20, fill="x")

        ttk.Button(burst_frame, text="糖×3", width=8,
                   command=lambda: self.burst("sugar", 3, 0.3)).pack(side="left", padx=5)
        ttk.Button(burst_frame, text="苦→糖", width=8,
                   command=lambda: self.burst_sequence([("bitter", 0.5), ("sugar", 0.5)])).pack(side="left", padx=5)
        ttk.Button(burst_frame, text="电击×1", width=8,
                   command=lambda: self.burst("shock", 1, 0.5)).pack(side="left", padx=5)

    def _update_label(self, value, which):
        if which == "intensity":
            self.intensity_label.config(text=f"{float(value):.2f}")
        elif which == "duration":
            self.duration_label.config(text=str(int(float(value))))

    def feed(self, ftype):
        data = {
            "type": ftype,
            "intensity": round(self.intensity.get(), 2),
            "duration": self.duration.get(),
            "ts": time.time()
        }
        with open(FEED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        self.status.set(f"✅ {ftype} → Blender (ts={data['ts']:.3f})")

    def reset(self):
        data = {"type": "none", "intensity": 0, "duration": 0, "ts": time.time()}
        with open(FEED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        self.status.set("🔄 已重置")

    def burst(self, ftype, count, interval):
        """连发 N 次"""
        import threading
        def _burst():
            for i in range(count):
                self.feed(ftype)
                time.sleep(interval)
        threading.Thread(target=_burst, daemon=True).start()
        self.status.set(f"🔥 连发 {ftype} ×{count}")

    def burst_sequence(self, seq):
        """按顺序投喂"""
        import threading
        def _seq():
            for ftype, delay in seq:
                self.feed(ftype)
                time.sleep(delay)
        threading.Thread(target=_seq, daemon=True).start()
        types = " → ".join(t[0] for t in seq)
        self.status.set(f"🔥 序列: {types}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FeedGUI(root)
    root.mainloop()