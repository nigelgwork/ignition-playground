#!/usr/bin/env python3
"""
Test script to explore Gateway modules page search functionality
"""

import asyncio
from playwright.async_api import async_playwright


async def test_module_search():
    """Test the Gateway modules page search functionality"""

    gateway_url = "http://localhost:9088"
    username = "admin"
    password = "password"

    async with async_playwright() as p:
        # Launch browser in headed mode so we can see what's happening
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Login
            print("1. Navigating to login page...")
            await page.goto(f"{gateway_url}/app/login")
            await page.wait_for_load_state("networkidle")

            print("2. Filling in credentials...")
            await page.fill("input[name='username'], input[id='username'], input[type='text']", username)
            await page.fill("input[name='password'], input[id='password'], input[type='password']", password)

            print("3. Clicking login button...")
            await page.click("button[type='submit'], button:has-text('Login'), button:has-text('Sign In')")
            await page.wait_for_load_state("networkidle")

            # Navigate to modules page
            print("4. Navigating to modules page...")
            await page.goto(f"{gateway_url}/app/platform/system/modules")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)

            # Take screenshot of modules page
            await page.screenshot(path="/git/ignition-playground/modules_page.png")
            print("   Screenshot saved to modules_page.png")

            # Explore the page structure
            print("\n5. Exploring page structure...")

            # Look for search/filter input
            search_inputs = await page.query_selector_all("input[type='text'], input[type='search'], input[placeholder*='search' i], input[placeholder*='filter' i]")
            print(f"   Found {len(search_inputs)} potential search inputs")

            for i, input_elem in enumerate(search_inputs):
                placeholder = await input_elem.get_attribute("placeholder") or ""
                name = await input_elem.get_attribute("name") or ""
                id_attr = await input_elem.get_attribute("id") or ""
                aria_label = await input_elem.get_attribute("aria-label") or ""
                print(f"   Input {i}: placeholder='{placeholder}', name='{name}', id='{id_attr}', aria-label='{aria_label}'")

            # Look for module rows/checkboxes
            checkboxes = await page.query_selector_all("input[type='checkbox']")
            print(f"\n   Found {len(checkboxes)} checkboxes")

            # Look for table structure
            tables = await page.query_selector_all("table")
            print(f"   Found {len(tables)} tables")

            if tables:
                rows = await page.query_selector_all("table tr")
                print(f"   Found {len(rows)} table rows")

                # Get first few rows to understand structure
                for i in range(min(3, len(rows))):
                    row = rows[i]
                    text = await row.inner_text()
                    print(f"   Row {i}: {text[:100]}...")

            # Test search functionality if we found an input
            if search_inputs:
                print("\n6. Testing search functionality...")
                search_input = search_inputs[0]

                # Try searching for "Python"
                test_query = "Python"
                print(f"   Entering search query: '{test_query}'")
                await search_input.fill(test_query)
                await page.wait_for_timeout(1000)

                # Take screenshot after search
                await page.screenshot(path="/git/ignition-playground/modules_search_result.png")
                print("   Screenshot saved to modules_search_result.png")

                # Check how many checkboxes are visible now
                visible_checkboxes = await page.query_selector_all("input[type='checkbox']:visible")
                print(f"   Visible checkboxes after search: {len(visible_checkboxes)}")

                # Try to get module names from visible rows
                visible_rows = await page.query_selector_all("table tr:visible")
                print(f"   Visible table rows after search: {len(visible_rows)}")

                if visible_rows:
                    print("   First few visible rows:")
                    for i in range(min(3, len(visible_rows))):
                        text = await visible_rows[i].inner_text()
                        print(f"     {text[:100]}...")

            print("\n7. Waiting 5 seconds before closing...")
            await page.wait_for_timeout(5000)

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_module_search())
