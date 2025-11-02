import asyncio
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pydantic import ValidationError
from models import InsertCrawlSession, InsertAutomation, InsertAutomationLog, InsertPage, InsertElement
from storage import storage
from crawler_service import crawler_service
from automation_service import automation_service
from openai_service import openai_service
import os
from urllib.parse import urlparse
import concurrent.futures

app = Flask(__name__, static_folder="../dist/public", static_url_path="")
CORS(app)

# Create a dedicated event loop for async operations
async_loop = None
async_thread = None

def start_async_loop():
    global async_loop
    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)
    async_loop.run_forever()

async_thread = threading.Thread(target=start_async_loop, daemon=True)
async_thread.start()

# Wait for loop to be ready
import time
while async_loop is None:
    time.sleep(0.01)

def run_async(coro):
    """Run async coroutine in the dedicated event loop"""
    future = asyncio.run_coroutine_threadsafe(coro, async_loop)
    return future.result()

def run_in_background(coro):
    """Submit async coroutine to run in background"""
    asyncio.run_coroutine_threadsafe(coro, async_loop)

@app.route("/api/crawl", methods=["POST"])
def create_crawl():
    try:
        data = InsertCrawlSession(**request.json)
        session = run_async(storage.create_crawl_session(data))
        
        async def background_crawl():
            try:
                await storage.update_crawl_session(session.id, {"status": "running"})
                
                pages_data = await crawler_service.crawl_website(data.url, {"depth": data.depth})

                for page_data in pages_data:
                    analysis = await openai_service.analyze_page({
                        "url": page_data["url"],
                        "title": page_data["title"],
                        "elements": page_data["elements"][:30]
                    })

                    page = await storage.create_page(InsertPage(
                        crawl_session_id=session.id,
                        url=page_data["url"],
                        title=page_data["title"] or analysis["pageType"],
                        element_count=len(page_data["elements"]),
                        screenshot=page_data["screenshot"],
                        template_hash=None,
                        template_group=None
                    ))

                    for element_data in page_data["elements"]:
                        embedding = None
                        if element_data.get("text") and len(element_data.get("text", "")) > 3:
                            try:
                                embedding_vector = await openai_service.generate_embedding(
                                    f"{element_data['tag']} {element_data['text']} {element_data['selector']}"
                                )
                                embedding = json.dumps(embedding_vector)
                            except Exception as error:
                                print(f"Error generating embedding: {error}")

                        await storage.create_element(InsertElement(
                            page_id=page.id,
                            tag=element_data["tag"],
                            selector=element_data["selector"],
                            text=element_data.get("text"),
                            attributes=element_data.get("attributes", {}),
                            xpath=element_data.get("xpath"),
                            confidence=100,
                            embedding=embedding
                        ))

                await storage.update_crawl_session(session.id, {
                    "status": "completed",
                    "pages_found": len(pages_data),
                    "elements_found": sum(len(p["elements"]) for p in pages_data),
                    "completed_at": datetime.now()
                })
            except Exception as error:
                print(f"Crawl error: {error}")
                await storage.update_crawl_session(session.id, {
                    "status": "failed",
                    "completed_at": datetime.now()
                })

        run_in_background(background_crawl())
        
        return jsonify(session.model_dump(by_alias=True)), 200
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400

@app.route("/api/crawl", methods=["GET"])
def get_crawls():
    sessions = run_async(storage.get_all_crawl_sessions())
    return jsonify([s.model_dump(by_alias=True) for s in sessions]), 200

@app.route("/api/crawl/<id>", methods=["GET"])
def get_crawl(id):
    session = run_async(storage.get_crawl_session(id))
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session.model_dump(by_alias=True)), 200

@app.route("/api/pages", methods=["GET"])
def get_pages():
    pages = run_async(storage.get_all_pages())
    return jsonify([p.model_dump(by_alias=True) for p in pages]), 200

@app.route("/api/pages/<id>", methods=["GET"])
def get_page(id):
    page = run_async(storage.get_page(id))
    if not page:
        return jsonify({"error": "Page not found"}), 404
    return jsonify(page.model_dump(by_alias=True)), 200

@app.route("/api/pages/<id>/elements", methods=["GET"])
def get_page_elements(id):
    elements = run_async(storage.get_elements_by_page(id))
    return jsonify([e.model_dump(by_alias=True) for e in elements]), 200

@app.route("/api/elements", methods=["GET"])
def search_elements():
    query = request.args.get("q", "")
    if query:
        elements = run_async(storage.search_elements(query))
        return jsonify([e.model_dump(by_alias=True) for e in elements]), 200
    return jsonify([]), 200

@app.route("/api/automations", methods=["POST"])
def create_automation():
    try:
        data = InsertAutomation(**request.json)
        automation = run_async(storage.create_automation(data))
        
        async def background_automation():
            try:
                await storage.update_automation(automation.id, {"status": "running"})
                
                pages = await storage.get_all_pages()
                pages_with_elements = []
                for page in pages[:10]:
                    elements = await storage.get_elements_by_page(page.id)
                    pages_with_elements.append({
                        "url": page.url,
                        "title": page.title,
                        "pageType": page.title,
                        "elements": [{"tag": e.tag, "text": e.text, "selector": e.selector} for e in elements[:20]]
                    })

                plan = await openai_service.generate_automation_plan(data.command, pages_with_elements)
                await storage.update_automation(automation.id, {"plan": plan})

                base_url = urlparse(pages[0].url).scheme + "://" + urlparse(pages[0].url).netloc if pages else None
                result = await automation_service.execute_automation(automation.id, plan["steps"], {"baseUrl": base_url})

                for log in result["logs"]:
                    await storage.create_automation_log(InsertAutomationLog(**log))

                await storage.update_automation(automation.id, {
                    "status": "success" if result["success"] else "error",
                    "result": result,
                    "duration": result["duration"],
                    "action_count": len(plan["steps"]),
                    "completed_at": datetime.now()
                })
            except Exception as error:
                print(f"Automation error: {error}")
                await storage.update_automation(automation.id, {
                    "status": "error",
                    "result": {"error": str(error)},
                    "completed_at": datetime.now()
                })

        run_in_background(background_automation())
        
        return jsonify(automation.model_dump(by_alias=True)), 200
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400

@app.route("/api/automations", methods=["GET"])
def get_automations():
    automations = run_async(storage.get_all_automations())
    return jsonify([a.model_dump(by_alias=True) for a in automations]), 200

@app.route("/api/automations/<id>", methods=["GET"])
def get_automation(id):
    automation = run_async(storage.get_automation(id))
    if not automation:
        return jsonify({"error": "Automation not found"}), 404
    return jsonify(automation.model_dump(by_alias=True)), 200

@app.route("/api/automations/<id>/logs", methods=["GET"])
def get_automation_logs(id):
    logs = run_async(storage.get_automation_logs(id))
    return jsonify([l.model_dump(by_alias=True) for l in logs]), 200

@app.route("/api/stats", methods=["GET"])
def get_stats():
    pages = run_async(storage.get_all_pages())
    automations = run_async(storage.get_all_automations())
    sessions = run_async(storage.get_all_crawl_sessions())
    
    successful_automations = sum(1 for a in automations if a.status == "success")
    total_automations = sum(1 for a in automations if a.status != "queued")
    success_rate = f"{(successful_automations / total_automations * 100):.1f}" if total_automations > 0 else "0.0"

    total_elements = sum(p.element_count for p in pages)

    return jsonify({
        "pagesCrawled": len(pages),
        "elementsIndexed": total_elements,
        "automationsRun": len(automations),
        "successRate": f"{success_rate}%",
        "crawlSessions": len(sessions)
    }), 200

@app.route("/api/settings", methods=["GET"])
def get_settings():
    settings = run_async(storage.get_settings())
    return jsonify(settings.to_dict()), 200

@app.route("/api/settings", methods=["POST"])
def update_settings():
    try:
        settings = run_async(storage.update_settings(request.json))
        return jsonify(settings.to_dict()), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 400

@app.route("/api/visual/analyze-screenshot", methods=["POST"])
def analyze_screenshot():
    try:
        data = request.json
        screenshot = data.get("screenshot")
        query = data.get("query")
        if not screenshot:
            return jsonify({"error": "Screenshot required"}), 400
        analysis = run_async(openai_service.analyze_screenshot(screenshot, query))
        return jsonify(analysis), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@app.route("/api/visual/compare-screenshots", methods=["POST"])
def compare_screenshots():
    try:
        data = request.json
        screenshot1 = data.get("screenshot1")
        screenshot2 = data.get("screenshot2")
        if not screenshot1 or not screenshot2:
            return jsonify({"error": "Both screenshots required"}), 400
        comparison = run_async(openai_service.compare_screenshots(screenshot1, screenshot2))
        return jsonify(comparison), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@app.route("/api/visual/find-element", methods=["POST"])
def find_element():
    try:
        data = request.json
        screenshot = data.get("screenshot")
        description = data.get("description")
        if not screenshot or not description:
            return jsonify({"error": "Screenshot and description required"}), 400
        location = run_async(openai_service.find_element_by_visual(screenshot, description))
        return jsonify({"location": location}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@app.route("/api/visual/generate-selectors", methods=["POST"])
def generate_selectors():
    try:
        data = request.json
        element_description = data.get("elementDescription")
        page_url = data.get("pageUrl")
        if not element_description or not page_url:
            return jsonify({"error": "Element description and page URL required"}), 400
        
        pages = run_async(storage.get_all_pages())
        target_page = next((p for p in pages if p.url == page_url), None)
        if not target_page:
            return jsonify({"error": "Page not found"}), 404
        
        elements = run_async(storage.get_elements_by_page(target_page.id))
        selectors = run_async(openai_service.generate_smart_selectors(element_description, {
            "url": page_url,
            "elements": [{"tag": e.tag, "text": e.text, "attributes": e.attributes} for e in elements]
        }))
        
        return jsonify(selectors), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
