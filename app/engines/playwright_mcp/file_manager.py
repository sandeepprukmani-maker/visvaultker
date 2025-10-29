"""
File Manager for Playwright Test Agents
Manages specs/ and tests/ directories following Microsoft's Playwright Test Agents conventions
"""
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentFileManager:
    """
    Manages file system operations for Playwright Test Agents
    Follows Microsoft's conventions for specs/ and tests/ directories
    """
    
    def __init__(self, workspace_root: str = "."):
        """
        Initialize the file manager
        
        Args:
            workspace_root: Root directory for the workspace
        """
        self.workspace_root = Path(workspace_root)
        self.specs_dir = self.workspace_root / "specs"
        self.tests_dir = self.workspace_root / "tests"
        
    def initialize_directories(self) -> Dict[str, str]:
        """
        Initialize the required directory structure
        
        Returns:
            Dictionary with created directories
        """
        directories = {
            "specs": str(self.specs_dir),
            "tests": str(self.tests_dir)
        }
        
        for name, path_str in directories.items():
            path = Path(path_str)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directory ready: {path}")
        
        # Create .gitkeep files to ensure empty directories are tracked
        (self.specs_dir / ".gitkeep").touch(exist_ok=True)
        (self.tests_dir / ".gitkeep").touch(exist_ok=True)
        
        return directories
    
    def save_spec(self, spec_name: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a test plan spec to the specs/ directory
        
        Args:
            spec_name: Name for the spec file (without extension)
            content: Markdown content of the spec
            metadata: Optional metadata to include in the spec header
            
        Returns:
            Path to the saved spec file
        """
        # Sanitize filename
        safe_name = self._sanitize_filename(spec_name)
        spec_path = self.specs_dir / f"{safe_name}.md"
        
        # Add metadata header if provided
        if metadata:
            header = self._create_spec_header(metadata)
            full_content = f"{header}\n\n{content}"
        else:
            full_content = content
        
        spec_path.write_text(full_content, encoding='utf-8')
        logger.info(f"📝 Spec saved: {spec_path}")
        
        return str(spec_path)
    
    def save_test(self, test_name: str, content: str, spec_ref: Optional[str] = None, 
                  seed_ref: Optional[str] = None) -> str:
        """
        Save a test file to the tests/ directory
        
        Args:
            test_name: Name for the test file (without extension)
            content: Python test code
            spec_ref: Reference to the spec file that generated this test
            seed_ref: Reference to the seed test file
            
        Returns:
            Path to the saved test file
        """
        # Sanitize filename
        safe_name = self._sanitize_filename(test_name)
        test_path = self.tests_dir / f"{safe_name}.py"
        
        # Add metadata comments at the top
        header_lines = []
        if spec_ref:
            header_lines.append(f"# spec: {spec_ref}")
        if seed_ref:
            header_lines.append(f"# seed: {seed_ref}")
        
        if header_lines:
            full_content = "\n".join(header_lines) + "\n\n" + content
        else:
            full_content = content
        
        test_path.write_text(full_content, encoding='utf-8')
        logger.info(f"🎨 Test saved: {test_path}")
        
        return str(test_path)
    
    def read_spec(self, spec_name: str) -> Optional[str]:
        """
        Read a spec file from the specs/ directory
        
        Args:
            spec_name: Name of the spec file (with or without .md extension)
            
        Returns:
            Content of the spec file, or None if not found
        """
        spec_name = spec_name if spec_name.endswith('.md') else f"{spec_name}.md"
        spec_path = self.specs_dir / spec_name
        
        if spec_path.exists():
            return spec_path.read_text(encoding='utf-8')
        
        logger.warning(f"⚠️ Spec not found: {spec_path}")
        return None
    
    def read_test(self, test_name: str) -> Optional[str]:
        """
        Read a test file from the tests/ directory
        
        Args:
            test_name: Name of the test file (with or without .py extension)
            
        Returns:
            Content of the test file, or None if not found
        """
        test_name = test_name if test_name.endswith('.py') else f"{test_name}.py"
        test_path = self.tests_dir / test_name
        
        if test_path.exists():
            return test_path.read_text(encoding='utf-8')
        
        logger.warning(f"⚠️ Test not found: {test_path}")
        return None
    
    def list_specs(self) -> List[str]:
        """
        List all spec files in the specs/ directory
        
        Returns:
            List of spec file names
        """
        if not self.specs_dir.exists():
            return []
        
        specs = [f.name for f in self.specs_dir.glob("*.md") if f.name != ".gitkeep"]
        return sorted(specs)
    
    def list_tests(self) -> List[str]:
        """
        List all test files in the tests/ directory
        
        Returns:
            List of test file names
        """
        if not self.tests_dir.exists():
            return []
        
        tests = [f.name for f in self.tests_dir.glob("*.py") if f.name != ".gitkeep"]
        return sorted(tests)
    
    def create_seed_test(self, base_url: str, fixtures_path: str = "./fixtures") -> str:
        """
        Create a seed test file following Microsoft's conventions
        
        Args:
            base_url: Base URL of the application to test
            fixtures_path: Path to fixtures file (default: ./fixtures)
            
        Returns:
            Path to the created seed test
        """
        seed_content = f'''"""
Seed test for Playwright Test Agents
Provides a ready-to-use page context for test generation
"""
from playwright.sync_api import Page, expect


def test_seed(page: Page):
    """
    Seed test that sets up the environment for Playwright Test Agents
    
    This test:
    - Navigates to the application
    - Provides a ready-to-use page object
    - Serves as an example for generated tests
    """
    # Navigate to the application
    page.goto("{base_url}")
    
    # Wait for page to be ready
    page.wait_for_load_state("networkidle")
    
    # Basic verification
    expect(page).to_have_url("{base_url}")
'''
        
        seed_path = self.tests_dir / "seed.spec.py"
        seed_path.write_text(seed_content, encoding='utf-8')
        logger.info(f"🌱 Seed test created: {seed_path}")
        
        return str(seed_path)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to be filesystem-safe
        
        Args:
            filename: Raw filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace unsafe characters
        safe = filename.lower()
        safe = safe.replace(" ", "-")
        safe = safe.replace("_", "-")
        
        # Remove any non-alphanumeric characters except hyphens
        safe = "".join(c for c in safe if c.isalnum() or c == "-")
        
        # Remove consecutive hyphens
        while "--" in safe:
            safe = safe.replace("--", "-")
        
        # Remove leading/trailing hyphens
        safe = safe.strip("-")
        
        return safe or "unnamed"
    
    def _create_spec_header(self, metadata: Dict[str, Any]) -> str:
        """
        Create a metadata header for spec files
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Formatted header string
        """
        lines = ["<!--"]
        lines.append(f"Generated: {datetime.now().isoformat()}")
        
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")
        
        lines.append("-->")
        
        return "\n".join(lines)
    
    def get_workspace_structure(self) -> Dict[str, Any]:
        """
        Get the current workspace structure
        
        Returns:
            Dictionary describing the workspace structure
        """
        return {
            "workspace_root": str(self.workspace_root),
            "specs_dir": str(self.specs_dir),
            "tests_dir": str(self.tests_dir),
            "specs_count": len(self.list_specs()),
            "tests_count": len(self.list_tests()),
            "specs": self.list_specs(),
            "tests": self.list_tests()
        }
