"""
Script Persistence Service
Manages storage and retrieval of generated and healed automation scripts
"""
import os
import logging
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ScriptPersistence:
    """
    Manages persistence of automation scripts
    
    Stores scripts in a local directory with metadata for tracking
    generated vs healed versions
    """
    
    def __init__(self, storage_dir: str = "automation_scripts"):
        """
        Initialize script persistence
        
        Args:
            storage_dir: Directory to store scripts
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.metadata_file = self.storage_dir / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}, starting fresh")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _generate_script_id(self, instruction: str) -> str:
        """
        Generate a unique ID for a script based on instruction
        
        Args:
            instruction: The automation instruction
            
        Returns:
            Unique script ID
        """
        # Create hash from instruction
        hash_obj = hashlib.md5(instruction.encode())
        return hash_obj.hexdigest()[:12]
    
    def save_generated_script(self, instruction: str, script: str, plan: Dict[str, Any]) -> str:
        """
        Save a generated script
        
        Args:
            instruction: The original instruction
            script: The generated Python script
            plan: The execution plan metadata
            
        Returns:
            Script ID
        """
        script_id = self._generate_script_id(instruction)
        script_path = self.storage_dir / f"{script_id}_generated.py"
        
        try:
            # Save script file
            with open(script_path, 'w') as f:
                f.write(script)
            
            # Update metadata
            self.metadata[script_id] = {
                'instruction': instruction,
                'generated_path': str(script_path),
                'healed_path': None,
                'plan': plan,
                'has_healed_version': False
            }
            self._save_metadata()
            
            logger.info(f"Saved generated script: {script_id}")
            return script_id
            
        except Exception as e:
            logger.error(f"Failed to save generated script: {e}")
            raise
    
    def save_healed_script(self, script_id: str, healed_script: str) -> bool:
        """
        Save a healed version of a script
        
        Args:
            script_id: The script ID
            healed_script: The healed Python script
            
        Returns:
            True if saved successfully
        """
        if script_id not in self.metadata:
            logger.warning(f"Script ID {script_id} not found in metadata")
            return False
        
        healed_path = self.storage_dir / f"{script_id}_healed.py"
        
        try:
            # Save healed script
            with open(healed_path, 'w') as f:
                f.write(healed_script)
            
            # Update metadata
            self.metadata[script_id]['healed_path'] = str(healed_path)
            self.metadata[script_id]['has_healed_version'] = True
            self._save_metadata()
            
            logger.info(f"Saved healed script: {script_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save healed script: {e}")
            return False
    
    def get_script(self, instruction: str) -> Optional[Dict[str, Any]]:
        """
        Get the best available script for an instruction
        
        Prefers healed version over generated version
        
        Args:
            instruction: The automation instruction
            
        Returns:
            Dictionary with script info or None if not found
        """
        script_id = self._generate_script_id(instruction)
        
        if script_id not in self.metadata:
            return None
        
        metadata = self.metadata[script_id]
        
        # Prefer healed version
        if metadata['has_healed_version'] and metadata['healed_path']:
            try:
                with open(metadata['healed_path'], 'r') as f:
                    script_content = f.read()
                return {
                    'script_id': script_id,
                    'script': script_content,
                    'type': 'healed',
                    'plan': metadata['plan']
                }
            except Exception as e:
                logger.warning(f"Failed to load healed script: {e}, falling back to generated")
        
        # Fallback to generated version
        if metadata['generated_path']:
            try:
                with open(metadata['generated_path'], 'r') as f:
                    script_content = f.read()
                return {
                    'script_id': script_id,
                    'script': script_content,
                    'type': 'generated',
                    'plan': metadata['plan']
                }
            except Exception as e:
                logger.error(f"Failed to load generated script: {e}")
                return None
        
        return None
    
    def get_script_by_id(self, script_id: str) -> Optional[Dict[str, Any]]:
        """
        Get script by ID
        
        Args:
            script_id: The script ID
            
        Returns:
            Dictionary with script info or None if not found
        """
        if script_id not in self.metadata:
            return None
        
        metadata = self.metadata[script_id]
        
        # Prefer healed version
        if metadata['has_healed_version'] and metadata['healed_path']:
            try:
                with open(metadata['healed_path'], 'r') as f:
                    script_content = f.read()
                return {
                    'script_id': script_id,
                    'script': script_content,
                    'type': 'healed',
                    'plan': metadata['plan']
                }
            except Exception as e:
                logger.warning(f"Failed to load healed script: {e}")
        
        # Fallback to generated
        if metadata['generated_path']:
            try:
                with open(metadata['generated_path'], 'r') as f:
                    script_content = f.read()
                return {
                    'script_id': script_id,
                    'script': script_content,
                    'type': 'generated',
                    'plan': metadata['plan']
                }
            except Exception as e:
                logger.error(f"Failed to load generated script: {e}")
        
        return None
    
    def list_scripts(self) -> list:
        """
        List all saved scripts
        
        Returns:
            List of script metadata
        """
        return [
            {
                'script_id': script_id,
                'instruction': metadata['instruction'],
                'has_healed_version': metadata['has_healed_version'],
                'scenario_name': metadata['plan'].get('scenario_name', 'Unknown')
            }
            for script_id, metadata in self.metadata.items()
        ]
