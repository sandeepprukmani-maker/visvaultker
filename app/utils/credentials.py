"""
Credential placeholder replacement utilities
"""
import re
import logging
from flask import has_app_context
from app.models import CredentialVault

logger = logging.getLogger(__name__)


def replace_credential_placeholders(instruction: str) -> tuple[str, list[str]]:
    """
    Replace credential placeholders in the instruction with actual values.
    Also detect credential names mentioned in the instruction and inject URL, username, and password.
    
    Supports two modes:
    1. Placeholder format: {{credential_name}} - replaces with password only (legacy mode)
    2. Natural language: "log in to gmail" - injects URL, username, and password
    
    Args:
        instruction: The instruction string that may contain placeholders or credential names
        
    Returns:
        Tuple of (processed_instruction, list_of_credentials_used)
        
    Example:
        Input: "log in to gmail"
        Output: ("Go to https://mail.google.com and log in with username user@gmail.com and password MyActualPassword123", ["gmail"])
    """
    processed_instruction = instruction
    credentials_used = []
    missing_credentials = []
    decryption_errors = []
    
    # Check for app context before database operations
    if not has_app_context():
        logger.warning("⚠️ No Flask app context - skipping credential replacement")
        return instruction, []
    
    # Get all credentials from database
    all_credentials = CredentialVault.query.all()
    
    # First, handle placeholder format {{credential_name}}
    placeholder_pattern = r'\{\{([a-zA-Z0-9_]+)\}\}'
    placeholders = re.findall(placeholder_pattern, instruction)
    
    for credential_name in placeholders:
        credential = CredentialVault.query.filter_by(name=credential_name).first()
        
        if credential:
            try:
                # Get the decrypted value
                actual_value = credential.get_credential()
                
                # Replace the placeholder with the actual value
                placeholder = f"{{{{{credential_name}}}}}"
                processed_instruction = processed_instruction.replace(placeholder, actual_value)
                
                if credential_name not in credentials_used:
                    credentials_used.append(credential_name)
                logger.info(f"🔐 Replaced credential placeholder: {{{{{{credential_name}}}}}}")
                
            except ValueError as e:
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
    
    # Second, detect credential names in natural language (case-insensitive)
    instruction_lower = processed_instruction.lower()
    
    for credential in all_credentials:
        credential_name_lower = credential.name.lower()
        
        # Check if credential name is mentioned in the instruction
        # Look for patterns like "log in to gmail", "login to gmail", "sign in to gmail"
        login_patterns = [
            f"log in to {credential_name_lower}",
            f"login to {credential_name_lower}",
            f"sign in to {credential_name_lower}",
            f"signin to {credential_name_lower}",
            f"log into {credential_name_lower}",
            f"sign into {credential_name_lower}",
            f"authenticate to {credential_name_lower}",
            f"authenticate with {credential_name_lower}",
        ]
        
        # Also check if just the credential name is mentioned with context words
        if any(pattern in instruction_lower for pattern in login_patterns):
            try:
                password = credential.get_credential()
                username = credential.username or ""
                url = credential.url or ""
                
                # Build the replacement text with all credential info
                replacement_parts = []
                
                if url:
                    replacement_parts.append(f"go to {url}")
                
                if username and password:
                    replacement_parts.append(f"log in with username {username} and password {password}")
                elif password:
                    replacement_parts.append(f"log in with password {password}")
                
                if replacement_parts:
                    replacement_text = " and ".join(replacement_parts)
                    
                    # Find and replace the login pattern in the instruction
                    for pattern in login_patterns:
                        if pattern in instruction_lower:
                            # Find the actual text in the original instruction (preserving case)
                            start_idx = instruction_lower.find(pattern)
                            end_idx = start_idx + len(pattern)
                            original_text = processed_instruction[start_idx:end_idx]
                            
                            # Replace with detailed credential information
                            processed_instruction = (
                                processed_instruction[:start_idx] +
                                replacement_text +
                                processed_instruction[end_idx:]
                            )
                            
                            if credential.name not in credentials_used:
                                credentials_used.append(credential.name)
                            logger.info(f"🔐 Detected and expanded credential reference: {credential.name}")
                            logger.info(f"   URL: {url if url else 'Not set'}")
                            logger.info(f"   Username: {username if username else 'Not set'}")
                            logger.info(f"   Password: {'*' * len(password) if password else 'Not set'}")
                            break
                
            except ValueError as e:
                logger.error(f"Encryption error for credential '{credential.name}': {str(e)}")
                raise ValueError(
                    f"Cannot decrypt credentials: {str(e)} "
                    "Please set the ENCRYPTION_KEY environment variable or Replit Secret."
                )
            except Exception as e:
                logger.error(f"Failed to decrypt credential '{credential.name}': {str(e)}")
                decryption_errors.append(f"{credential.name}: {str(e)}")
    
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
