#!/usr/bin/env python3
"""Test cumulative analysis display."""
import asyncio
from playwright.async_api import async_playwright

async def click_card(page, card_id, context):
    """Click a card button and wait for page to update."""
    try:
        button = page.locator(f'button:has-text("{card_id[0]}")').filter(has=page.locator(f'button[key*="card_{context}_{card_id}"]')).first
        await button.click()
        await page.wait_for_timeout(1000)  # Wait for rerender
    except Exception as e:
        print(f"Warning: Could not click {card_id}: {e}")

async def main():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})

        print("\n=== Loading app ===")
        await page.goto('http://localhost:8501')
        await page.wait_for_timeout(3000)

        print("\n=== Step 1: Select Hero Cards (Ah, Kd) ===")
        # Click Ah in hero context
        ah_button = page.locator('button[key="card_hero_Ah"]')
        await ah_button.click()
        await page.wait_for_timeout(1500)
        print("Selected Ah")

        # Click Kd in hero context
        kd_button = page.locator('button[key="card_hero_Kd"]')
        await kd_button.click()
        await page.wait_for_timeout(2000)
        print("Selected Kd")

        # Screenshot after preflop
        await page.screenshot(path='cumulative_01_preflop.png', full_page=True)
        print("✓ Screenshot: Preflop analysis should be visible")

        # Check for Preflop Analysis
        preflop = await page.locator('text=Preflop Analysis').count()
        print(f"  - Preflop Analysis found: {preflop > 0}")

        print("\n=== Step 2: Select Flop (Qh, Jc, Tc) ===")
        # Click Qh in board context
        qh_button = page.locator('button[key="card_board_Qh"]')
        await qh_button.click()
        await page.wait_for_timeout(1500)
        print("Selected Qh")

        jc_button = page.locator('button[key="card_board_Jc"]')
        await jc_button.click()
        await page.wait_for_timeout(1500)
        print("Selected Jc")

        tc_button = page.locator('button[key="card_board_Tc"]')
        await tc_button.click()
        await page.wait_for_timeout(2000)
        print("Selected Tc")

        # Screenshot after flop
        await page.screenshot(path='cumulative_02_flop.png', full_page=True)
        print("✓ Screenshot: Preflop + Flop analysis should both be visible")

        # Check both analyses are visible
        preflop = await page.locator('text=Preflop Analysis').count()
        flop = await page.locator('text=Flop Analysis').count()
        print(f"  - Preflop still visible: {preflop > 0}")
        print(f"  - Flop Analysis found: {flop > 0}")

        print("\n=== Step 3: Select Turn (9s) ===")
        s9_button = page.locator('button[key="card_board_9s"]')
        await s9_button.click()
        await page.wait_for_timeout(2000)
        print("Selected 9s")

        await page.screenshot(path='cumulative_03_turn.png', full_page=True)
        print("✓ Screenshot: Preflop + Flop + Turn all visible")

        preflop = await page.locator('text=Preflop Analysis').count()
        flop = await page.locator('text=Flop Analysis').count()
        turn = await page.locator('text=Turn Analysis').count()
        print(f"  - Preflop still visible: {preflop > 0}")
        print(f"  - Flop still visible: {flop > 0}")
        print(f"  - Turn Analysis found: {turn > 0}")

        print("\n=== Step 4: Select River (8d) ===")
        d8_button = page.locator('button[key="card_board_8d"]')
        await d8_button.click()
        await page.wait_for_timeout(2000)
        print("Selected 8d")

        await page.screenshot(path='cumulative_04_river.png', full_page=True)
        print("✓ Screenshot: All analyses visible (Preflop + Flop + Turn + River)")

        preflop = await page.locator('text=Preflop Analysis').count()
        flop = await page.locator('text=Flop Analysis').count()
        turn = await page.locator('text=Turn Analysis').count()
        river = await page.locator('text=River Analysis').count()
        print(f"  - Preflop still visible: {preflop > 0}")
        print(f"  - Flop still visible: {flop > 0}")
        print(f"  - Turn still visible: {turn > 0}")
        print(f"  - River Analysis found: {river > 0}")

        # Check for errors
        errors = await page.locator('.stException').count()
        if errors > 0:
            print("\n❌ ERRORS DETECTED!")
        else:
            print("\n✅ No errors detected")

        await browser.close()
        print("\n=== Test Complete ===")

if __name__ == '__main__':
    asyncio.run(main())
