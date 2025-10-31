"""
Test Playwright screenshot streaming capabilities
Quick proof-of-concept to benchmark performance
"""

import asyncio
import base64
import time
from playwright.async_api import async_playwright

async def test_screenshot_streaming():
    """Test screenshot capture performance"""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        # Navigate to a page
        await page.goto("https://www.google.com")

        print("Testing screenshot capture performance...")
        print("-" * 60)

        # Test 1: PNG screenshots
        print("\n1. PNG Format:")
        start = time.time()
        for i in range(10):
            screenshot_bytes = await page.screenshot(type='png', full_page=False)
            size_kb = len(screenshot_bytes) / 1024
            print(f"  Screenshot {i+1}: {size_kb:.1f} KB")
        elapsed = time.time() - start
        print(f"  Total time: {elapsed:.2f}s ({10/elapsed:.1f} FPS)")

        # Test 2: JPEG screenshots (80% quality)
        print("\n2. JPEG Format (80% quality):")
        start = time.time()
        for i in range(10):
            screenshot_bytes = await page.screenshot(
                type='jpeg',
                quality=80,
                full_page=False
            )
            size_kb = len(screenshot_bytes) / 1024
            print(f"  Screenshot {i+1}: {size_kb:.1f} KB")
        elapsed = time.time() - start
        print(f"  Total time: {elapsed:.2f}s ({10/elapsed:.1f} FPS)")

        # Test 3: JPEG screenshots (60% quality)
        print("\n3. JPEG Format (60% quality):")
        start = time.time()
        for i in range(10):
            screenshot_bytes = await page.screenshot(
                type='jpeg',
                quality=60,
                full_page=False
            )
            size_kb = len(screenshot_bytes) / 1024
            print(f"  Screenshot {i+1}: {size_kb:.1f} KB")
        elapsed = time.time() - start
        print(f"  Total time: {elapsed:.2f}s ({10/elapsed:.1f} FPS)")

        # Test 4: Base64 encoding overhead
        print("\n4. Base64 Encoding Overhead:")
        screenshot_bytes = await page.screenshot(type='jpeg', quality=80)
        start = time.time()
        for i in range(100):
            b64 = base64.b64encode(screenshot_bytes).decode()
        elapsed = time.time() - start
        print(f"  100 encodings: {elapsed:.3f}s ({100/elapsed:.0f} ops/sec)")
        print(f"  Base64 size: {len(b64) / 1024:.1f} KB (vs {len(screenshot_bytes) / 1024:.1f} KB raw)")

        # Test 5: Streaming simulation (2 FPS for 5 seconds)
        print("\n5. Streaming Simulation (2 FPS for 5 seconds):")
        frames_captured = 0
        total_bytes = 0
        start = time.time()

        for i in range(10):  # 10 frames = 5 seconds at 2 FPS
            frame_start = time.time()
            screenshot_bytes = await page.screenshot(type='jpeg', quality=80)
            b64 = base64.b64encode(screenshot_bytes).decode()
            total_bytes += len(b64)
            frames_captured += 1

            # Simulate 500ms interval
            elapsed_frame = time.time() - frame_start
            sleep_time = max(0, 0.5 - elapsed_frame)
            await asyncio.sleep(sleep_time)

        elapsed_total = time.time() - start
        avg_fps = frames_captured / elapsed_total
        bandwidth_kbps = (total_bytes / 1024) / elapsed_total

        print(f"  Frames captured: {frames_captured}")
        print(f"  Total time: {elapsed_total:.2f}s")
        print(f"  Average FPS: {avg_fps:.2f}")
        print(f"  Bandwidth: {bandwidth_kbps:.1f} KB/s")
        print(f"  Total data: {total_bytes / 1024:.1f} KB")

        print("\n" + "=" * 60)
        print("RECOMMENDATION:")
        print("  - Use JPEG at 80% quality for good balance")
        print(f"  - 2 FPS streaming = ~{bandwidth_kbps:.0f} KB/s bandwidth")
        print("  - Screenshot capture fast enough for real-time streaming")
        print("=" * 60)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_screenshot_streaming())
