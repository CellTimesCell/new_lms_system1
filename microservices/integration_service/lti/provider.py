# LTI Provider for LMS Integration
import base64
import hashlib
import json
import logging
import os
import time
import uuid
from typing import Dict, List, Optional
from urllib.parse import parse_qsl, urlencode

import jwt
import oauthlib.oauth1
from fastapi import HTTPException, Request
from pydantic import BaseModel

# Initialize logging
logger = logging.getLogger(__name__)

# LTI Configuration
LTI_CONSUMER_SECRETS = json.loads(os.getenv("LTI_CONSUMER_SECRETS", "{}"))
LTI_ISSUER = os.getenv("LTI_ISSUER", "https://yourlms.com")
LTI_KEY_SET_URL = os.getenv("LTI_KEY_SET_URL", "https://yourlms.com/lti/keys")
LTI_AUTH_URL = os.getenv("LTI_AUTH_URL", "https://yourlms.com/lti/auth")
LTI_TOKEN_URL = os.getenv("LTI_TOKEN_URL", "https://yourlms.com/lti/token")


class LTI13Config:
    """LTI 1.3 Configuration"""

    def __init__(self, client_id: str, deployment_id: str, iss: str, platform_jwks_url: str):
        self.client_id = client_id
        self.deployment_id = deployment_id
        self.iss = iss
        self.platform_jwks_url = platform_jwks_url


class LTILaunchData(BaseModel):
    """LTI Launch Data Model"""
    iss: str
    client_id: str
    deployment_id: str
    target_link_uri: str
    login_hint: Optional[str] = None
    lti_message_hint: Optional[str] = None


class LTIResourceLinkRequest(BaseModel):
    """LTI Resource Link Request"""
    id_token: str
    state: str


# LTI 1.1 Provider
async def validate_lti11_launch(request: Request, consumer_key: str) -> Dict:
    """
    Validate an LTI 1.1 launch request

    Args:
        request: The FastAPI request object
        consumer_key: The consumer key to validate against

    Returns:
        Dict of validated LTI parameters
    """
    # Get form parameters
    form_data = await request.form()
    params = dict(form_data)

    # Check required parameters
    required_params = [
        'oauth_consumer_key',
        'oauth_signature_method',
        'oauth_timestamp',
        'oauth_nonce',
        'oauth_version',
        'oauth_signature'
    ]

    for param in required_params:
        if param not in params:
            logger.error(f"Missing required LTI parameter: {param}")
            raise HTTPException(status_code=400, detail=f"Missing required LTI parameter: {param}")

    # Verify consumer key
    if params['oauth_consumer_key'] != consumer_key:
        logger.error(f"Invalid consumer key: {params['oauth_consumer_key']}")
        raise HTTPException(status_code=401, detail="Invalid consumer key")

    # Get consumer secret
    consumer_secret = LTI_CONSUMER_SECRETS.get(consumer_key)
    if not consumer_secret:
        logger.error(f"Consumer secret not found for key: {consumer_key}")
        raise HTTPException(status_code=401, detail="Consumer secret not found")

    # Create OAuth client
    client = oauthlib.oauth1.Client(
        consumer_key,
        client_secret=consumer_secret,
        signature_method=params['oauth_signature_method']
    )

    # Verify the request
    uri = str(request.url)
    http_method = request.method

    # Extract signature for verification
    signature = params.pop('oauth_signature')

    # Normalize parameters
    normalized_params = urlencode(sorted(params.items()))

    # Create base string
    base_string = '&'.join([
        http_method,
        base64.b64encode(uri.encode()).decode(),
        base64.b64encode(normalized_params.encode()).decode()
    ])

    # Calculate signature
    _, calculated_signature, _ = client.sign(
        uri,
        http_method,
        body=normalized_params,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    # Verify signature
    if signature != calculated_signature:
        logger.error("Invalid OAuth signature")
        raise HTTPException(status_code=401, detail="Invalid OAuth signature")

    # Validate timestamp to prevent replay attacks
    timestamp = int(params['oauth_timestamp'])
    current_time = int(time.time())

    if abs(current_time - timestamp) > 300:  # 5 minutes
        logger.error(f"Expired timestamp: {timestamp}, current: {current_time}")
        raise HTTPException(status_code=401, detail="Expired request")

    # Check for custom parameters
    if 'custom_course_id' in params:
        # Map external course ID to internal course ID
        pass

    # Check user information
    if 'lis_person_sourcedid' not in params and 'lis_person_name_full' not in params:
        logger.warning("Missing user identification parameters")

    # Validate context
    if 'context_id' not in params:
        logger.warning("Missing context ID")

    # Return validated parameters
    return params


# LTI 1.3 Provider
async def initiate_lti13_login(launch_data: LTILaunchData) -> Dict:
    """
    Initiate LTI 1.3 login

    Args:
        launch_data: LTI launch data

    Returns:
        Dict with redirect URL and state
    """
    # Create state for OIDC flow
    state = str(uuid.uuid4())

    # Create nonce for OIDC flow
    nonce = str(uuid.uuid4())

    # Store state and nonce in cache/database
    # This would be implemented in a real system

    # Prepare OIDC parameters
    params = {
        'client_id': launch_data.client_id,
        'login_hint': launch_data.login_hint,
        'lti_message_hint': launch_data.lti_message_hint,
        'nonce': nonce,
        'prompt': 'none',
        'redirect_uri': launch_data.target_link_uri,
        'response_mode': 'form_post',
        'response_type': 'id_token',
        'scope': 'openid',
        'state': state,
    }

    # Create OIDC initiation URL
    auth_url = f"{launch_data.iss}/auth"
    initiation_url = f"{auth_url}?{urlencode(params)}"

    return {
        'redirect_url': initiation_url,
        'state': state
    }


async def validate_lti13_launch(request: LTIResourceLinkRequest) -> Dict:
    """
    Validate an LTI 1.3 launch request

    Args:
        request: The LTI resource link request

    Returns:
        Dict of validated LTI claims
    """
    # Verify state
    # This would fetch the state from cache/database in a real system

    # Decode ID token
    try:
        # In a real implementation, you would validate the JWT signature
        # using the platform's public key fetched from jwks_url
        claims = jwt.decode(
            request.id_token,
            options={"verify_signature": False}  # For demonstration only
        )
    except jwt.PyJWTError as e:
        logger.error(f"Error decoding ID token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid ID token")

    # Validate required claims
    required_claims = [
        'iss', 'sub', 'aud', 'exp', 'iat', 'nonce',
        'https://purl.imsglobal.org/spec/lti/claim/message_type',
        'https://purl.imsglobal.org/spec/lti/claim/version',
        'https://purl.imsglobal.org/spec/lti/claim/deployment_id'
    ]

    for claim in required_claims:
        if claim not in claims:
            logger.error(f"Missing required claim: {claim}")
            raise HTTPException(status_code=400, detail=f"Missing required claim: {claim}")

    # Verify message type
    if claims['https://purl.imsglobal.org/spec/lti/claim/message_type'] != 'LtiResourceLinkRequest':
        logger.error(f"Unsupported message type: {claims['https://purl.imsglobal.org/spec/lti/claim/message_type']}")
        raise HTTPException(status_code=400, detail="Unsupported message type")

    # Verify LTI version
    if claims['https://purl.imsglobal.org/spec/lti/claim/version'] != '1.3.0':
        logger.error(f"Unsupported LTI version: {claims['https://purl.imsglobal.org/spec/lti/claim/version']}")
        raise HTTPException(status_code=400, detail="Unsupported LTI version")

    # Verify expiration
    if claims['exp'] < time.time():
        logger.error("Expired ID token")
        raise HTTPException(status_code=401, detail="Expired ID token")

    # Process role claims
    roles = claims.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])

    # Map LTI roles to internal roles
    role_mapping = {
        'http://purl.imsglobal.org/vocab/lis/v2/institution/person#Student': 'student',
        'http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor': 'instructor',
        'http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator': 'admin'
    }

    internal_roles = [role_mapping.get(role, 'user') for role in roles if role in role_mapping]

    # Process custom parameters
    custom = claims.get('https://purl.imsglobal.org/spec/lti/claim/custom', {})

    # Create user if not exists and map to internal user
    # This would be implemented in a real system

    # Return processed claims with internal mappings
    return {
        'lti_claims': claims,
        'internal_roles': internal_roles,
        'custom_params': custom,
        'validated': True
    }