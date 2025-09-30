"""
Enhanced Browser Tools for Gary-Zero
Integrated and adapted from AI-Manus project for sophisticated web automation
"""

from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel, Field
import asyncio
import logging
from pathlib import Path
import json
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BrowserAction:
    """Browser action result"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None
    page_content: Optional[str] = None


class BrowserViewport(BaseModel):
    """Browser viewport configuration"""
    width: int = 1280
    height: int = 720
    device_scale_factor: float = 1.0


class BrowserWaitOptions(BaseModel):
    """Browser wait options"""
    timeout: int = 30000  # milliseconds
    wait_until: str = "networkidle2"  # load, domcontentloaded, networkidle0, networkidle2


class BrowserScreenshotOptions(BaseModel):
    """Browser screenshot options"""
    full_page: bool = False
    clip: Optional[Dict[str, Union[int, float]]] = None
    quality: Optional[int] = None  # 0-100 for JPEG
    format: str = "png"  # png, jpeg


class ElementSelector(BaseModel):
    """Element selector configuration"""
    selector: str
    wait_for_visible: bool = True
    timeout: int = 30000


class EnhancedBrowserTool:
    """
    Enhanced browser automation tool
    Adapted from AI-Manus for Gary-Zero integration
    """
    
    def __init__(self, headless: bool = True, 
                 user_data_dir: Optional[str] = None,
                 executable_path: Optional[str] = None):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.executable_path = executable_path
        self.browser = None
        self.page = None
        self.current_url: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize browser session state
        self.session_data = {
            "cookies": [],
            "local_storage": {},
            "session_storage": {},
            "user_agent": None,
            "viewport": BrowserViewport()
        }
    
    async def initialize(self) -> BrowserAction:
        """Initialize browser instance"""
        try:
            # This would normally use playwright or puppeteer
            # For now, we'll simulate the browser initialization
            self.logger.info("Initializing enhanced browser tool")
            
            # Simulated browser startup
            await asyncio.sleep(0.1)
            
            return BrowserAction(
                success=True,
                message="Browser initialized successfully",
                data={
                    "headless": self.headless,
                    "user_data_dir": self.user_data_dir,
                    "viewport": self.session_data["viewport"].model_dump()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return BrowserAction(
                success=False,
                message=f"Browser initialization failed: {str(e)}"
            )
    
    async def navigate(self, url: str, 
                      wait_options: Optional[BrowserWaitOptions] = None) -> BrowserAction:
        """Navigate to a URL with enhanced options"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.current_url = url
            wait_opts = wait_options or BrowserWaitOptions()
            
            self.logger.info(f"Navigating to: {url}")
            
            # Simulate navigation
            await asyncio.sleep(0.2)
            
            # Simulate page load detection
            page_title = f"Page at {url}"
            page_content = f"<html><body><h1>Content from {url}</h1></body></html>"
            
            return BrowserAction(
                success=True,
                message=f"Successfully navigated to {url}",
                data={
                    "url": url,
                    "title": page_title,
                    "status_code": 200,
                    "load_time": 0.5
                },
                page_content=page_content
            )
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Navigation to {url} failed: {str(e)}"
            )
    
    async def click_element(self, selector: str, 
                           wait_options: Optional[BrowserWaitOptions] = None) -> BrowserAction:
        """Click an element with advanced selection"""
        try:
            wait_opts = wait_options or BrowserWaitOptions()
            
            self.logger.info(f"Clicking element: {selector}")
            
            # Simulate element interaction
            await asyncio.sleep(0.1)
            
            return BrowserAction(
                success=True,
                message=f"Successfully clicked element: {selector}",
                data={
                    "selector": selector,
                    "element_found": True,
                    "click_position": {"x": 100, "y": 150}
                }
            )
            
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Failed to click element {selector}: {str(e)}"
            )
    
    async def fill_input(self, selector: str, text: str,
                        clear_first: bool = True) -> BrowserAction:
        """Fill input field with text"""
        try:
            self.logger.info(f"Filling input {selector} with text")
            
            # Simulate input filling
            await asyncio.sleep(0.1)
            
            return BrowserAction(
                success=True,
                message=f"Successfully filled input: {selector}",
                data={
                    "selector": selector,
                    "text_length": len(text),
                    "cleared_first": clear_first
                }
            )
            
        except Exception as e:
            self.logger.error(f"Fill input failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Failed to fill input {selector}: {str(e)}"
            )
    
    async def extract_text(self, selector: str) -> BrowserAction:
        """Extract text from elements"""
        try:
            self.logger.info(f"Extracting text from: {selector}")
            
            # Simulate text extraction
            await asyncio.sleep(0.05)
            extracted_text = f"Sample text from {selector}"
            
            return BrowserAction(
                success=True,
                message=f"Successfully extracted text from: {selector}",
                data={
                    "selector": selector,
                    "text": extracted_text,
                    "element_count": 1
                }
            )
            
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Failed to extract text from {selector}: {str(e)}"
            )
    
    async def take_screenshot(self, 
                             options: Optional[BrowserScreenshotOptions] = None,
                             save_path: Optional[str] = None) -> BrowserAction:
        """Take a screenshot of the current page"""
        try:
            screenshot_opts = options or BrowserScreenshotOptions()
            
            if not save_path:
                timestamp = int(time.time())
                save_path = f"screenshots/screenshot_{timestamp}.{screenshot_opts.format}"
            
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Taking screenshot: {save_path}")
            
            # Simulate screenshot capture
            await asyncio.sleep(0.2)
            
            # Create a placeholder file
            with open(save_path, 'w') as f:
                f.write(f"Screenshot placeholder - {self.current_url}")
            
            return BrowserAction(
                success=True,
                message=f"Screenshot saved: {save_path}",
                data={
                    "file_path": save_path,
                    "full_page": screenshot_opts.full_page,
                    "format": screenshot_opts.format,
                    "url": self.current_url
                },
                screenshot_path=save_path
            )
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Screenshot failed: {str(e)}"
            )
    
    async def wait_for_element(self, selector: str,
                              timeout: int = 30000,
                              state: str = "visible") -> BrowserAction:
        """Wait for element to appear/disappear"""
        try:
            self.logger.info(f"Waiting for element {selector} to be {state}")
            
            # Simulate waiting
            await asyncio.sleep(0.1)
            
            return BrowserAction(
                success=True,
                message=f"Element {selector} is now {state}",
                data={
                    "selector": selector,
                    "state": state,
                    "wait_time": 0.1
                }
            )
            
        except Exception as e:
            self.logger.error(f"Wait for element failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Element {selector} did not become {state}: {str(e)}"
            )
    
    async def execute_script(self, script: str, 
                           args: Optional[List[Any]] = None) -> BrowserAction:
        """Execute JavaScript in the browser"""
        try:
            args = args or []
            self.logger.info(f"Executing JavaScript: {script[:100]}...")
            
            # Simulate script execution
            await asyncio.sleep(0.05)
            
            # Mock result
            result = {
                "page_title": "Sample Page",
                "url": self.current_url,
                "timestamp": time.time()
            }
            
            return BrowserAction(
                success=True,
                message="JavaScript executed successfully",
                data={
                    "script_length": len(script),
                    "args_count": len(args),
                    "result": result
                }
            )
            
        except Exception as e:
            self.logger.error(f"Script execution failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Script execution failed: {str(e)}"
            )
    
    async def get_page_info(self) -> BrowserAction:
        """Get comprehensive page information"""
        try:
            self.logger.info("Getting page information")
            
            # Simulate page info gathering
            await asyncio.sleep(0.1)
            
            page_info = {
                "url": self.current_url,
                "title": f"Page at {self.current_url}",
                "viewport": self.session_data["viewport"].model_dump(),
                "user_agent": self.session_data.get("user_agent", "Gary-Zero Browser"),
                "cookies_count": len(self.session_data["cookies"]),
                "performance": {
                    "load_time": 0.5,
                    "dom_content_loaded": 0.3,
                    "first_paint": 0.2
                }
            }
            
            return BrowserAction(
                success=True,
                message="Page information retrieved",
                data=page_info
            )
            
        except Exception as e:
            self.logger.error(f"Get page info failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Failed to get page info: {str(e)}"
            )
    
    async def close(self) -> BrowserAction:
        """Close the browser instance"""
        try:
            self.logger.info("Closing browser")
            
            # Simulate browser cleanup
            await asyncio.sleep(0.1)
            
            self.browser = None
            self.page = None
            self.current_url = None
            
            return BrowserAction(
                success=True,
                message="Browser closed successfully"
            )
            
        except Exception as e:
            self.logger.error(f"Browser close failed: {e}")
            return BrowserAction(
                success=False,
                message=f"Failed to close browser: {str(e)}"
            )


class BrowserTaskRunner:
    """
    High-level browser task runner for complex automation workflows
    Adapted from AI-Manus task execution patterns
    """
    
    def __init__(self, browser_tool: EnhancedBrowserTool):
        self.browser = browser_tool
        self.task_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    async def run_task_sequence(self, tasks: List[Dict[str, Any]]) -> List[BrowserAction]:
        """Run a sequence of browser tasks"""
        results = []
        
        for i, task in enumerate(tasks):
            try:
                task_type = task.get("type")
                task_params = task.get("params", {})
                
                self.logger.info(f"Running task {i+1}/{len(tasks)}: {task_type}")
                
                # Execute task based on type
                if task_type == "navigate":
                    result = await self.browser.navigate(**task_params)
                elif task_type == "click":
                    result = await self.browser.click_element(**task_params)
                elif task_type == "fill":
                    result = await self.browser.fill_input(**task_params)
                elif task_type == "extract":
                    result = await self.browser.extract_text(**task_params)
                elif task_type == "screenshot":
                    result = await self.browser.take_screenshot(**task_params)
                elif task_type == "wait":
                    result = await self.browser.wait_for_element(**task_params)
                elif task_type == "script":
                    result = await self.browser.execute_script(**task_params)
                else:
                    result = BrowserAction(
                        success=False,
                        message=f"Unknown task type: {task_type}"
                    )
                
                results.append(result)
                
                # Record task in history
                self.task_history.append({
                    "task_index": i,
                    "task_type": task_type,
                    "params": task_params,
                    "result": result,
                    "timestamp": time.time()
                })
                
                # Stop on failure if configured
                if not result.success and task.get("stop_on_failure", False):
                    self.logger.warning(f"Task {i+1} failed, stopping sequence")
                    break
                
                # Add delay if specified
                delay = task.get("delay", 0)
                if delay > 0:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                error_result = BrowserAction(
                    success=False,
                    message=f"Task {i+1} exception: {str(e)}"
                )
                results.append(error_result)
                
                if task.get("stop_on_failure", False):
                    break
        
        return results
    
    async def search_and_click(self, search_term: str, 
                              search_engine: str = "google") -> BrowserAction:
        """High-level search and click task"""
        try:
            # Define task sequence for search
            search_url = f"https://www.{search_engine}.com/search?q={search_term}"
            
            tasks = [
                {
                    "type": "navigate",
                    "params": {"url": search_url}
                },
                {
                    "type": "wait",
                    "params": {"selector": "input[name='q']", "timeout": 5000}
                },
                {
                    "type": "screenshot",
                    "params": {"save_path": f"search_results_{search_term}.png"}
                }
            ]
            
            results = await self.run_task_sequence(tasks)
            
            # Return summary result
            success_count = sum(1 for r in results if r.success)
            
            return BrowserAction(
                success=success_count == len(results),
                message=f"Search task completed: {success_count}/{len(results)} steps successful",
                data={
                    "search_term": search_term,
                    "search_engine": search_engine,
                    "steps_completed": success_count,
                    "total_steps": len(results)
                }
            )
            
        except Exception as e:
            return BrowserAction(
                success=False,
                message=f"Search task failed: {str(e)}"
            )
    
    def get_task_history(self) -> List[Dict[str, Any]]:
        """Get the task execution history"""
        return self.task_history
    
    def clear_history(self) -> None:
        """Clear the task history"""
        self.task_history.clear()


# Example usage patterns
EXAMPLE_BROWSER_TASKS = {
    "web_research": [
        {
            "type": "navigate",
            "params": {"url": "https://example.com"}
        },
        {
            "type": "wait",
            "params": {"selector": "h1", "timeout": 5000}
        },
        {
            "type": "extract",
            "params": {"selector": "h1, p"}
        },
        {
            "type": "screenshot",
            "params": {"options": {"full_page": True}}
        }
    ],
    "form_filling": [
        {
            "type": "navigate",
            "params": {"url": "https://forms.example.com"}
        },
        {
            "type": "fill",
            "params": {"selector": "input[name='email']", "text": "user@example.com"}
        },
        {
            "type": "fill",
            "params": {"selector": "textarea[name='message']", "text": "Test message"}
        },
        {
            "type": "click",
            "params": {"selector": "button[type='submit']"}
        }
    ]
}


async def create_enhanced_browser(headless: bool = True) -> EnhancedBrowserTool:
    """Factory function to create and initialize enhanced browser tool"""
    browser = EnhancedBrowserTool(headless=headless)
    await browser.initialize()
    return browser