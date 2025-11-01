import asyncio
from typing import Dict, List
from datetime import datetime, timedelta
import json
import os

class AutoUpdater:
    def __init__(self, 
                 crawler,
                 template_detector,
                 embedder,
                 version_tracker,
                 update_interval_hours: int = 24):
        self.crawler = crawler
        self.template_detector = template_detector
        self.embedder = embedder
        self.version_tracker = version_tracker
        self.update_interval = timedelta(hours=update_interval_hours)
        self.schedule_path = "./data/update_schedule.json"
        self.schedule = self._load_schedule()
        self.running = False
    
    def _load_schedule(self) -> Dict:
        if os.path.exists(self.schedule_path):
            with open(self.schedule_path, 'r') as f:
                return json.load(f)
        return {"urls": {}}
    
    def _save_schedule(self):
        os.makedirs(os.path.dirname(self.schedule_path), exist_ok=True)
        with open(self.schedule_path, 'w') as f:
            json.dump(self.schedule, f, indent=2)
    
    def add_url_to_schedule(self, url: str, interval_hours: int = None):
        interval = interval_hours if interval_hours else self.update_interval.total_seconds() / 3600
        
        self.schedule['urls'][url] = {
            "url": url,
            "interval_hours": interval,
            "last_crawled": None,
            "next_crawl": datetime.now().isoformat(),
            "crawl_count": 0,
            "auto_update_enabled": True
        }
        self._save_schedule()
    
    def remove_url_from_schedule(self, url: str):
        if url in self.schedule['urls']:
            del self.schedule['urls'][url]
            self._save_schedule()
    
    async def check_and_update(self, url: str) -> Dict:
        url_config = self.schedule['urls'].get(url)
        if not url_config or not url_config['auto_update_enabled']:
            return {"status": "skipped", "reason": "not enabled"}
        
        next_crawl = datetime.fromisoformat(url_config['next_crawl'])
        if datetime.now() < next_crawl:
            return {"status": "skipped", "reason": "not due yet"}
        
        try:
            pages = await self.crawler.crawl_url(url, depth=1)
            
            if not pages:
                return {"status": "failed", "reason": "no pages crawled"}
            
            page_data = pages[0]
            
            version_id = self.version_tracker.save_crawl_version(url, page_data)
            
            latest_version = self.version_tracker.get_latest_version(url)
            
            if latest_version:
                version_history = self.version_tracker.get_version_history(url)
                
                if len(version_history) >= 2:
                    prev_version_id = version_history[-2]['version_id']
                    current_version_id = version_history[-1]['version_id']
                    
                    changes = self.version_tracker.compare_versions(
                        url,
                        prev_version_id,
                        current_version_id
                    )
                    
                    if not changes.get('error') and (changes.get('structure_changed') or changes.get('summary', {}).get('total_added', 0) > 0):
                        template_id = self.template_detector.detect_template(
                            page_data['dom_structure'],
                            page_data['url']
                        )
                        
                        added_elements = changes.get('elements_added', [])
                        modified_elements = [e['new'] for e in changes.get('elements_modified', [])]
                        
                        elements_to_reindex = added_elements + modified_elements
                        
                        if elements_to_reindex:
                            self.embedder.index_page_elements(
                                template_id,
                                elements_to_reindex,
                                page_data['url']
                            )
            
            url_config['last_crawled'] = datetime.now().isoformat()
            url_config['next_crawl'] = (
                datetime.now() + timedelta(hours=url_config['interval_hours'])
            ).isoformat()
            url_config['crawl_count'] += 1
            self._save_schedule()
            
            return {
                "status": "success",
                "url": url,
                "version_id": version_id,
                "changes_detected": latest_version is not None,
                "next_crawl": url_config['next_crawl']
            }
        
        except Exception as e:
            return {"status": "failed", "reason": str(e)}
    
    async def run_scheduler(self):
        self.running = True
        
        while self.running:
            for url in list(self.schedule['urls'].keys()):
                result = await self.check_and_update(url)
                print(f"Auto-update for {url}: {result['status']}")
            
            await asyncio.sleep(3600)
    
    def stop_scheduler(self):
        self.running = False
    
    def get_schedule_status(self) -> Dict:
        status = {
            "scheduler_running": self.running,
            "tracked_urls": len(self.schedule['urls']),
            "urls": []
        }
        
        for url, config in self.schedule['urls'].items():
            status['urls'].append({
                "url": url,
                "enabled": config['auto_update_enabled'],
                "last_crawled": config['last_crawled'],
                "next_crawl": config['next_crawl'],
                "crawl_count": config['crawl_count']
            })
        
        return status
