import asyncio
from playwright.async_api import async_playwright
import time
import base64

class DeltamathAutomator:
    def __init__(self, credentials, socketio=None):
        self.credentials = credentials
        self.url = "https://www.deltamath.com/"
        self.socketio = socketio

    def log(self, message, type='system'):
        if self.socketio:
            self.socketio.emit('log', {'message': message, 'type': type})
        print(f"[Automation] {message}")

    async def update_preview(self, page):
        if self.socketio:
            screenshot = await page.screenshot()
            b64_shot = base64.b64encode(screenshot).decode('utf-8')
            self.socketio.emit('browser_update', {'status': 'RUNNING', 'screenshot': b64_shot})

    async def login_and_complete(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            self.log(f"Navigating to {self.url}...")
            await page.goto(self.url)
            await self.update_preview(page)
            
            try:
                # Deltamath login: Look for login button or fields
                # This is a refined heuristic approach
                login_btn = page.get_by_text("Login", exact=False)
                if await login_btn.is_visible():
                    await login_btn.click()
                
                self.log("Entering credentials...")
                # Adjusting to likely selectors based on common patterns
                await page.fill("input[type='email'], input[name='username']", self.credentials['username'])
                await page.fill("input[type='password']", self.credentials['password'])
                await self.update_preview(page)
                
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
                
                self.log("Login submitted. Checking status...")
                await self.update_preview(page)
                
                # Further assignment logic would go here
                self.log("Reached dashboard. Scanning for assignments...")
                
            except Exception as e:
                self.log(f"Automation error: {e}", type='error')
            finally:
                await browser.close()
                if self.socketio:
                    self.socketio.emit('browser_update', {'status': 'COMPLETED'})

def run_automation(creds, socketio):
    automator = DeltamathAutomator(creds, socketio)
    asyncio.run(automator.login_and_complete())
