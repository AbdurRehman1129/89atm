#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Pixel Offer Checker – FULL FLOW ($100 / $452)
- NO REFRESH (AVOIDS CAPTCHA)
- Smart Back Navigation: 3× only if went to offer, 1× if already used, 2× if country failed
- Handles "Not a Pixel device" → stays on IMEI page
- Clears old IMEI before next
- Saves: imei, status, offer_amount
- Retries for dropdown, continue, and back buttons (up to 3 times)
- Removes processed IMEIs from input CSV
- NEW: Restarts browser on IMEI field not found
"""

import csv
import time
import argparse
from pathlib import Path
import re

from playwright.sync_api import sync_playwright


PROFILE_DIR = "playwright_profile"
DEFAULT_OUT_DIR = "outputs"
DEFAULT_RESULTS = "results.csv"

USER_XPATH = "/html/body/div[2]/div/div[1]/section/div/div[1]/div/article/div[67]/div[4]/div[2]/div[1]/div[2]/input"


# ----------------------------------------------------------- 
# Helper Functions
# -----------------------------------------------------------

class RestartException(Exception):
    pass


def wait_for_google_signin(page):
    if "accounts.google.com" in page.url:
        print("\n[!] Login required (possible captcha).")
        input("Complete login → press ENTER...")
    time.sleep(1)


def click_initial_confirm(page):
    print("Checking for initial Confirm screen...")
    for sel in [
        'role=button[name="Confirm"]',
        'role=button[name="Continue"]',
        'text=Confirm',
        'text=Continue',
        'text=Next'
    ]:
        try:
            page.locator(sel).first.click(timeout=1500)
            print("Clicked initial Confirm.")
            time.sleep(1)
            return True
        except:
            pass
    print("No initial Confirm found.")
    return False


def find_imei_field(page):
    """Try multiple selectors with timeout"""
    selectors = [
        'input.widget__text-input[id^="widget-id-"]',
        "input[placeholder*='123456789']",
        f"xpath={USER_XPATH}"
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=3000)
            return loc
        except:
            continue
    return None


def fill_imei(page, imei):
    loc = find_imei_field(page)
    if not loc:
        return False

    try:
        loc.scroll_into_view_if_needed(timeout=1000)
        loc.click(timeout=1500)
        loc.fill("")
        loc.type(imei, delay=30)
        return True
    except:
        try:
            handle = loc.element_handle()
            if handle:
                page.evaluate(
                    """(el, val) => {
                        el.focus(); el.value = val;
                        el.dispatchEvent(new Event('input', {bubbles:true}));
                        el.dispatchEvent(new Event('change', {bubbles:true}));
                    }""",
                    handle, imei
                )
                return True
        except:
            return False
    return False


def click_continue(page):
    for sel in [
        'role=button[name="Continue"]',
        'text=Continue',
        'text=Next',
        'role=button[name="Next"]'
    ]:
        try:
            btn = page.locator(sel).first
            btn.wait_for(state="visible", timeout=3000)
            btn.click(timeout=1500)
            time.sleep(0.8)
            return True
        except:
            pass
    return False


def click_back_button(page):
    for sel in ['text=Back', 'role=button[name="Back"]']:
        try:
            btn = page.locator(sel).first
            btn.wait_for(state="visible", timeout=2000)
            btn.click(timeout=1500)
            time.sleep(0.8)
            return True
        except:
            pass
    return False


def extract_text(page, selectors):
    for sel in selectors:
        try:
            txt = page.locator(sel).first.inner_text(timeout=2000).strip()
            if txt:
                return " ".join(txt.split())
        except:
            pass
    return ""


def select_country_afghanistan(page):
    print("Selecting country: Afghanistan...")
    # Retry up to 3 times
    for attempt in range(3):
        print(f"Attempt {attempt + 1}/3 to find dropdown...")
        dropdown = None
        for sel in ['role=combobox', '[aria-haspopup="listbox"]']:
            try:
                cand = page.locator(sel).first
                cand.wait_for(state="visible", timeout=3000)
                if "select" in cand.inner_text(timeout=1000).strip().lower():
                    dropdown = cand
                    break
            except:
                continue

        if not dropdown:
            print("Dropdown not found, retrying...")
            time.sleep(2)  # Delay before retry
            continue

        try:
            dropdown.click()
            time.sleep(0.7)
        except:
            print("Failed to click dropdown, retrying...")
            time.sleep(2)
            continue

        try:
            page.locator('role=option').first.wait_for(state="visible", timeout=3000)
        except:
            print("Options not visible, retrying...")
            time.sleep(2)
            continue

        try:
            afg = page.get_by_role("option", name="Afghanistan")
            afg.wait_for(state="visible", timeout=2000)
            afg.click()
            time.sleep(0.6)
            print("Clicked: Afghanistan")
            return True
        except Exception as e:
            print(f"Failed to select Afghanistan: {e}, retrying...")
            time.sleep(2)
            continue

    print("Failed to select Afghanistan after 3 attempts.")
    return False


def get_offer_amount(page):
    txt = extract_text(page, [
        "role=alert", "article", "main", "body", "[aria-live]",
        "text=/\\$\\d+/", "text=/USD/"
    ])
    if not txt:
        return "$0"

    txt_l = txt.lower()
    if "$452" in txt_l:
        return "$452"
    if "$100" in txt_l:
        return "$100"

    m = re.search(r'\$([0-9]+)', txt)
    return f"${m.group(1)}" if m else "$0"


def classify_status(page):
    """
    Returns: (status, needs_back_count)
    - eligible → go to country → 3× back (or 2 if country fails)
    - already used → 1× back
    - not pixel → 0× back (stay on IMEI page)
    - unknown → 0× back
    """
    txt = extract_text(page, ["role=alert", "article", "main", "body"])

    if not txt:
        return "unknown", 0

    txt_l = txt.lower()

    # 1. Not a Pixel device → stay on IMEI page
    if "not for a pixel device" in txt_l or "not a pixel" in txt_l:
        return "not pixel", 0

    # 2. Already used
    if "already" in txt_l or "used" in txt_l:
        return "already used", 1

    # 3. Eligible (not associated)
    if txt_l.startswith("it looks like that device is not associated"):
        return "eligible", 3  # will go to country → need 3× back (adjusted if fails)

    # 4. Not eligible
    if "not eligible" in txt_l:
        return "not eligible", 1

    return "unknown", 0


# ----------------------------------------------------------- 
# MAIN PROCESS
# -----------------------------------------------------------

def process_imei(page, url, imei, out_dir):
    # First IMEI: load page
    if page.url != url:
        page.goto(url, timeout=60000)
        wait_for_google_signin(page)
        click_initial_confirm(page)
        time.sleep(2)

    print(f"Filling IMEI: {imei}")
    if not fill_imei(page, imei):
        print("IMEI field not found - triggering restart")
        raise RestartException("IMEI field not found")

    if not click_continue(page):
        print("Continue failed after IMEI")
        return imei, "Continue failed", "$0"

    time.sleep(2.5)

    status, back_count_needed = classify_status(page)
    offer = "$0"
    country_selected = False

    print(f"Status: {status}")

    if status == "eligible":
        print("Eligible → Proceeding to country & offer...")
        if click_continue(page):
            time.sleep(2)
            if select_country_afghanistan(page):
                country_selected = True
                # Retry continue after country up to 3 times
                for attempt in range(3):
                    print(f"Attempt {attempt + 1}/3 to continue after country...")
                    if click_continue(page):
                        time.sleep(3)
                        offer = get_offer_amount(page)
                        print(f"Offer detected: {offer}")
                        break
                    else:
                        print("Continue failed after country, retrying...")
                        time.sleep(2)
                if not offer or offer == "$0":
                    print("Failed to get offer after retries.")
            else:
                print("Failed to select country")
                back_count_needed = 2  # Adjust back count since country failed
        else:
            print("Continue failed after eligibility")

    elif status == "already used":
        print("Already used → skipping offer")
    elif status == "not pixel":
        print("Not a Pixel device → staying on IMEI page")
    else:
        print(f"Unknown status: {status}")

    # Screenshot
    safe_name = f"{imei}_{status}_{offer.replace('$', '')}.png"
    try:
        page.screenshot(path=str(out_dir / safe_name), full_page=True)
    except:
        pass

    print(f"Result: {status} | Offer: {offer}")

    # === SMART BACK NAVIGATION ===
    print(f"Returning: {back_count_needed}× Back...")
    for _ in range(back_count_needed):
        # Retry back button up to 3 times
        for attempt in range(3):
            if click_back_button(page):
                break
            else:
                print(f"Back button attempt {attempt + 1}/3 failed, retrying...")
                time.sleep(1)
        else:
            print("Back button not found after 3 attempts")
            break
        time.sleep(1)

    # === ENSURE IMEI FIELD IS READY FOR NEXT ===
    time.sleep(1.5)
    imei_field = find_imei_field(page)
    if imei_field:
        try:
            imei_field.fill("")
            print("Cleared old IMEI")
        except:
            print("Failed to clear IMEI")
    else:
        print("IMEI field not found after navigation")

    return imei, status, offer


def remove_imei_from_csv(csv_path, imei_to_remove):
    """Remove the processed IMEI from the input CSV."""
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        
        # Filter out the processed IMEI
        updated_rows = [row for row in rows if row.get('imei', '').strip() != imei_to_remove]
        
        # Rewrite the CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if updated_rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(updated_rows)
            else:
                # If no rows left, just write header
                writer = csv.DictWriter(f, fieldnames=['imei'])
                writer.writeheader()
        print(f"Removed IMEI {imei_to_remove} from {csv_path}")
    except Exception as e:
        print(f"Error removing IMEI from CSV: {e}")


# ----------------------------------------------------------- 
# MAIN
# -----------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--csv", default="imeis.csv")
    ap.add_argument("--profile", default=PROFILE_DIR)
    ap.add_argument("--outdir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--results", default=DEFAULT_RESULTS)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.outdir)
    out_dir.mkdir(exist_ok=True)

    # Load IMEIs
    try:
        with open(args.csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            imeis = [row["imei"].strip() for row in reader if row.get("imei")]
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if not imeis:
        print("No IMEIs in CSV.")
        return

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=args.profile,
            headless=args.headless,
            viewport={"width": 1200, "height": 800},
            args=["--start-maximized"]
        )
        page = ctx.new_page()

        results_path = Path(args.results)
        file_exists = results_path.exists()

        with open(args.results, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not file_exists:
                w.writerow(["imei", "status", "offer_amount"])

            i = 0
            while i < len(imeis):
                imei = imeis[i]
                print(f"\n[{i+1}/{len(imeis)}] Checking {imei}")
                try:
                    imei_res, status, offer = process_imei(page, args.url, imei, out_dir)
                    w.writerow([imei_res, status, offer])
                    f.flush()
                    # Remove processed IMEI from input CSV
                    remove_imei_from_csv(args.csv, imei)
                    i += 1  # Move to next IMEI
                except RestartException:
                    print("Restarting browser due to IMEI field issue...")
                    try:
                        ctx.close()
                    except:
                        pass
                    # Relaunch context
                    ctx = p.chromium.launch_persistent_context(
                        user_data_dir=args.profile,
                        headless=args.headless,
                        viewport={"width": 1200, "height": 800},
                        args=["--start-maximized"]
                    )
                    page = ctx.new_page()
                    # Do not increment i, so it retries the same IMEI
                except KeyboardInterrupt:
                    print("\nStopped by user.")
                    break
                except Exception as e:
                    print(f"Error on {imei}: {e}")
                    w.writerow([imei, "error", "$0"])
                    f.flush()
                    # Still remove on error to avoid reprocessing
                    remove_imei_from_csv(args.csv, imei)
                    i += 1

        try:
            ctx.close()
        except:
            pass

    print("\nDONE – Smart navigation, no refresh, no captcha.")


if __name__ == "__main__":
    main()
