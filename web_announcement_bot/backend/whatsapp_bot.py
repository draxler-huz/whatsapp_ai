import os
import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Playwright, BrowserContext, Page

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "whatsapp_session"))

class WhatsAppBot:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._lock = asyncio.Lock()

    async def _init_browser(self):
        """Initializes Playwright persistent browser context if not already active."""
        os.makedirs(SESSION_DIR, exist_ok=True)
        if self.playwright is None:
            self.playwright = await async_playwright().start()

        is_alive = False
        if self.context is not None:
            try:
                # Test if browser context is still connected
                if len(self.context.pages) > 0 and not self.context.pages[0].is_closed():
                    is_alive = True
            except Exception:
                is_alive = False

        if not is_alive:
            # Clean up stale locks if any from previous unclean exits
            for lock_name in ["SingletonLock", "lockfile"]:
                lock_path = os.path.join(SESSION_DIR, lock_name)
                if os.path.exists(lock_path):
                    try:
                        os.remove(lock_path)
                    except Exception:
                        pass

            launch_kwargs = {
                "user_data_dir": SESSION_DIR,
                "headless": False,
                "args": [
                    "--new-window",
                    "--start-maximized",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled"
                ]
            }

            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            chrome_x86 = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

            browser_context = None
            if os.path.exists(chrome_path) or os.path.exists(chrome_x86):
                try:
                    print("[WhatsApp Bot] Launching with system Google Chrome...")
                    browser_context = await self.playwright.chromium.launch_persistent_context(
                        **launch_kwargs, channel="chrome"
                    )
                except Exception as e:
                    print(f"[WhatsApp Bot] Notice: Chrome channel launch fallback: {e}")

            if browser_context is None and os.path.exists(edge_path):
                try:
                    print("[WhatsApp Bot] Launching with system Microsoft Edge...")
                    browser_context = await self.playwright.chromium.launch_persistent_context(
                        **launch_kwargs, channel="msedge"
                    )
                except Exception as e:
                    print(f"[WhatsApp Bot] Notice: Edge channel launch fallback: {e}")

            if browser_context is None:
                print("[WhatsApp Bot] Launching default Playwright Chromium...")
                browser_context = await self.playwright.chromium.launch_persistent_context(**launch_kwargs)

            self.context = browser_context
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

            # Navigate to WhatsApp Web using domcontentloaded so it renders immediately
            print("[WhatsApp Bot] Navigating to WhatsApp Web...")
            try:
                await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)
                await self.page.bring_to_front()
            except Exception as e:
                print(f"[WhatsApp Bot] Notice on navigation: {e}")

    async def open_whatsapp(self) -> Dict[str, str]:
        """
        Step 1: Opens the WhatsApp Web browser window so user can scan QR code
        or reconnect existing session.
        """
        async with self._lock:
            await self._init_browser()
            status = await self._check_login_state_fast()
            return {
                "status": status,
                "message": "WhatsApp is open. Please scan the QR code if prompted." if status == "waiting_qr" else "WhatsApp is logged in and ready!"
            }

    async def get_status(self) -> Dict[str, str]:
        """Returns the current connection and login status of WhatsApp Web."""
        if self.page is None or self.page.is_closed():
            return {"status": "disconnected", "message": "Browser is not currently open."}
        try:
            status = await self._check_login_state_fast()
            return {
                "status": status,
                "message": "Logged in" if status == "logged_in" else "Waiting for QR code scan" if status == "waiting_qr" else "Loading WhatsApp Web..."
            }
        except Exception as e:
            return {"status": "disconnected", "message": str(e)}

    async def _check_login_state_fast(self) -> str:
        """Quickly checks whether the chat list is visible or QR canvas is displayed."""
        if self.page is None:
            return "disconnected"
        
        try:
            # Check for chat list / search bar (logged in)
            is_logged_in = await self.page.locator(
                'div[contenteditable="true"][data-tab="3"], #side, div[data-testid="chat-list"]'
            ).first.is_visible(timeout=2500)
            if is_logged_in:
                return "logged_in"
        except Exception:
            pass

        try:
            # Check for QR code canvas or landing container
            has_qr = await self.page.locator('canvas, div[data-ref], [data-testid="qrcode"]').first.is_visible(timeout=2000)
            if has_qr:
                return "waiting_qr"
        except Exception:
            pass

        return "loading"

    async def fetch_groups(self) -> List[str]:
        """
        Step 2: Scrapes visible chat/group names from the WhatsApp sidebar.
        """
        async with self._lock:
            await self._init_browser()

            # Wait for chat list to be ready
            try:
                await self.page.wait_for_selector(
                    'div[contenteditable="true"][data-tab="3"], #side, div[data-testid="chat-list"]',
                    timeout=30000
                )
            except Exception:
                raise TimeoutError("WhatsApp is not logged in yet. Please scan the QR code in the browser window.")

            # Give a brief moment for chats to render
            await self.page.wait_for_timeout(1500)

            # Extract chat titles from #pane-side with slight scroll to capture more
            groups_script = """
            async () => {
                const uniqueTitles = new Set();
                const pane = document.querySelector('#pane-side');

                function harvest() {
                    const elements = document.querySelectorAll('#pane-side span[title], div[data-testid="chat-list"] span[title]');
                    elements.forEach(el => {
                        const title = el.getAttribute('title');
                        if (title && title.trim().length > 0) {
                            // Filter out timestamps, system badges, or empty strings
                            if (!title.match(/^\\d{1,2}:\\d{2}$/) && !title.includes('unread message')) {
                                uniqueTitles.add(title.trim());
                            }
                        }
                    });
                }

                harvest();
                if (pane) {
                    // Scroll down slightly to load more items
                    pane.scrollTop = 400;
                    await new Promise(r => setTimeout(r, 600));
                    harvest();
                    pane.scrollTop = 800;
                    await new Promise(r => setTimeout(r, 600));
                    harvest();
                    pane.scrollTop = 0; // return to top
                }

                return Array.from(uniqueTitles);
            }
            """
            try:
                groups = await self.page.evaluate(groups_script)
                print(f"[WhatsApp Bot] Harvested {len(groups)} chats/groups from sidebar.")
                return groups
            except Exception as e:
                print(f"[WhatsApp Bot] Failed harvesting groups: {e}")
                return []

    async def broadcast_announcement(self, group_names: List[str], message: str) -> Dict[str, str]:
        """
        Step 4: Sends formatted announcement to specified groups.
        """
        async with self._lock:
            await self._init_browser()

            # Verify session is ready
            try:
                await self.page.wait_for_selector(
                    'div[contenteditable="true"][data-tab="3"], #side, div[data-testid="chat-list"]',
                    timeout=60000
                )
            except Exception:
                raise TimeoutError("WhatsApp login timed out. Please scan the QR code first.")

            results = {}
            for group in group_names:
                group_name = group.strip()
                if not group_name:
                    continue

                print(f"\n[WhatsApp Bot] Broadcasting to group: '{group_name}'...")
                try:
                    # 1. Locate search box
                    search_box = self.page.locator('div[contenteditable="true"][data-tab="3"], div[data-testid="chat-list-search"]').first
                    await search_box.click()
                    await self.page.wait_for_timeout(200)

                    # Clear search box
                    await self.page.keyboard.press("Control+A")
                    await self.page.keyboard.press("Backspace")
                    await self.page.wait_for_timeout(150)

                    # Type target group name
                    await self.page.keyboard.insert_text(group_name)
                    await self.page.wait_for_timeout(2000)

                    # 2. Select group from search results
                    escaped_name = group_name.replace('"', '\\"')
                    group_chat = self.page.locator(f'span[title="{escaped_name}"]').first
                    if await group_chat.count() == 0:
                        group_chat = self.page.locator(f'span:text-is("{escaped_name}")').first
                    if await group_chat.count() == 0:
                        group_chat = self.page.locator(f'#pane-side span[title*="{escaped_name}"]').first

                    if await group_chat.count() == 0:
                        raise ValueError(f"Group '{group_name}' not found in search results.")

                    await group_chat.click()
                    await self.page.wait_for_timeout(1500)

                    # 3. Locate message box
                    message_box = self.page.locator('footer div[contenteditable="true"], div[contenteditable="true"][data-tab="10"]').last
                    await message_box.click()
                    await self.page.wait_for_timeout(300)

                    # 4. Insert lines safely with emojis
                    lines = message.split('\n')
                    for i, line in enumerate(lines):
                        if line:
                            await self.page.keyboard.insert_text(line)
                        if i < len(lines) - 1:
                            await self.page.keyboard.press("Shift+Enter")
                        await self.page.wait_for_timeout(20)

                    await self.page.wait_for_timeout(400)
                    await self.page.keyboard.press("Enter")
                    await self.page.wait_for_timeout(2500)

                    results[group_name] = "Success"
                    print(f"[WhatsApp Bot] Delivered successfully to '{group_name}'.")

                except Exception as e:
                    err_msg = str(e)
                    print(f"[WhatsApp Bot] Delivery failed for '{group_name}': {err_msg}")
                    results[group_name] = f"Failed: {err_msg}"

            # Clear search
            try:
                await self.page.keyboard.press("Escape")
                await self.page.wait_for_timeout(300)
                await self.page.keyboard.press("Escape")
            except Exception:
                pass

            return results

    async def close(self):
        """Closes browser session."""
        async with self._lock:
            if self.context:
                await self.context.close()
                self.context = None
                self.page = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

# Global bot instance
bot_instance = WhatsAppBot()

# Helper function for backward compatibility
async def send_to_multiple_groups(group_names: List[str], message: str) -> Dict[str, str]:
    return await bot_instance.broadcast_announcement(group_names, message)
