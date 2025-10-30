"""
Secure Credential Manager
Fetches credentials from database and keeps them hidden from AI models
"""
import os
import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Import at module level to avoid circular imports
_db_imported = False
_SiteCredential = None

def _get_site_credential_model():
    """Lazy import of SiteCredential model to avoid circular imports"""
    global _db_imported, _SiteCredential
    if not _db_imported:
        try:
            from app.models import SiteCredential
            _SiteCredential = SiteCredential
            _db_imported = True
        except ImportError:
            pass
    return _SiteCredential


class CredentialManager:
    """
    Manages secure credential handling for browser automation
    
    Features:
    - Fetches credentials from environment variables
    - Redacts credentials from prompts sent to AI models
    - Injects real credentials during automation execution
    """
    
    def __init__(self):
        """Initialize credential manager"""
        self.credential_patterns = {
            'smarh': {
                'username_env': 'SMARH_USERNAME',
                'password_env': 'SMARH_PASSWORD',
                'keywords': ['smarh', 'smar-h']
            },
            'generic': {
                'username_env': 'AUTO_USERNAME',
                'password_env': 'AUTO_PASSWORD',
                'keywords': ['login', 'sign in', 'log in']
            }
        }
        
        logger.info("🔐 Credential Manager initialized")
    
    def detect_credential_request(self, instruction: str) -> Optional[str]:
        """
        Detect if the instruction requires credentials
        
        Args:
            instruction: User's automation instruction
            
        Returns:
            Service name if credentials are needed, None otherwise
        """
        instruction_lower = instruction.lower()
        
        for service, config in self.credential_patterns.items():
            if any(keyword in instruction_lower for keyword in config['keywords']):
                return service
        
        return None
    
    def get_credentials(self, service: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Fetch credentials from database or environment variables
        
        Args:
            service: Service name (e.g., 'smarh', 'generic')
            
        Returns:
            Tuple of (username, password, url) or (None, None, None) if not found
        """
        # First try to get from database
        SiteCredential = _get_site_credential_model()
        if SiteCredential:
            try:
                cred = SiteCredential.query.filter_by(site_name=service.lower()).first()
                if not cred:
                    # Try matching keywords
                    all_creds = SiteCredential.query.all()
                    for c in all_creds:
                        if c.keywords:
                            keywords = [k.strip().lower() for k in c.keywords.split(',')]
                            if service.lower() in keywords:
                                cred = c
                                break
                
                if cred:
                    logger.info(f"🔐 Credentials found in database for {service} (username: {cred.username[:3]}***)")
                    return cred.username, cred.get_password(), cred.url
            except Exception as e:
                logger.error(f"Error fetching credentials from database: {e}")
        
        # Fallback to environment variables (legacy support)
        if service not in self.credential_patterns:
            logger.warning(f"⚠️  Unknown service: {service}")
            return None, None, None
        
        config = self.credential_patterns[service]
        username = os.environ.get(config['username_env'])
        password = os.environ.get(config['password_env'])
        
        if username and password:
            logger.info(f"🔐 Credentials found in environment for {service} (username: {username[:3]}***)")
            return username, password, None
        else:
            missing = []
            if not username:
                missing.append(config['username_env'])
            if not password:
                missing.append(config['password_env'])
            
            logger.warning(f"⚠️  Missing credentials for {service}: {', '.join(missing)}")
            return None, None, None
    
    def redact_instruction(self, instruction: str, service: str) -> str:
        """
        Redact sensitive credential information from instruction
        
        Args:
            instruction: Original instruction
            service: Service name
            
        Returns:
            Instruction with credentials redacted
        """
        username, password = self.get_credentials(service)
        
        if not username or not password:
            return instruction
        
        redacted = instruction
        
        # Replace actual credentials if they appear in the instruction
        redacted = redacted.replace(username, '[USERNAME_FROM_ENV]')
        redacted = redacted.replace(password, '[PASSWORD_FROM_ENV]')
        
        return redacted
    
    def prepare_secure_instruction(self, instruction: str) -> Tuple[str, Dict]:
        """
        Prepare instruction for AI model with credentials redacted
        
        Args:
            instruction: Original user instruction
            
        Returns:
            Tuple of (redacted_instruction, credential_context)
        """
        service = self.detect_credential_request(instruction)
        
        if not service:
            return instruction, {}
        
        username, password, url = self.get_credentials(service)
        
        if not username or not password:
            logger.warning(f"⚠️  Credentials not available for {service}")
            return instruction, {}
        
        # Redact the instruction
        redacted_instruction = self.redact_instruction(instruction, service)
        
        # Create credential context for injection during execution
        credential_context = {
            'service': service,
            'username': username,
            'password': password,
            'url': url,
            'original_instruction': instruction,
            'redacted_instruction': redacted_instruction
        }
        
        # Enhance the instruction with credential injection guidance
        # If we have a URL, include navigation instruction
        if url:
            enhanced_instruction = f"""Navigate to {url} and {redacted_instruction}

CREDENTIAL INJECTION (SECURE MODE):
- URL: {url} (will navigate automatically)
- Username will be automatically filled from secure storage
- Password will be automatically filled from secure storage
- DO NOT ask for credentials
- DO NOT display credentials in any output
- Proceed with the automation using the provided credentials"""
        else:
            enhanced_instruction = f"""{redacted_instruction}

CREDENTIAL INJECTION (SECURE MODE):
- Username will be automatically filled from secure storage
- Password will be automatically filled from secure storage
- DO NOT ask for credentials
- DO NOT display credentials in any output
- Proceed with the automation using the provided credentials"""
        
        logger.info(f"🔐 Instruction prepared with secure credential injection for {service}")
        if url:
            logger.info(f"🌐 Auto-navigation to: {url}")
        
        return enhanced_instruction, credential_context
    
    def add_custom_service(self, service_name: str, username_env: str, password_env: str, keywords: list):
        """
        Add a custom service configuration
        
        Args:
            service_name: Name of the service (e.g., 'github', 'aws')
            username_env: Environment variable name for username
            password_env: Environment variable name for password
            keywords: Keywords to detect in instructions
        """
        self.credential_patterns[service_name] = {
            'username_env': username_env,
            'password_env': password_env,
            'keywords': keywords
        }
        
        logger.info(f"🔐 Added custom service: {service_name}")
    
    def get_credential_instructions(self) -> str:
        """
        Get instructions for setting up credentials
        
        Returns:
            Formatted string with setup instructions
        """
        instructions = ["🔐 CREDENTIAL SETUP INSTRUCTIONS", "=" * 60]
        
        for service, config in self.credential_patterns.items():
            instructions.append(f"\n{service.upper()}:")
            instructions.append(f"  • Set {config['username_env']}=<your_username> in .env")
            instructions.append(f"  • Set {config['password_env']}=<your_password> in .env")
            instructions.append(f"  • Keywords: {', '.join(config['keywords'])}")
        
        instructions.append("\n" + "=" * 60)
        instructions.append("After setting credentials in .env, restart the application.")
        
        return "\n".join(instructions)


# Global credential manager instance
credential_manager = CredentialManager()
