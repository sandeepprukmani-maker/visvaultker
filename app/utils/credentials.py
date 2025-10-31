"""
Credential placeholder replacement utilities
"""
import re
import logging
from app.models import CredentialVault

logger = logging.getLogger(__name__)


def replace_credential_placeholders(instruction: str) -> tuple[str, list[str]]:
    """
    Replace credential placeholders in the instruction with actual values.
    
    Placeholders are in the format: {{credential_name}}
    
    Args:
        instruction: The instruction string that may contain placeholders
        
    Returns:
        Tuple of (processed_instruction, list_of_credentials_used)
        
    Example:
        Input: "Login with email user@example.com and password {{gmail_password}}"
        Output: ("Login with email user@example.com and password MyActualPassword123", ["gmail_password"])
    """
    # Pattern to match {{credential_name}}
    placeholder_pattern = r'\{\{([a-zA-Z0-9_]+)\}\}'
    
    # Find all placeholders
    placeholders = re.findall(placeholder_pattern, instruction)
    
    if not placeholders:
        return instruction, []
    
    processed_instruction = instruction
    credentials_used = []
    missing_credentials = []
    decryption_errors = []
    
    for credential_name in placeholders:
        # Fetch the credential from database
        credential = CredentialVault.query.filter_by(name=credential_name).first()
        
        if credential:
            try:
                # Get the decrypted value
                actual_value = credential.get_credential()
                
                # Replace the placeholder with the actual value
                placeholder = f"{{{{{credential_name}}}}}"
                processed_instruction = processed_instruction.replace(placeholder, actual_value)
                
                credentials_used.append(credential_name)
                logger.info(f"🔐 Replaced credential placeholder: {{{{{{credential_name}}}}}}")
                
            except ValueError as e:
                # Encryption key not set or invalid
                logger.error(f"Encryption error for credential '{credential_name}': {str(e)}")
                raise ValueError(
                    f"Cannot decrypt credentials: {str(e)} "
                    "Please set the ENCRYPTION_KEY environment variable or Replit Secret."
                )
            except Exception as e:
                logger.error(f"Failed to decrypt credential '{credential_name}': {str(e)}")
                decryption_errors.append(f"{credential_name}: {str(e)}")
        else:
            logger.warning(f"⚠️  Credential not found: {{{{{{credential_name}}}}}}")
            missing_credentials.append(credential_name)
    
    if decryption_errors:
        raise ValueError(
            f"Failed to decrypt credentials: {'; '.join(decryption_errors)}"
        )
    
    if missing_credentials:
        raise ValueError(
            f"Missing credentials: {', '.join(missing_credentials)}. "
            f"Please add these credentials in the Credentials page before using them in automations."
        )
    
    return processed_instruction, credentials_used


def has_credential_placeholders(instruction: str) -> bool:
    """
    Check if the instruction contains any credential placeholders.
    
    Args:
        instruction: The instruction string to check
        
    Returns:
        True if placeholders are found, False otherwise
    """
    placeholder_pattern = r'\{\{([a-zA-Z0-9_]+)\}\}'
    return bool(re.search(placeholder_pattern, instruction))


def extract_credential_names(instruction: str) -> list[str]:
    """
    Extract credential names from placeholders in the instruction.
    
    Args:
        instruction: The instruction string that may contain placeholders
        
    Returns:
        List of credential names found in placeholders
    """
    placeholder_pattern = r'\{\{([a-zA-Z0-9_]+)\}\}'
    return re.findall(placeholder_pattern, instruction)
