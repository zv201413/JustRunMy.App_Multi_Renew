#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import requests
from seleniumbase import SB

# ============================================================
#  环境变量配置 (严格对接你要求的变量名)
# ============================================================
ACCOUNTS = []
# 账号 A
if os.environ.get("EML_1") and os.environ.get("PWD_1"):
    ACCOUNTS.append({"email": os.environ.get("EML_1"), "pwd": os.environ.get("PWD_1"), "tag": "账号 A"})
# 账号 B
if os.environ.get("EML_2") and os.environ.get("PWD_2"):
    ACCOUNTS.append({"email": os.environ.get("EML_2"), "pwd": os.environ.get("PWD_2"), "tag": "账号 B"})

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_ID    = os.environ.get("TG_ID")

if not ACCOUNTS:
    print("❌ 致命错误：未检测到有效环境变量（EML_1/PWD_1 或 EML_2/PWD_2）")
    sys.exit(1)

# 全局变量，用于动态保存网页上抓取到的应用名称
DYNAMIC_APP_NAME = "未知应用"

# ============================================================
#  原版核心 JS 注入逻辑 (一字未改)
# ============================================================
_EXPAND_JS = """(function() { var ts = document.querySelector('input[name="cf-turnstile-response"]'); if (!ts) return 'no-turnstile'; var el = ts; for (var i = 0; i < 20; i++) { el = el.parentElement; if (!el) break; var s = window.getComputedStyle(el); if (s.overflow === 'hidden' || s.overflowX === 'hidden' || s.overflowY === 'hidden') el.style.overflow = 'visible'; el.style.minWidth = 'max-content'; } document.querySelectorAll('iframe').forEach(function(f){ if (f.src && f.src.includes('challenges.cloudflare.com')) { f.style.width = '300px'; f.style.height = '65px'; f.style.minWidth = '300px'; f.style.visibility = 'visible'; f.style.opacity = '1'; } }); return 'done'; })()"""
_SOLVED_JS = """(function(){ var i = document.querySelector('input[name="cf-turnstile-response"]'); return !!(i && i.value && i.value.length > 20); })()"""
_EXISTS_JS = """(function(){ return document.querySelector('input[name="cf-turnstile-response"]') !== null; })()"""
_COORDS_JS = """(function(){ var iframes = document.querySelectorAll('iframe'); for (var i = 0; i < iframes.length; i++) { var src = iframes[i].src || ''; if (src.includes('cloudflare') || src.includes('turnstile') || src.includes('challenges')) { var r = iframes[i].getBoundingClientRect(); if (r.width > 0 && r.height > 0) return {cx: Math.round(r.x + 30), cy: Math.round(r.y + r.height / 2)}; } } return null; })()"""
_WININFO_JS = """(function(){ return {sx: window.screenX || 0, sy: window.screenY || 0, oh: window.outerHeight, ih: window.innerHeight}; })()"""

# ============================================================
#  原版底层物理点击与窗口激活逻辑 (完全保留)
# ============================================================
def _activate_window():
    for cls in ["chrome", "chromium", "Chromium", "Chrome", "google-chrome"]:
        try:
            r = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", cls], capture_output=True, text=True, timeout=3)
            wids = [w for w in r.stdout.strip().split("\n") if w.strip()]
            if wids:
                subprocess.run(["xdotool", "windowactivate", "--sync", wids[0]], timeout=3, stderr=subprocess.DEVNULL)
                return True
        except: pass
    return False

def _xdotool_click(x: int, y: int):
    _activate_window()
    try:
        subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], timeout=3, stderr=subprocess.DEVNULL)
        time.sleep(0.15)
        subprocess.run(["xdotool", "click", "1"], timeout=2, stderr=subprocess.DEVNULL)
    except:
        os.system(f"xdotool mousemove {x} {y} click 1 2>/dev/null")

def handle_turnstile(sb) -> bool:
    print("🔍 处理 Cloudflare Turnstile 验证...")
    for attempt in range(1, 11):
        if sb.execute_script(_SOLVED_JS):
            print(f"  ✅ Turnstile 已通过")
            return True
        try:
            sb.execute_script(_EXPAND_JS)
            coords = sb.execute_script(_COORDS_JS)
            wi = sb.execute_script(_WININFO_JS)
            if coords:
                title_bar_height = wi["oh"] - wi["ih"]
                abs_x = coords["cx"] + wi["sx"]
                abs_y = coords["cy"] + wi["sy"] + (title_bar_height if title_bar_height > 0 else 0)
                print(f"  🖱️ 物理点击 Turnstile ({abs_x}, {abs_y})")
                _xdotool_click(abs_x, abs_y)
        except Exception as e:
            print(f"  ⚠️ 点击尝试失败: {e}")
        time.sleep(5)
    return sb.execute_script(_SOLVED_JS)

def js_fill_input(sb, selector, text):
    safe_text = text.replace('"', '\\"')
    sb.execute_script(f'document.querySelector("{selector}").value = "{safe_text}";')
    sb.execute_script(f'document.querySelector("{selector}").dispatchEvent(new Event("input", {{ bubbles: true }}));')

# ============================================================
#  消息通知
# ============================================================
def send_tg_message(status_icon, status_text, time_left):
    if not TG_TOKEN or not TG_ID: return
    local_time = time.gmtime(time.time() + 8 * 3600)
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    message = (f"🖥 {DYNAMIC_APP_NAME}\n{status_icon} {status_text}\n⏱️ 剩余: {time_left}\n📅 {current_time_str}")
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={"chat_id": TG_ID, "text": message}, timeout=10)
    except: pass

# ============================================================
#  单账号执行逻辑
# ============================================================
def run_renewal_process(sb, acc):
    global DYNAMIC_APP_NAME
    print(f"\n🚀 正在处理【{acc['tag']}】: {acc['email']}")
    
    # 1. 登录
    sb.uc_open_with_reconnect("https://justrunmy.app/id/Account/Login")
    sb.wait_for_element('input[name="Email"]', timeout=15)
    js_fill_input(sb, 'input[name="Email"]', acc['email'])
    js_fill_input(sb, 'input[name="Password"]', acc['pwd'])
    
    if sb.execute_script(_EXISTS_JS):
        handle_turnstile(sb)
    
    sb.press_keys('input[name="Password"]', '\n')
    time.sleep(5)
    
    if "Login" in sb.get_current_url():
        raise Exception("登录失败，请检查账号密码或验证码。")

    # 2. 续期
    sb.open("https://justrunmy.app/panel")
    sb.wait_for_element('h3.font-semibold', timeout=20)
    DYNAMIC_APP_NAME = sb.get_text('h3.font-semibold')
    sb.click('h3.font-semibold')
    time.sleep(3)
    
    sb.click('button:contains("Reset Timer")')
    time.sleep(3)
    if sb.execute_script(_EXISTS_JS):
        handle_turnstile(sb)
        
    sb.click('button:contains("Just Reset")')
    print("⏳ 等待续期完成...")
    time.sleep(8)
    
    sb.refresh()
    time.sleep(5)
    timer_text = sb.get_text('span.font-mono.text-xl')
    print(f"⏱️ 状态: {timer_text}")
    send_tg_message("✅", "续期完成", timer_text)

# ============================================================
#  主程序入口
# ============================================================
def main():
    use_proxy = os.environ.get("USE_PROXY", "false").lower() == "true"
    sb_kwargs = {"uc": True, "test": True, "headless": False}
    if use_proxy:
        sb_kwargs["proxy"] = "http://127.0.0.1:8080"
        
    with SB(**sb_kwargs) as sb:
        for acc in ACCOUNTS:
            try:
                run_renewal_process(sb, acc)
                sb.delete_all_cookies() # 切换账号前清除状态
                time.sleep(2)
            except Exception as e:
                print(f"💥 {acc['tag']} 运行异常: {e}")
                send_tg_message("❌", "运行失败", str(e)[:30])

if __name__ == "__main__":
    main()
