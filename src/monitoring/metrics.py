import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

class MetricsTracker:
    def __init__(self, metrics_path: str = "./data/metrics"):
        self.metrics_path = metrics_path
        os.makedirs(metrics_path, exist_ok=True)
        self.metrics_file = os.path.join(metrics_path, "metrics.json")
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict:
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        
        return {
            "crawls": [],
            "automations": [],
            "healings": [],
            "searches": [],
            "summary": {
                "total_crawls": 0,
                "total_automations": 0,
                "total_healings": 0,
                "total_searches": 0,
                "unique_templates": 0,
                "unique_urls_crawled": 0
            }
        }
    
    def _save_metrics(self):
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def record_crawl(self, url: str, success: bool, pages_crawled: int, 
                     templates_found: int, duration_seconds: float):
        self.metrics['crawls'].append({
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "success": success,
            "pages_crawled": pages_crawled,
            "templates_found": templates_found,
            "duration_seconds": duration_seconds
        })
        
        if success:
            self.metrics['summary']['total_crawls'] += 1
        
        self._save_metrics()
    
    def record_automation(self, task: str, success: bool, steps_total: int,
                         steps_completed: int, steps_failed: int, 
                         duration_seconds: float, healings_used: int = 0):
        self.metrics['automations'].append({
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "success": success,
            "steps_total": steps_total,
            "steps_completed": steps_completed,
            "steps_failed": steps_failed,
            "healings_used": healings_used,
            "duration_seconds": duration_seconds,
            "success_rate": steps_completed / steps_total if steps_total > 0 else 0
        })
        
        self.metrics['summary']['total_automations'] += 1
        self._save_metrics()
    
    def record_healing(self, original_selector: str, healed_selector: str,
                      confidence: float, success: bool):
        self.metrics['healings'].append({
            "timestamp": datetime.now().isoformat(),
            "original_selector": original_selector,
            "healed_selector": healed_selector,
            "confidence": confidence,
            "success": success
        })
        
        self.metrics['summary']['total_healings'] += 1
        self._save_metrics()
    
    def record_search(self, query: str, results_count: int, avg_similarity: float):
        self.metrics['searches'].append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "results_count": results_count,
            "avg_similarity": avg_similarity
        })
        
        self.metrics['summary']['total_searches'] += 1
        self._save_metrics()
    
    def get_success_rate(self, metric_type: str = "automations", 
                        time_window_hours: Optional[int] = None) -> float:
        if metric_type not in self.metrics:
            return 0.0
        
        records = self.metrics[metric_type]
        
        if time_window_hours:
            cutoff = datetime.now().timestamp() - (time_window_hours * 3600)
            records = [
                r for r in records 
                if datetime.fromisoformat(r['timestamp']).timestamp() > cutoff
            ]
        
        if not records:
            return 0.0
        
        successful = sum(1 for r in records if r.get('success', False))
        return successful / len(records)
    
    def get_healing_accuracy(self) -> float:
        if not self.metrics['healings']:
            return 0.0
        
        successful = sum(1 for h in self.metrics['healings'] if h['success'])
        return successful / len(self.metrics['healings'])
    
    def get_average_confidence(self) -> float:
        if not self.metrics['healings']:
            return 0.0
        
        total_confidence = sum(h['confidence'] for h in self.metrics['healings'])
        return total_confidence / len(self.metrics['healings'])
    
    def get_crawl_coverage(self) -> Dict:
        urls = set()
        for crawl in self.metrics['crawls']:
            if crawl['success']:
                urls.add(crawl['url'])
        
        return {
            "unique_urls_crawled": len(urls),
            "total_crawls": len(self.metrics['crawls']),
            "avg_pages_per_crawl": sum(c['pages_crawled'] for c in self.metrics['crawls']) / len(self.metrics['crawls']) if self.metrics['crawls'] else 0
        }
    
    def get_dashboard_data(self) -> Dict:
        return {
            "summary": self.metrics['summary'],
            "success_rates": {
                "crawls": self.get_success_rate("crawls"),
                "automations": self.get_success_rate("automations"),
                "automations_24h": self.get_success_rate("automations", 24)
            },
            "healing_metrics": {
                "total_healings": len(self.metrics['healings']),
                "healing_accuracy": self.get_healing_accuracy(),
                "average_confidence": self.get_average_confidence()
            },
            "coverage": self.get_crawl_coverage(),
            "recent_automations": self.metrics['automations'][-10:],
            "recent_crawls": self.metrics['crawls'][-10:],
            "recent_healings": self.metrics['healings'][-10:]
        }
    
    def get_time_series(self, metric_type: str, days: int = 7) -> List[Dict]:
        if metric_type not in self.metrics:
            return []
        
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        records = [
            r for r in self.metrics[metric_type]
            if datetime.fromisoformat(r['timestamp']).timestamp() > cutoff
        ]
        
        by_date = defaultdict(list)
        for record in records:
            date = datetime.fromisoformat(record['timestamp']).date().isoformat()
            by_date[date].append(record)
        
        time_series = []
        for date, day_records in sorted(by_date.items()):
            time_series.append({
                "date": date,
                "count": len(day_records),
                "success_count": sum(1 for r in day_records if r.get('success', False)),
                "success_rate": sum(1 for r in day_records if r.get('success', False)) / len(day_records)
            })
        
        return time_series
