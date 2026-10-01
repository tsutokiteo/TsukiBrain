import bpy
import json
import os
import time

FEED_FILE = r"F:\TsukiBrain\output\feed_signal.json"
_last_ts = 0
_feed_active = False
_feed_start = 0
_feed_duration = 0
_feed_type = "none"

# ========== 兼容清理旧定时器 ==========
def _clean_old_timers():
    # 尝试注销名为 feed_timer 的定时器（兼容所有版本）
    try:
        bpy.app.timers.unregister(feed_timer)
    except Exception:
        pass
    # 额外：遍历尝试清理（避免重复注册导致累加）
    if hasattr(bpy.app.timers, "registry"):
        # 新版本有 registry
        for h in list(bpy.app.timers.registry):
            if "feed" in str(h):
                try:
                    bpy.app.timers.unregister(h)
                except Exception:
                    pass
    else:
        # 旧版本无 registry，直接尝试注销（已在上一步处理）
        pass

_clean_old_timers()

# ========== 形态键辅助 ==========
def _set_mouth_shape(stage):
    """stage: 0=闭, 1=微张, 2=大张, 3=紧闭"""
    body = bpy.context.active_object
    if not body or not body.data.shape_keys:
        return
    keys = body.data.shape_keys.key_blocks
    # 按常见命名匹配，按需修改
    mouth_open = None
    mouth_close = None
    for k in keys:
        kn = k.name.lower()
        if any(x in kn for x in ["open", "a", "啊", "あ"]):
            mouth_open = k.name
        if any(x in kn for x in ["close", "n", "嗯", "ん"]):
            mouth_close = k.name
    if stage == 0:  # 正常闭
        if mouth_open: keys[mouth_open].value = 0.0
        if mouth_close: keys[mouth_close].value = 0.0
    elif stage == 1:  # 微张（水/准备）
        if mouth_open: keys[mouth_open].value = 0.3
        if mouth_close: keys[mouth_close].value = 0.0
    elif stage == 2:  # 大张（糖/电击）
        if mouth_open: keys[mouth_open].value = 0.8
        if mouth_close: keys[mouth_close].value = 0.0
    elif stage == 3:  # 紧闭（苦）
        if mouth_open: keys[mouth_open].value = 0.0
        if mouth_close: keys[mouth_close].value = 0.8

def _ear_tail_reaction(ftype, intensity):
    """简单骨骼反应（按需改骨骼名）"""
    try:
        ear_l = bpy.context.scene.objects.get("Ear.001.L")
        ear_r = bpy.context.scene.objects.get("Ear.001.R")
        if ear_l and ear_r:
            if ftype == "sugar":
                ear_l.rotation_euler[0] = 0.1 * intensity
                ear_r.rotation_euler[0] = 0.1 * intensity
            elif ftype == "bitter":
                ear_l.rotation_euler[0] = -0.1
                ear_r.rotation_euler[0] = -0.1
            else:
                ear_l.rotation_euler[0] = 0
                ear_r.rotation_euler[0] = 0
    except Exception:
        pass

# ========== 投喂触发 ==========
def trigger_feed_response(ftype, intensity, duration):
    global _feed_active, _feed_start, _feed_duration, _feed_type
    _feed_active = True
    _feed_start = time.time()
    _feed_duration = duration / 100.0  # duration 是帧数近似，转秒
    _feed_type = ftype

    print(f"🍽️ 投喂反应: {ftype} (强度={intensity}, 持续={duration})")
    _ear_tail_reaction(ftype, intensity)

    if ftype == "sugar":
        _set_mouth_shape(2)
    elif ftype == "water":
        _set_mouth_shape(1)
    elif ftype == "bitter":
        _set_mouth_shape(3)
    elif ftype == "shock":
        _set_mouth_shape(2)
    else:
        _set_mouth_shape(0)

# ========== 主定时器 ==========
def feed_timer():
    global _last_ts, _feed_active, _feed_start, _feed_duration, _feed_type
    if not os.path.exists(FEED_FILE):
        return 0.01

    try:
        with open(FEED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return 0.01

    ts = data.get("ts", 0)
    if ts != _last_ts:
        _last_ts = ts
        ftype = data.get("type", "none")
        if ftype != "none":
            trigger_feed_response(ftype, data.get("intensity", 1.0), data.get("duration", 50))

    # 持续动画恢复
    if _feed_active:
        elapsed = time.time() - _feed_start
        if elapsed >= _feed_duration:
            _feed_active = False
            _set_mouth_shape(0)
            _ear_tail_reaction("none", 0)
            # 写回 none 防重复
            try:
                with open(FEED_FILE, "w", encoding="utf-8") as f:
                    json.dump({"type": "none", "intensity": 0, "duration": 0, "ts": time.time()}, f)
            except Exception:
                pass

    return 0.01  # 10ms 轮询，低延迟

# ========== 启动 ==========
bpy.app.timers.register(feed_timer)
print("✅ FlyBrain 投喂监听器 v2 已启动 (10ms轮询, 兼容模式)")