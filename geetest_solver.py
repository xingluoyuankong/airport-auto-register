#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极验(Geetest)滑块验证码突破模块
基于 ddddocr + Playwright拟人轨迹算法
支持：Geetest v3/v4 滑块验证、点击验证

用法:
    from geetest_solver import solve_geetest_slider
    result = solve_geetest_slider(page)  # True=通过
"""
import random, math, time, io
from io import BytesIO
from PIL import Image
import numpy as np
import cv2
import ddddocr

class GeetestSolver:
    """极验验证码突破器"""
    
    def __init__(self):
        self.ocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
        self.click_ocr = ddddocr.DdddOcr(det=False, ocr=True, show_ad=False)
    
    # ========== 滑块验证 ==========
    
    def _extract_captcha_images(self, page):
        """从页面提取极验Canvas数据 — 针对geetest v4 slider"""
        # 等canvas加载
        try:
            page.wait_for_selector('canvas.geetest_canvas_bg', timeout=8000)
        except:
            try:
                page.wait_for_selector('canvas', timeout=5000)
            except:
                pass
        time.sleep(0.5)
        
        data = page.evaluate("""() => {
            let bgData = null, sliceData = null;
            
            // 方法1: canvas.geetest_canvas_bg + geetest_canvas_slice
            let bgCanvas = document.querySelector('canvas.geetest_canvas_bg');
            let sliceCanvas = document.querySelector('canvas.geetest_canvas_slice');
            
            if (bgCanvas && bgCanvas.width > 0) {
                try { bgData = bgCanvas.toDataURL('image/png'); } catch(e) {}
            }
            if (sliceCanvas && sliceCanvas.width > 0) {
                try { sliceData = sliceCanvas.toDataURL('image/png'); } catch(e) {}
            }
            
            // 方法2: 备用 - 截图整个geetest区域
            if (!bgData || !sliceData) {
                let allCans = document.querySelectorAll('canvas');
                for (let c of allCans) {
                    if (c.width >= 200 && !bgData) {
                        try { bgData = c.toDataURL('image/png'); } catch(e) {}
                    } else if (c.width >= 50 && c.width < 200 && !sliceData) {
                        try { sliceData = c.toDataURL('image/png'); } catch(e) {}
                    }
                }
            }
            
            return {bg: bgData || '', slice: sliceData || ''};
        }""")
        
        return data
    
    def _data_url_to_bytes(self, data_url):
        """data: URL → bytes"""
        import base64
        if data_url.startswith("data:"):
            return base64.b64decode(data_url.split(",")[1])
        return data_url.encode() if isinstance(data_url, str) else data_url
    
    def _download_image(self, page, url_or_data):
        """下载图片为PIL Image"""
        if url_or_data.startswith("data:"):
            import base64
            b64 = url_or_data.split(",")[1]
            return Image.open(BytesIO(base64.b64decode(b64)))
        
        # 用page goto下载
        import requests
        try:
            # 获取cookie
            cookies = page.context.cookies()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": page.url
            }
            r = requests.get(url_or_data, headers=headers, cookies={c['name']:c['value'] for c in cookies}, timeout=10)
            if r.status_code == 200:
                return Image.open(BytesIO(r.content))
        except:
            pass
        return None
    
    def find_gap_cv2(self, bg_bytes, fullbg_bytes, slice_bytes=None):
        """使用OpenCV找缺口位置 — 比较bg与fullbg的差异"""
        # 方法1: 比较bg和fullbg，找到缺口位置
        try:
            bg_img = cv2.imdecode(np.frombuffer(bg_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
            fullbg_img = cv2.imdecode(np.frombuffer(fullbg_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
            
            if bg_img is None or fullbg_img is None:
                return None
            
            # 计算差异
            diff = cv2.absdiff(bg_img, fullbg_img)
            # 二值化
            _, thresh = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)
            
            # 找差异区域的轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 找最大的差异区域
                max_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(max_contour)
                gap_x = x + w // 2  # 缺口中心
                
                # 知道图片实际宽260px
                return gap_x
            
        except Exception as e:
            print(f"    CV2差异法失败: {e}", flush=True)
        
        # 方法2: 如果提供了slice图，用模板匹配
        if slice_bytes:
            try:
                bg_img = cv2.imdecode(np.frombuffer(bg_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
                sl_img = cv2.imdecode(np.frombuffer(slice_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
                
                if bg_img is not None and sl_img is not None:
                    # 模板匹配
                    result = cv2.matchTemplate(bg_img, sl_img, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    if max_val > 0.3:
                        return max_loc[0]
            except Exception as e:
                print(f"    CV2模板匹配失败: {e}", flush=True)
        
        # 方法3: ddddocr兜底
        try:
            result = self.ocr.slide_match(slice_bytes or b'', bg_bytes, simple_target=True)
            if result and 'target' in result and result['target']:
                return result['target'][0]
        except:
            pass
        
        return None
    
    def _generate_track(self, distance):
        """三段式拟人轨迹：加速-匀速-减速，带贝塞尔平滑"""
        dist = max(1, distance)
        
        track = []
        current = 0
        v = 0
        
        # 1. 加速段 (0-40%)
        a = random.uniform(1.8, 3.0)
        target1 = dist * random.uniform(0.35, 0.45)
        while current < target1:
            v += a * 0.3
            move = max(1, int(v))
            current += move
            track.append(min(current, dist))
            a *= random.uniform(0.92, 0.98)
        
        # 2. 匀速段 (40-70%)
        target2 = dist * random.uniform(0.65, 0.75)
        while current < target2:
            move = max(1, int(v + random.uniform(-1.5, 1.5)))
            current += move
            track.append(min(current, dist))
        
        # 3. 减速段 (70-90%)
        while v > 0.5 and current < dist * 0.9:
            v -= a * 0.3
            move = max(1, int(v))
            current += move
            if v < 0: v = 0
            track.append(min(current, dist))
        
        # 4. 微调段 (90-100%) — 小步慢移
        while current < dist:
            move = random.randint(1, 3)
            current += move
            track.append(min(current, dist))
        
        # 确保以distance结尾
        if track[-1] < dist:
            track.append(dist)
        
        # 平滑+扰动
        smoothed = [track[0]]
        for i in range(1, len(track)):
            val = track[i] + random.randint(-1, 1)
            val = max(smoothed[-1] + 1, min(val, dist))
            smoothed.append(int(val))
        
        if smoothed[-1] < dist:
            smoothed[-1] = dist
        
        return smoothed
    
    def solve_slider(self, page, max_retries=3):
        """
        尝试突破极验滑块验证
        返回: True=成功, False=失败
        """
        # 找到常见的极验滑块选择器
        slider_selectors = [
            '.geetest_slider_button',
            '.geetest_btn',
            '.gt_slider_knob',
            '[class*="geetest_slide"]',
            '.gt_slider',
            '.slider-button',
        ]
        
        bg_selectors = ['.geetest_bg', '.gt_bg', '[class*="geetest_canvas"]']
        slice_selectors = ['.geetest_slice', '.gt_slice', '[class*="geetest_slice"]']
        
        for attempt in range(max_retries):
            print(f"  [Geetest] 第{attempt+1}次尝试...", flush=True)
            
            # 找滑块
            slider = None
            for sel in slider_selectors:
                s = page.query_selector(sel)
                if s and s.is_visible():
                    slider = s
                    print(f"    滑块: {sel}", flush=True)
                    break
            
            if not slider:
                print("    找不到滑块元素!", flush=True)
                # 尝试直接在canvas上操作
                canvases = page.query_selector_all('canvas')
                if len(canvases) >= 2:
                    pass  # fall through to time-based approach
                else:
                    time.sleep(1)
                    continue
            
            # 提取3个Canvas数据
            bg_data = None
            slice_data = None
            fullbg_data = None
            
            try:
                bg_data = page.evaluate("""() => {
                    let c = document.querySelector('canvas.geetest_canvas_bg');
                    return c ? c.toDataURL('image/png') : '';
                }""")
                slice_data = page.evaluate("""() => {
                    let c = document.querySelector('canvas.geetest_canvas_slice');
                    return c ? c.toDataURL('image/png') : '';
                }""")
                fullbg_data = page.evaluate("""() => {
                    let c = document.querySelector('canvas.geetest_canvas_fullbg');
                    return c ? c.toDataURL('image/png') : '';
                }""")
            except:
                pass
            
            gap_x = None
            
            # 方法1: CV2比较bg和fullbg的差异
            if bg_data and fullbg_data:
                try:
                    bg_bytes = self._data_url_to_bytes(bg_data)
                    fullbg_bytes = self._data_url_to_bytes(fullbg_data)
                    slice_bytes = self._data_url_to_bytes(slice_data) if slice_data else None
                    gap_x = self.find_gap_cv2(bg_bytes, fullbg_bytes, slice_bytes)
                    if gap_x is not None:
                        print(f"    CV2缺口: {gap_x}px", flush=True)
                except Exception as e:
                    print(f"    CV2异常: {e}", flush=True)
            
            # 执行拖拽 — 先获取滑块位置
            if slider:
                box = slider.bounding_box()
            else:
                canvas = page.query_selector('.geetest_canvas_bg, canvas')
                if canvas:
                    cbox = canvas.bounding_box()
                    if cbox:
                        box = {'x': cbox['x'], 'y': cbox['y'] + cbox['height'] - 40,
                               'width': 40, 'height': 40}
                    else:
                        box = None
                else:
                    box = None
            
            if not box:
                time.sleep(1)
                continue
            
            # 不缩放！gap_x直接就是拖拽距离（canvas渲染和鼠标坐标1:1）
            if gap_x is not None:
                gap_x = gap_x + random.randint(-2, 5)
                print(f"    拖拽距离(raw): {gap_x}px", flush=True)
            
            if not box:
                time.sleep(1)
                continue
            
            start_x = box['x'] + box['width'] / 2
            start_y = box['y'] + box['height'] / 2
            
            print(f"    拖拽: start({start_x:.0f},{start_y:.0f}) -> +{gap_x}px", flush=True)
            
            # JS原生事件拖拽 — 绕过Playwright的mouse事件限制
            dragged = page.evaluate("""(params) => {
                let slider = document.querySelector('.geetest_slider_button');
                if (!slider) return false;
                
                let rect = slider.getBoundingClientRect();
                let sx = rect.x + rect.width / 2;
                let sy = rect.y + rect.height / 2;
                let distance = params.gap_x;
                
                // 生成轨迹
                let track = [];
                let seg1 = Math.floor(distance * 0.35);
                let seg2 = Math.floor(distance * 0.35);
                let seg3 = distance - seg1 - seg2;
                
                // 加速段
                for (let i = 0; i < params.steps1; i++) {
                    let p = (i + 1) / params.steps1;
                    let x = seg1 * p * p;
                    track.push(Math.min(x, distance));
                }
                // 匀速段
                for (let i = 0; i < params.steps2; i++) {
                    let p = (i + 1) / params.steps2;
                    let x = seg1 + seg2 * p;
                    track.push(Math.min(x, distance));
                }
                // 减速段
                for (let i = 0; i < params.steps3; i++) {
                    let p = (i + 1) / params.steps3;
                    let ease = 1 - Math.pow(1 - p, 3);
                    let x = seg1 + seg2 + seg3 * ease;
                    track.push(Math.min(x, distance));
                }
                track.push(distance);
                
                // 发送事件序列
                let mousedown = new MouseEvent('mousedown', {
                    clientX: sx, clientY: sy,
                    bubbles: true, cancelable: true
                });
                slider.dispatchEvent(mousedown);
                
                // 逐步移动
                let lastX = 0;
                for (let i = 0; i < track.length; i++) {
                    let dx = track[i];
                    let ex = sx + dx;
                    let ey = sy + (Math.random() * 4 - 2);
                    
                    let move = new MouseEvent('mousemove', {
                        clientX: ex, clientY: ey,
                        bubbles: true, cancelable: true,
                        movementX: dx - lastX, movementY: 0
                    });
                    document.dispatchEvent(move);
                    lastX = dx;
                }
                
                // 释放
                let mouseup = new MouseEvent('mouseup', {
                    clientX: sx + distance, clientY: sy,
                    bubbles: true, cancelable: true
                });
                document.dispatchEvent(mouseup);
                
                return true;
            }""", {
                "gap_x": int(gap_x),
                "steps1": random.randint(10, 15),
                "steps2": random.randint(5, 10),
                "steps3": random.randint(12, 18)
            })
            
            print(f"    JS拖拽: {dragged}", flush=True)
            time.sleep(2.5)  # 等极验验证
            
            # 检查结果
            body = page.evaluate("() => document.body.innerText")
            success_indicators = ["验证成功", "通过验证", "验证通过"]
            fail_indicators = ["请完成验证", "拖动滑块", "请重试", "再试一次", "失败"]
            
            for ind in success_indicators:
                if ind in body:
                    print(f"    ✅ Geetest验证通过!", flush=True)
                    return True
            
            has_fail = any(ind in body for ind in fail_indicators)
            has_slider = "拖动滑块" in body or "滑块按钮" in body
            
            if not has_slider and not has_fail:
                # 滑块消失了，可能是通过了
                print(f"    滑块消失，可能已通过!", flush=True)
                return True
            
            if has_fail:
                print(f"    验证失败，重试...", flush=True)
                # 点刷新 - 多种方式
                refresh_btns = [
                    '.geetest_refresh',
                    '.geetest_reset_tip_content',
                    '[class*="geetest_refresh"]',
                    '.geetest_panel_refresh',
                    'text=刷新验证',
                ]
                for btn_sel in refresh_btns:
                    try:
                        btn = page.locator(btn_sel).first
                        if btn.is_visible(timeout=1000):
                            btn.click(force=True, timeout=2000)
                            print("    已点击刷新", flush=True)
                            time.sleep(1)
                            break
                    except:
                        continue
                else:
                    print("    未找到刷新按钮", flush=True)
            else:
                # 滑块还在但没提示
                print(f"    滑块仍在，可能还没释放", flush=True)
        
        print(f"  [Geetest] 全部{max_retries}次重试失败", flush=True)
        return False
    
    # ========== 点击验证 ==========
    
    def solve_click_captcha(self, page, max_retries=3):
        """解决极验点选验证（如iKuuu）"""
        for attempt in range(max_retries):
            print(f"  [Geetest-Click] 第{attempt+1}次尝试...", flush=True)
            
            # 找点击目标
            targets = page.evaluate("""() => {
                let imgs = document.querySelectorAll('.geetest_item_img, [class*=geetest_item] img');
                let results = [];
                for (let img of imgs) {
                    if (img.src) {
                        results.push({src: img.src});
                    }
                }
                // 如果没有，找data URI
                if (results.length === 0) {
                    let allImgs = document.querySelectorAll('img[src^="data:"]');
                    for (let img of allImgs) {
                        results.push({src: img.src});
                    }
                }
                return results;
            }""")
            
            if not targets:
                print("    未找到点击目标", flush=True)
                time.sleep(1)
                continue
            
            print(f"    找到{len(targets)}个目标图", flush=True)
            
            # 对每个目标图，用ddddocr识别点击哪个
            import base64
            for t in targets:
                try:
                    src = t['src']
                    if src.startswith('data:'):
                        img_bytes = base64.b64decode(src.split(',')[1])
                        # 用ddddocr分类
                        result = self.click_ocr.classification(img_bytes)
                        print(f"    OCR结果: {result}", flush=True)
                except Exception as e:
                    print(f"    OCR错误: {e}", flush=True)
            
            # 简化：直接按顺序点
            images = page.query_selector_all('.geetest_item_img, [class*=geetest_item]')
            for img in images:
                try:
                    img.click(delay=random.randint(100, 300))
                    time.sleep(0.5)
                except:
                    pass
            
            time.sleep(2)
            
            # 检查结果
            body = page.evaluate("() => document.body.innerText")
            if "验证成功" in body or "验证通过" in body:
                print(f"    ✅ 点选验证通过!", flush=True)
                return True
            elif "点我开始验证" in body:
                continue
        
        return False


# ========== 便捷函数 ==========

_solver = None

def _get_solver():
    global _solver
    if _solver is None:
        _solver = GeetestSolver()
    return _solver

def solve_geetest(page):
    """统一入口：自动检测Geetest类型并解决"""
    solver = _get_solver()
    
    # 先检测类型
    body = page.evaluate("() => document.body.innerText")
    
    if "拖动滑块" in body or "滑块按钮" in body or "开始验证" in body:
        # 检测是否有点击验证特征
        has_click = page.query_selector('.geetest_item_img, [class*=geetest_item]')
        if has_click:
            return solver.solve_click_captcha(page)
        return solver.solve_slider(page)
    
    # 默认尝试滑块
    return solver.solve_slider(page)
