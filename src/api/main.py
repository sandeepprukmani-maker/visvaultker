from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import sys
import time
from datetime import datetime

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from config import config
from src.crawler.crawler import WebCrawler
from src.templates.template_detector import TemplateDetector
from src.templates.version_tracker import VersionTracker
from src.embeddings.embedder import ElementEmbedder
from src.embeddings.semantic_labeler import SemanticLabeler
from src.planner.context_retriever import ContextRetriever
from src.planner.action_planner import ActionPlanner
from src.executor.runner import AutomationRunner
from src.executor.self_healer import SelfHealer
from src.scheduler.auto_update import AutoUpdater
from src.monitoring.metrics import MetricsTracker
from src.optimization.cache import EmbeddingCache
from src.optimization.rate_limiter import RateLimitMiddleware
from src.optimization.async_client import run_sync_in_async
from src.agents.planner_agent import PlannerAgent
from src.agents.generator_agent import GeneratorAgent
from src.agents.healer_agent import HealerAgent
from src.agents.agentic_loop import AgenticLoop

app = FastAPI(
    title="Self-Learning UI Automation Engine",
    description="An AI-powered web automation system that learns from web UIs and heals itself",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

app.mount("/static", StaticFiles(directory="static"), name="static")

crawler = None
template_detector = None
version_tracker = None
embedder = None
labeler = None
context_retriever = None
action_planner = None
automation_runner = None
self_healer = None
auto_updater = None
metrics_tracker = None
embedding_cache = None
planner_agent = None
generator_agent = None
healer_agent = None
agentic_loop = None


def initialize_components():
    global crawler, template_detector, version_tracker, embedder, labeler
    global context_retriever, action_planner, automation_runner, self_healer
    global auto_updater, metrics_tracker, embedding_cache
    global planner_agent, generator_agent, healer_agent, agentic_loop

    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Note: Some endpoints will not work without OPENAI_API_KEY")
        return

    if not config.OPENAI_API_KEY:
        print("OPENAI_API_KEY not configured")
        return

    embedding_cache = EmbeddingCache()
    metrics_tracker = MetricsTracker()
    version_tracker = VersionTracker()

    crawler = WebCrawler(config.SCREENSHOTS_PATH)
    template_detector = TemplateDetector(config.TEMPLATES_PATH)
    embedder = ElementEmbedder(config.OPENAI_API_KEY, config.VECTOR_DB_PATH, cache=embedding_cache)
    labeler = SemanticLabeler(config.OPENAI_API_KEY)
    context_retriever = ContextRetriever(embedder)
    action_planner = ActionPlanner(config.OPENAI_API_KEY)
    automation_runner = AutomationRunner(config.SCREENSHOTS_PATH)
    self_healer = SelfHealer(embedder, enable_vision=True, vision_threshold=0.75)
    auto_updater = AutoUpdater(crawler, template_detector, embedder, version_tracker)

    # Initialize Playwright-inspired test agents
    from openai import OpenAI
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    planner_agent = PlannerAgent(crawler, embedder, labeler, openai_client)
    generator_agent = GeneratorAgent(context_retriever, openai_client, crawler)
    healer_agent = HealerAgent(automation_runner, self_healer, openai_client)
    agentic_loop = AgenticLoop(planner_agent, generator_agent, healer_agent)


class CrawlRequest(BaseModel):
    url: str
    depth: int = 1
    save_version: bool = True


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class RunAutomationRequest(BaseModel):
    task: str
    start_url: Optional[str] = None
    context_limit: int = 10
    enable_vision: bool = True
    vision_threshold: float = 0.75


class ScheduleRequest(BaseModel):
    url: str
    interval_hours: int = 24


class PlannerRequest(BaseModel):
    url: str
    scenarios: List[str]
    seed_context: Optional[Dict] = None
    prd: Optional[str] = None


class GeneratorRequest(BaseModel):
    spec_filename: str
    seed_url: Optional[str] = None
    verify_selectors: bool = True


class HealerRequest(BaseModel):
    test_filename: str
    max_heal_attempts: int = 3
    confidence_threshold: float = 0.75
    enable_vision: bool = True
    vision_threshold: float = 0.75


class AgenticLoopRequest(BaseModel):
    url: str
    scenarios: List[str]
    seed_context: Optional[Dict] = None
    prd: Optional[str] = None
    max_heal_attempts: int = 3
    confidence_threshold: float = 0.75


@app.on_event("startup")
async def startup_event():
    initialize_components()


@app.get("/")
async def home():
    """Serve the web UI"""
    return FileResponse("static/index.html")


@app.get("/api")
async def api_root():
    """API documentation endpoint"""
    return {
        "message": "Self-Learning UI Automation Engine v3.0 - Enhanced with Playwright Test Agents",
        "status": "running",
        "features": [
            "crawling", "templates", "embeddings", "automation", "self-healing",
            "versioning", "monitoring", "auto-updates",
            "🎭 planner-agent", "🎭 generator-agent", "🎭 healer-agent", "🎭 agentic-loop"
        ],
        "endpoints": {
            "crawl": "POST /crawl",
            "templates": "GET /templates",
            "search": "POST /search",
            "run": "POST /run",
            "versions": "GET /versions/{url}",
            "metrics": "GET /metrics/dashboard",
            "schedule": "POST /schedule",
            "cache": "GET /cache/stats",
            "health": "GET /health",
            "agents": {
                "planner": "POST /agents/plan - Generate test plans",
                "generator": "POST /agents/generate - Generate executable tests",
                "healer": "POST /agents/heal - Run tests with healing",
                "loop": "POST /agents/loop - Run full agentic loop",
                "list_specs": "GET /agents/specs - List all specs",
                "list_tests": "GET /agents/tests - List all tests",
                "list_reports": "GET /agents/reports - List all healing reports"
            }
        }
    }


@app.get("/health")
async def health_check():
    api_key_configured = bool(config.OPENAI_API_KEY)

    components_status = {
        "crawler": crawler is not None,
        "template_detector": template_detector is not None,
        "version_tracker": version_tracker is not None,
        "embedder": embedder is not None,
        "labeler": labeler is not None,
        "metrics_tracker": metrics_tracker is not None,
        "embedding_cache": embedding_cache is not None,
        "auto_updater": auto_updater is not None
    }

    all_initialized = all(components_status.values())

    return {
        "status": "healthy" if (api_key_configured and all_initialized) else "degraded",
        "openai_configured": api_key_configured,
        "components": components_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/crawl")
async def crawl_url(request: CrawlRequest):
    if not crawler:
        raise HTTPException(status_code=500, detail="Crawler not initialized. Check OPENAI_API_KEY configuration.")

    start_time = time.time()

    try:
        pages = await crawler.crawl_url(request.url, request.depth)

        results = []
        for page_data in pages:
            if not template_detector:
                raise HTTPException(status_code=500, detail="Template detector not initialized")

            template_id = template_detector.detect_template(
                page_data['dom_structure'],
                page_data['url']
            )

            if request.save_version and version_tracker:
                version_id = version_tracker.save_crawl_version(page_data['url'], page_data)

            if embedder and page_data.get('elements'):
                await run_sync_in_async(
                    embedder.index_page_elements,
                    template_id,
                    page_data['elements'],
                    page_data['url']
                )

            semantic_label = None
            if labeler:
                semantic_label = await run_sync_in_async(
                    labeler.label_template,
                    page_data['dom_structure'],
                    page_data['url']
                )

            results.append({
                "url": page_data['url'],
                "template_id": template_id,
                "structure_hash": page_data['structure_hash'],
                "screenshot": page_data['screenshot'],
                "elements_count": len(page_data.get('elements', [])),
                "semantic_label": semantic_label,
                "version_id": version_id if request.save_version and version_tracker else None
            })

        duration = time.time() - start_time
        template_count = template_detector.get_unique_template_count() if template_detector else 0

        if metrics_tracker:
            metrics_tracker.record_crawl(
                request.url,
                True,
                len(pages),
                template_count,
                duration
            )

        return {
            "status": "success",
            "pages_crawled": len(pages),
            "unique_templates": template_count,
            "duration_seconds": duration,
            "results": results
        }

    except Exception as e:
        if metrics_tracker:
            metrics_tracker.record_crawl(request.url, False, 0, 0, time.time() - start_time)
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")


@app.get("/templates")
async def get_templates():
    if not template_detector:
        raise HTTPException(status_code=500, detail="Template detector not initialized")

    templates = template_detector.get_all_templates()

    summary = []
    for template_id, template_data in templates.items():
        summary.append({
            "template_id": template_id,
            "match_count": template_data.get('match_count', 0),
            "urls": template_data.get('urls', [])
        })

    return {
        "total_templates": len(templates),
        "templates": summary
    }


@app.get("/templates/{template_id}")
async def get_template(template_id: str):
    if not template_detector:
        raise HTTPException(status_code=500, detail="Template detector not initialized")

    template = template_detector.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@app.post("/search")
async def search_elements(request: SearchRequest):
    if not context_retriever:
        raise HTTPException(status_code=500, detail="Search not available. Check OPENAI_API_KEY configuration.")

    try:
        results = await run_sync_in_async(
            context_retriever.retrieve_context,
            request.query,
            request.top_k
        )

        avg_similarity = sum(r['similarity'] for r in results) / len(results) if results else 0

        if metrics_tracker:
            metrics_tracker.record_search(request.query, len(results), avg_similarity)

        return {
            "query": request.query,
            "results_count": len(results),
            "avg_similarity": avg_similarity,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/run")
async def run_automation(request: RunAutomationRequest):
    if not all([context_retriever, action_planner, automation_runner]):
        raise HTTPException(status_code=500, detail="Automation not available. Check OPENAI_API_KEY configuration.")

    start_time = time.time()

    try:
        if not context_retriever:
            raise HTTPException(status_code=500, detail="Context retriever not initialized")
        if not action_planner:
            raise HTTPException(status_code=500, detail="Action planner not initialized")
        if not automation_runner:
            raise HTTPException(status_code=500, detail="Automation runner not initialized")

        context = await run_sync_in_async(
            context_retriever.retrieve_context,
            request.task,
            request.context_limit
        )

        plan = await run_sync_in_async(
            action_planner.generate_plan,
            request.task,
            context
        )

        execution_results = await automation_runner.execute_plan(plan, request.start_url)

        duration = time.time() - start_time

        if metrics_tracker:
            metrics_tracker.record_automation(
                request.task,
                execution_results['status'] == 'success',
                len(plan),
                execution_results['steps_completed'],
                execution_results['steps_failed'],
                duration
            )

        return {
            "status": "success",
            "task": request.task,
            "context_items": len(context),
            "plan_steps": len(plan),
            "plan": plan,
            "execution": execution_results,
            "duration_seconds": duration
        }

    except Exception as e:
        if metrics_tracker:
            metrics_tracker.record_automation(request.task, False, 0, 0, 0, time.time() - start_time)
        raise HTTPException(status_code=500, detail=f"Automation failed: {str(e)}")


@app.get("/versions")
async def get_all_versions():
    if not version_tracker:
        raise HTTPException(status_code=500, detail="Version tracker not initialized")

    urls = version_tracker.get_all_tracked_urls()

    return {
        "tracked_urls": len(urls),
        "urls": urls
    }


@app.get("/versions/{url:path}")
async def get_version_history(url: str):
    if not version_tracker:
        raise HTTPException(status_code=500, detail="Version tracker not initialized")

    history = version_tracker.get_version_history(url)

    return {
        "url": url,
        "versions_count": len(history),
        "versions": history
    }


@app.get("/versions/{url:path}/compare")
async def compare_versions(url: str, v1: str, v2: str):
    if not version_tracker:
        raise HTTPException(status_code=500, detail="Version tracker not initialized")

    changes = version_tracker.compare_versions(url, v1, v2)

    return changes


@app.get("/metrics/dashboard")
async def get_dashboard():
    if not metrics_tracker:
        raise HTTPException(status_code=500, detail="Metrics tracker not initialized")

    return metrics_tracker.get_dashboard_data()


@app.get("/metrics/timeseries/{metric_type}")
async def get_timeseries(metric_type: str, days: int = 7):
    if not metrics_tracker:
        raise HTTPException(status_code=500, detail="Metrics tracker not initialized")

    if metric_type not in ['crawls', 'automations', 'healings', 'searches']:
        raise HTTPException(status_code=400, detail="Invalid metric type")

    return metrics_tracker.get_time_series(metric_type, days)


@app.post("/schedule")
async def add_to_schedule(request: ScheduleRequest):
    if not auto_updater:
        raise HTTPException(status_code=500, detail="Auto updater not initialized")

    auto_updater.add_url_to_schedule(request.url, request.interval_hours)

    return {
        "status": "success",
        "url": request.url,
        "interval_hours": request.interval_hours,
        "message": "URL added to auto-update schedule"
    }


@app.delete("/schedule/{url:path}")
async def remove_from_schedule(url: str):
    if not auto_updater:
        raise HTTPException(status_code=500, detail="Auto updater not initialized")

    auto_updater.remove_url_from_schedule(url)

    return {
        "status": "success",
        "url": url,
        "message": "URL removed from auto-update schedule"
    }


@app.get("/schedule/status")
async def get_schedule_status():
    if not auto_updater:
        raise HTTPException(status_code=500, detail="Auto updater not initialized")

    return auto_updater.get_schedule_status()


@app.get("/cache/stats")
async def get_cache_stats():
    if not embedding_cache:
        raise HTTPException(status_code=500, detail="Cache not initialized")

    return embedding_cache.get_stats()


@app.post("/cache/clear")
async def clear_cache():
    if not embedding_cache:
        raise HTTPException(status_code=500, detail="Cache not initialized")

    embedding_cache.flush()

    return {
        "status": "success",
        "message": "Cache cleared successfully"
    }


@app.post("/cache/cleanup")
async def cleanup_cache():
    if not embedding_cache:
        raise HTTPException(status_code=500, detail="Cache not initialized")

    expired_count = embedding_cache.clear_expired()

    return {
        "status": "success",
        "expired_entries_removed": expired_count
    }


@app.post("/agents/plan")
async def run_planner(request: PlannerRequest):
    """🎭 Planner Agent - Explore app and generate test plan"""
    if not planner_agent:
        raise HTTPException(status_code=500, detail="Planner agent not initialized")

    try:
        result = await planner_agent.explore_and_plan(
            url=request.url,
            scenarios=request.scenarios,
            seed_context=request.seed_context,
            prd=request.prd
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/generate")
async def run_generator(request: GeneratorRequest):
    """🎭 Generator Agent - Convert spec to executable tests"""
    if not generator_agent:
        raise HTTPException(status_code=500, detail="Generator agent not initialized")

    try:
        # Read the spec
        spec_content = planner_agent.get_spec(request.spec_filename)
        if not spec_content:
            raise HTTPException(status_code=404, detail=f"Spec not found: {request.spec_filename}")

        result = await generator_agent.generate_from_spec(
            spec_content=spec_content,
            spec_filename=request.spec_filename,
            seed_url=request.seed_url,
            verify_selectors=request.verify_selectors
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/heal")
async def run_healer(request: HealerRequest):
    """🎭 Healer Agent - Run tests with automatic healing"""
    if not healer_agent:
        raise HTTPException(status_code=500, detail="Healer agent not initialized")

    try:
        # Read the test suite
        test_suite = generator_agent.get_test(request.test_filename)
        if not test_suite:
            raise HTTPException(status_code=404, detail=f"Test suite not found: {request.test_filename}")

        result = await healer_agent.heal_and_run(
            test_suite=test_suite,
            max_heal_attempts=request.max_heal_attempts,
            confidence_threshold=request.confidence_threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/loop")
async def run_agentic_loop(request: AgenticLoopRequest):
    """🎭 Agentic Loop - Run full planner → generator → healer pipeline"""
    if not agentic_loop:
        raise HTTPException(status_code=500, detail="Agentic loop not initialized")

    try:
        result = await agentic_loop.run_full_loop(
            url=request.url,
            scenarios=request.scenarios,
            seed_context=request.seed_context,
            prd=request.prd,
            max_heal_attempts=request.max_heal_attempts,
            confidence_threshold=request.confidence_threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/specs")
async def list_specs():
    """List all generated test specifications"""
    if not planner_agent:
        raise HTTPException(status_code=500, detail="Planner agent not initialized")

    return {"specs": planner_agent.list_specs()}


@app.get("/agents/tests")
async def list_tests():
    """List all generated test suites"""
    if not generator_agent:
        raise HTTPException(status_code=500, detail="Generator agent not initialized")

    return {"tests": generator_agent.list_tests()}


@app.get("/agents/reports")
async def list_reports():
    """List all healing reports"""
    if not healer_agent:
        raise HTTPException(status_code=500, detail="Healer agent not initialized")

    return {"reports": healer_agent.list_reports()}


@app.get("/agents/specs/{filename}")
async def get_spec(filename: str):
    """Get a specific test specification"""
    if not planner_agent:
        raise HTTPException(status_code=500, detail="Planner agent not initialized")

    spec_content = planner_agent.get_spec(filename)
    if not spec_content:
        raise HTTPException(status_code=404, detail=f"Spec not found: {filename}")

    return {"filename": filename, "content": spec_content}


@app.get("/agents/tests/{filename}")
async def get_test(filename: str):
    """Get a specific test suite"""
    if not generator_agent:
        raise HTTPException(status_code=500, detail="Generator agent not initialized")

    test_suite = generator_agent.get_test(filename)
    if not test_suite:
        raise HTTPException(status_code=404, detail=f"Test suite not found: {filename}")

    return test_suite


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
