"""
Seed dummy data for VisionVault database
"""
from sqlalchemy.orm import Session
from server.database import SessionLocal, init_db
from server.models import AutomationHistory
from datetime import datetime, timedelta
import json
import numpy as np
import random

def generate_dummy_embedding():
    """Generate a random 768-dimensional embedding vector"""
    return np.random.randn(768).tolist()

def create_dummy_records():
    init_db()
    db = SessionLocal()
    
    try:
        # Dummy record 1: Google Search
        record1 = AutomationHistory(
            prompt="Go to Google and search for 'web automation tools'",
            prompt_embedding=generate_dummy_embedding(),
            detected_url="https://www.google.com",
            mode="act",
            model="google/gemini-2.5-flash",
            success=True,
            session_id=f"session_{random.randint(10000, 99999)}",
            logs=[
                {
                    "id": "1",
                    "timestamp": 1699564800000,
                    "action": "navigate",
                    "status": "success",
                    "description": "Navigating to https://www.google.com"
                },
                {
                    "id": "2",
                    "timestamp": 1699564802000,
                    "action": "act",
                    "status": "success",
                    "selector": "xpath=//textarea[@name='q']",
                    "description": "Typing 'web automation tools' in search box"
                },
                {
                    "id": "3",
                    "timestamp": 1699564804000,
                    "action": "act",
                    "status": "success",
                    "selector": "xpath=//input[@name='btnK']",
                    "description": "Clicking search button"
                }
            ],
            generated_code={
                "locators": """import { chromium } from 'playwright';

async function runAutomation() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  await page.goto('https://www.google.com');
  await page.locator('xpath=//textarea[@name=\"q\"]').fill('web automation tools');
  await page.locator('xpath=//input[@name=\"btnK\"]').click();
  
  await browser.close();
}

runAutomation();"""
            },
            screenshot=None,
            error=None,
            created_at=datetime.utcnow() - timedelta(days=4)
        )
        
        # Dummy record 2: GitHub Login
        record2 = AutomationHistory(
            prompt="Navigate to GitHub and click the sign in button",
            prompt_embedding=generate_dummy_embedding(),
            detected_url="https://github.com",
            mode="act",
            model="google/gemini-2.5-flash",
            success=True,
            session_id=f"session_{random.randint(10000, 99999)}",
            logs=[
                {
                    "id": "1",
                    "timestamp": 1699564800000,
                    "action": "navigate",
                    "status": "success",
                    "description": "Navigating to https://github.com"
                },
                {
                    "id": "2",
                    "timestamp": 1699564802000,
                    "action": "act",
                    "status": "success",
                    "selector": "xpath=//a[contains(text(), 'Sign in')]",
                    "description": "Clicking sign in button"
                }
            ],
            generated_code={
                "locators": """import { chromium } from 'playwright';

async function runAutomation() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  await page.goto('https://github.com');
  await page.locator('xpath=//a[contains(text(), \"Sign in\")]').click();
  
  await browser.close();
}

runAutomation();"""
            },
            screenshot=None,
            error=None,
            created_at=datetime.utcnow() - timedelta(days=3)
        )
        
        # Dummy record 3: Amazon Product Search
        record3 = AutomationHistory(
            prompt="Search for 'wireless headphones' on Amazon",
            prompt_embedding=generate_dummy_embedding(),
            detected_url="https://www.amazon.com",
            mode="observe",
            model="google/gemini-2.5-flash",
            success=True,
            session_id=f"session_{random.randint(10000, 99999)}",
            logs=[
                {
                    "id": "1",
                    "timestamp": 1699564800000,
                    "action": "navigate",
                    "status": "success",
                    "description": "Navigating to https://www.amazon.com"
                },
                {
                    "id": "2",
                    "timestamp": 1699564802000,
                    "action": "observe",
                    "status": "success",
                    "selector": "xpath=//input[@id='twotabsearchtextbox']",
                    "description": "Found search input field"
                },
                {
                    "id": "3",
                    "timestamp": 1699564804000,
                    "action": "act",
                    "status": "success",
                    "selector": "xpath=//input[@id='twotabsearchtextbox']",
                    "description": "Typed search query"
                }
            ],
            generated_code={
                "locators": """import { chromium } from 'playwright';

async function runAutomation() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  await page.goto('https://www.amazon.com');
  const searchBox = await page.locator('xpath=//input[@id=\"twotabsearchtextbox\"]');
  await searchBox.fill('wireless headphones');
  
  await browser.close();
}

runAutomation();"""
            },
            screenshot=None,
            error=None,
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        
        # Dummy record 4: Failed automation
        record4 = AutomationHistory(
            prompt="Click the non-existent button on example.com",
            prompt_embedding=generate_dummy_embedding(),
            detected_url="https://example.com",
            mode="act",
            model="google/gemini-2.5-flash",
            success=False,
            session_id=f"session_{random.randint(10000, 99999)}",
            logs=[
                {
                    "id": "1",
                    "timestamp": 1699564800000,
                    "action": "navigate",
                    "status": "success",
                    "description": "Navigating to https://example.com"
                },
                {
                    "id": "2",
                    "timestamp": 1699564802000,
                    "action": "act",
                    "status": "error",
                    "description": "Failed to find element"
                }
            ],
            generated_code={
                "locators": "// Automation failed - no code generated"
            },
            screenshot=None,
            error="Element not found: Could not locate the specified button",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        
        # Dummy record 5: Wikipedia Extract
        record5 = AutomationHistory(
            prompt="Extract the main heading from Wikipedia homepage",
            prompt_embedding=generate_dummy_embedding(),
            detected_url="https://www.wikipedia.org",
            mode="extract",
            model="google/gemini-2.5-flash",
            success=True,
            session_id=f"session_{random.randint(10000, 99999)}",
            logs=[
                {
                    "id": "1",
                    "timestamp": 1699564800000,
                    "action": "navigate",
                    "status": "success",
                    "description": "Navigating to https://www.wikipedia.org"
                },
                {
                    "id": "2",
                    "timestamp": 1699564802000,
                    "action": "extract",
                    "status": "success",
                    "selector": "xpath=//h1",
                    "description": "Extracted main heading text"
                }
            ],
            generated_code={
                "locators": """import { chromium } from 'playwright';

async function runAutomation() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  await page.goto('https://www.wikipedia.org');
  const heading = await page.locator('xpath=//h1').textContent();
  console.log('Heading:', heading);
  
  await browser.close();
}

runAutomation();"""
            },
            screenshot=None,
            error=None,
            created_at=datetime.utcnow() - timedelta(hours=6)
        )
        
        # Add all records to database
        db.add_all([record1, record2, record3, record4, record5])
        db.commit()
        
        print("✅ Successfully added 5 dummy records to the database")
        print("\nRecords added:")
        print("1. Google Search - web automation tools")
        print("2. GitHub Sign In")
        print("3. Amazon Product Search")
        print("4. Failed automation on example.com")
        print("5. Wikipedia heading extraction")
        
    except Exception as e:
        print(f"❌ Error adding dummy data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_dummy_records()
