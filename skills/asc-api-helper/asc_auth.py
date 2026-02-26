"""JWT token generation for App Store Connect API."""

import jwt
import time
from cryptography.hazmat.primitives import serialization


def generate_token(key_id: str, issuer_id: str, key_file: str) -> str:
    """
    Generate a JWT token for App Store Connect API authentication.
    
    Args:
        key_id: The Key ID from App Store Connect
        issuer_id: The Issuer ID from App Store Connect
        key_file: Path to the .p8 private key file
        
    Returns:
        JWT token string
        
    Raises:
        FileNotFoundError: If the key file doesn't exist
        ValueError: If the key file is invalid
    """
    # Load private key
    with open(key_file, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    
    # Generate JWT (valid for 20 minutes)
    now = int(time.time())
    payload = {
        'iss': issuer_id,
        'exp': now + 1200,  # 20 minutes
        'aud': 'appstoreconnect-v1',
    }
    
    headers = {
        'alg': 'ES256',
        'kid': key_id,
        'typ': 'JWT',
    }
    
    return jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
