"""调试Geetest - 保存canvas图并测试ddddocr"""
import sys, os, time, base64, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright
import ddddocr
from PIL import Image

SAVE_DIR = os.path.dirname(__file__)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox"])
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    
    page.goto("https://www.tanz.website/auth/register?code=ssfJ", wait_until="domcontentloaded", timeout=20000)
    time.sleep(3)
    
    # 填表
    page.locator('#name').first.fill("测试")
    page.locator('#email').first.fill("test")
    page.locator('#email_postfix').first.select_option('@qq.com')
    
    # 触发Geetest
    page.locator('[class*="geetest_btn"]').first.click()
    time.sleep(3)
    
    # 等canvas加载
    try:
        page.wait_for_selector('canvas.geetest_canvas_bg', timeout=8000)
    except:
        pass
    time.sleep(2)
    
    # 获取canvas信息
    info = page.evaluate("""() => {
        let cans = document.querySelectorAll('canvas');
        let r = [];
        cans.forEach(function(c, i) {
            r.push({
                index: i,
                cls: c.className.toString(),
                w: c.width,
                h: c.height,
                bbox: (function() {
                    let b = c.getBoundingClientRect();
                    return {x: b.x, y: b.y, w: b.width, h: b.height};
                })()
            });
        });
        return r;
    }""")
    
    print("Canvas信息:")
    for c in info:
        print(f"  [{c['index']}] {c['cls']} logical={c['w']}x{c['h']} display={c['bbox']['w']:.0f}x{c['bbox']['h']:.0f}")
    
    # 保存每个canvas
    for i, c in enumerate(info):
        data = page.evaluate(f"() => document.querySelectorAll('canvas')[{i}].toDataURL('image/png')")
        if data:
            img_bytes = base64.b64decode(data.split(',')[1])
            fname = os.path.join(SAVE_DIR, f"canvas_{i}_{c['cls'].replace('.','_').replace(' ','_')[:50]}.png")
            with open(fname, 'wb') as f:
                f.write(img_bytes)
            print(f"  保存: {fname}")
    
    # 测试ddddocr
    print("\nddddocr测试:")
    det = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    
    for bg_idx in range(len(info)):
        for sl_idx in range(len(info)):
            if bg_idx == sl_idx:
                continue
            try:
                bg_data = page.evaluate(f"() => document.querySelectorAll('canvas')[{bg_idx}].toDataURL('image/png')")
                sl_data = page.evaluate(f"() => document.querySelectorAll('canvas')[{sl_idx}].toDataURL('image/png')")
                bg_bytes = base64.b64decode(bg_data.split(',')[1])
                sl_bytes = base64.b64decode(sl_data.split(',')[1])
                
                for simple in [True, False]:
                    try:
                        res = det.slide_match(sl_bytes, bg_bytes, simple_target=simple)
                        if res and res.get('target'):
                            x = res['target'][0]
                            print(f"  bg[{bg_idx}]({info[bg_idx]['cls'][:30]}) <> sl[{sl_idx}]({info[sl_idx]['cls'][:30]}) simple={simple}: {res}")
                    except Exception as e:
                        print(f"  bg[{bg_idx}]<>sl[{sl_idx}] simple={simple}: ERROR - {e}")
            except:
                pass
    
    # 滑块的bounding box
    slider = page.query_selector('.geetest_slider_button')
    if slider:
        box = slider.bounding_box()
        print(f"\n滑块位置: x={box['x']:.0f} y={box['y']:.0f} w={box['width']:.0f} h={box['height']:.0f}")
    
    # Geetest container位置
    container = page.query_selector('.geetest_wind, .geetest_holder')
    if container:
        box = container.bounding_box()
        print(f"面板位置: x={box['x']:.0f} y={box['y']:.0f} w={box['width']:.0f} h={box['height']:.0f}")
    
    page.screenshot(path=os.path.join(SAVE_DIR, "geetest_debug_full.png"))
    print("全页截图保存")
    
    time.sleep(3)
    browser.close()
