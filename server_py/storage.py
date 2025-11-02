from typing import Optional, Protocol
from models import (
    CrawlSession, InsertCrawlSession,
    Page, InsertPage,
    Element, InsertElement,
    Automation, InsertAutomation,
    AutomationLog, InsertAutomationLog
)
from datetime import datetime
import threading

class AppSettings:
    def __init__(self):
        self.api_key: Optional[str] = None
        self.auto_screenshots: bool = True
        self.template_detection: bool = True
        self.parallel_crawling: bool = True
        self.self_healing: bool = True
        self.learning_from_failures: bool = True

    def to_dict(self):
        return {
            "apiKey": self.api_key,
            "autoScreenshots": self.auto_screenshots,
            "templateDetection": self.template_detection,
            "parallelCrawling": self.parallel_crawling,
            "selfHealing": self.self_healing,
            "learningFromFailures": self.learning_from_failures
        }

class IStorage(Protocol):
    async def create_crawl_session(self, session: InsertCrawlSession) -> CrawlSession: ...
    async def get_crawl_session(self, id: str) -> Optional[CrawlSession]: ...
    async def update_crawl_session(self, id: str, updates: dict) -> Optional[CrawlSession]: ...
    async def get_all_crawl_sessions(self) -> list[CrawlSession]: ...
    
    async def create_page(self, page: InsertPage) -> Page: ...
    async def get_page(self, id: str) -> Optional[Page]: ...
    async def get_pages_by_session(self, session_id: str) -> list[Page]: ...
    async def get_all_pages(self) -> list[Page]: ...
    
    async def create_element(self, element: InsertElement) -> Element: ...
    async def get_element(self, id: str) -> Optional[Element]: ...
    async def get_elements_by_page(self, page_id: str) -> list[Element]: ...
    async def search_elements(self, query: str) -> list[Element]: ...
    
    async def create_automation(self, automation: InsertAutomation) -> Automation: ...
    async def get_automation(self, id: str) -> Optional[Automation]: ...
    async def update_automation(self, id: str, updates: dict) -> Optional[Automation]: ...
    async def get_all_automations(self) -> list[Automation]: ...
    
    async def create_automation_log(self, log: InsertAutomationLog) -> AutomationLog: ...
    async def get_automation_logs(self, automation_id: str) -> list[AutomationLog]: ...
    
    async def get_settings(self) -> AppSettings: ...
    async def update_settings(self, settings: dict) -> AppSettings: ...

class MemStorage:
    def __init__(self):
        self._lock = threading.RLock()
        self.crawl_sessions: dict[str, CrawlSession] = {}
        self.pages: dict[str, Page] = {}
        self.elements: dict[str, Element] = {}
        self.automations: dict[str, Automation] = {}
        self.automation_logs: dict[str, AutomationLog] = {}
        self.settings = AppSettings()

    async def create_crawl_session(self, insert_session: InsertCrawlSession) -> CrawlSession:
        with self._lock:
            session = CrawlSession(
                url=insert_session.url,
                depth=insert_session.depth,
                status="pending",
                pages_found=0,
                elements_found=0,
                started_at=datetime.now(),
                completed_at=None
            )
            self.crawl_sessions[session.id] = session
            return session

    async def get_crawl_session(self, id: str) -> Optional[CrawlSession]:
        with self._lock:
            return self.crawl_sessions.get(id)

    async def update_crawl_session(self, id: str, updates: dict) -> Optional[CrawlSession]:
        with self._lock:
            session = self.crawl_sessions.get(id)
            if not session:
                return None
            
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            self.crawl_sessions[id] = session
            return session

    async def get_all_crawl_sessions(self) -> list[CrawlSession]:
        with self._lock:
            return sorted(
                self.crawl_sessions.values(),
                key=lambda x: x.started_at,
                reverse=True
            )

    async def create_page(self, insert_page: InsertPage) -> Page:
        with self._lock:
            page = Page(
                crawl_session_id=insert_page.crawl_session_id,
                url=insert_page.url,
                title=insert_page.title,
                element_count=insert_page.element_count or 0,
                screenshot=insert_page.screenshot,
                template_hash=insert_page.template_hash,
                template_group=insert_page.template_group,
                crawled_at=datetime.now()
            )
            self.pages[page.id] = page
            return page

    async def get_page(self, id: str) -> Optional[Page]:
        with self._lock:
            return self.pages.get(id)

    async def get_pages_by_session(self, session_id: str) -> list[Page]:
        with self._lock:
            return [p for p in self.pages.values() if p.crawl_session_id == session_id]

    async def get_all_pages(self) -> list[Page]:
        with self._lock:
            return sorted(
                self.pages.values(),
                key=lambda x: x.crawled_at,
                reverse=True
            )

    async def create_element(self, insert_element: InsertElement) -> Element:
        with self._lock:
            element = Element(
                page_id=insert_element.page_id,
                tag=insert_element.tag,
                selector=insert_element.selector,
                text=insert_element.text,
                attributes=insert_element.attributes or {},
                xpath=insert_element.xpath,
                confidence=insert_element.confidence or 100,
                embedding=insert_element.embedding
            )
            self.elements[element.id] = element
            return element

    async def get_element(self, id: str) -> Optional[Element]:
        with self._lock:
            return self.elements.get(id)

    async def get_elements_by_page(self, page_id: str) -> list[Element]:
        with self._lock:
            return [e for e in self.elements.values() if e.page_id == page_id]

    async def search_elements(self, query: str) -> list[Element]:
        with self._lock:
            lower_query = query.lower()
            return [
                e for e in self.elements.values()
                if lower_query in e.tag.lower()
                or lower_query in e.selector.lower()
                or (e.text and lower_query in e.text.lower())
            ]

    async def create_automation(self, insert_automation: InsertAutomation) -> Automation:
        with self._lock:
            automation = Automation(
                command=insert_automation.command,
                status="queued",
                plan=insert_automation.plan,
                result=insert_automation.result,
                duration=None,
                action_count=0,
                created_at=datetime.now(),
                completed_at=None
            )
            self.automations[automation.id] = automation
            return automation

    async def get_automation(self, id: str) -> Optional[Automation]:
        with self._lock:
            return self.automations.get(id)

    async def update_automation(self, id: str, updates: dict) -> Optional[Automation]:
        with self._lock:
            automation = self.automations.get(id)
            if not automation:
                return None
            
            for key, value in updates.items():
                if hasattr(automation, key):
                    setattr(automation, key, value)
            
            self.automations[id] = automation
            return automation

    async def get_all_automations(self) -> list[Automation]:
        with self._lock:
            return sorted(
                self.automations.values(),
                key=lambda x: x.created_at,
                reverse=True
            )

    async def create_automation_log(self, insert_log: InsertAutomationLog) -> AutomationLog:
        with self._lock:
            log = AutomationLog(
                automation_id=insert_log.automation_id,
                timestamp=datetime.now(),
                action=insert_log.action,
                status=insert_log.status,
                details=insert_log.details,
                screenshot=insert_log.screenshot
            )
            self.automation_logs[log.id] = log
            return log

    async def get_automation_logs(self, automation_id: str) -> list[AutomationLog]:
        with self._lock:
            return sorted(
                [log for log in self.automation_logs.values() if log.automation_id == automation_id],
                key=lambda x: x.timestamp
            )

    async def get_settings(self) -> AppSettings:
        with self._lock:
            return self.settings

    async def update_settings(self, updates: dict) -> AppSettings:
        with self._lock:
            if "apiKey" in updates:
                self.settings.api_key = updates["apiKey"]
            if "autoScreenshots" in updates:
                self.settings.auto_screenshots = updates["autoScreenshots"]
            if "templateDetection" in updates:
                self.settings.template_detection = updates["templateDetection"]
            if "parallelCrawling" in updates:
                self.settings.parallel_crawling = updates["parallelCrawling"]
            if "selfHealing" in updates:
                self.settings.self_healing = updates["selfHealing"]
            if "learningFromFailures" in updates:
                self.settings.learning_from_failures = updates["learningFromFailures"]
            return self.settings

storage = MemStorage()
