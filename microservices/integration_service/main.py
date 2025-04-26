# Integration Service for LMS
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
import uvicorn
import logging
from typing import Dict, List, Optional
import json
import os

from security.authentication.auth import get_current_active_user
from microservices.integration_service.lti.provider import (
    validate_lti11_launch,
    initiate_lti13_login,
    validate_lti13_launch,
    LTILaunchData,
    LTIResourceLinkRequest
)
from microservices.integration_service.schemas import (
    ExternalToolConfig,
    ToolLaunchRequest,
    SSOConfig
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LMS Integration Service",
    description="Service for external tool integrations, LTI, and SSO",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# External tool configurations
TOOLS_CONFIG = json.loads(os.getenv("EXTERNAL_TOOLS_CONFIG", "{}"))


@app.post("/lti/v1/launch")
async def lti11_launch(request: Request, oauth_consumer_key: str = Form(...)):
    """
    Handle LTI 1.1 launch requests
    """
    try:
        # Validate LTI launch parameters
        lti_params = await validate_lti11_launch(request, oauth_consumer_key)

        # Extract context and user information
        context_id = lti_params.get('context_id')
        user_id = lti_params.get('user_id')
        roles = lti_params.get('roles', '').split(',')

        # Map external user to internal user
        internal_user = await map_lti_user(user_id, lti_params)

        # Create session for user
        # This would create a session in a real system

        # Determine redirect URL based on role and context
        redirect_url = "/dashboard"
        if "Instructor" in roles:
            redirect_url = f"/instructor/course/{context_id}"
        else:
            redirect_url = f"/student/course/{context_id}"

        # Create response with session information
        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling LTI 1.1 launch: {str(e)}")
        raise HTTPException(status_code=500, detail="Error handling LTI launch")


@app.post("/lti/v1.3/login-initiation")
async def lti13_login_initiation(launch_data: LTILaunchData):
    """
    Initiate LTI 1.3 login
    """
    try:
        # Process LTI 1.3 login initiation
        result = await initiate_lti13_login(launch_data)

        # Return redirect URL
        return {"redirect_url": result["redirect_url"]}

    except Exception as e:
        logger.error(f"Error initiating LTI 1.3 login: {str(e)}")
        raise HTTPException(status_code=500, detail="Error initiating LTI login")


@app.post("/lti/v1.3/launch")
async def lti13_launch(request: LTIResourceLinkRequest):
    """
    Handle LTI 1.3 launch requests
    """
    try:
        # Validate LTI launch
        result = await validate_lti13_launch(request)

        # Extract LTI claims
        claims = result["lti_claims"]
        roles = result["internal_roles"]

        # Extract context information
        resource_link = claims.get('https://purl.imsglobal.org/spec/lti/claim/resource_link', {})
        context = claims.get('https://purl.imsglobal.org/spec/lti/claim/context', {})

        # Map to internal course
        course_id = await map_lti_context(context.get('id'), context)

        # Create session for user
        # This would create a session in a real system

        # Determine redirect URL based on role and context
        redirect_url = "/dashboard"
        if "instructor" in roles:
            redirect_url = f"/instructor/course/{course_id}"
        else:
            redirect_url = f"/student/course/{course_id}"

        # Create response with session information
        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling LTI 1.3 launch: {str(e)}")
        raise HTTPException(status_code=500, detail="Error handling LTI launch")


@app.get("/external-tools")
async def list_external_tools(user=Depends(get_current_active_user)):
    """
    List available external tools
    """
    try:
        # Filter tools based on user roles
        user_roles = [role.name for role in user.roles]

        available_tools = []
        for tool_id, tool_config in TOOLS_CONFIG.items():
            # Check role requirements
            required_roles = tool_config.get("required_roles", [])
            if not required_roles or any(role in user_roles for role in required_roles):
                available_tools.append({
                    "id": tool_id,
                    "name": tool_config.get("name"),
                    "description": tool_config.get("description"),
                    "icon_url": tool_config.get("icon_url"),
                    "launch_url": f"/api/integrations/external-tools/{tool_id}/launch"
                })

        return available_tools

    except Exception as e:
        logger.error(f"Error listing external tools: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing external tools")


@app.post("/external-tools/{tool_id}/launch")
async def launch_external_tool(
        tool_id: str,
        launch_request: ToolLaunchRequest,
        user=Depends(get_current_active_user)
):
    """
    Launch an external tool
    """
    try:
        # Get tool configuration
        tool_config = TOOLS_CONFIG.get(tool_id)
        if not tool_config:
            raise HTTPException(status_code=404, detail="Tool not found")

        # Check if user has required roles
        user_roles = [role.name for role in user.roles]
        required_roles = tool_config.get("required_roles", [])
        if required_roles and not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Determine launch method
        launch_method = tool_config.get("launch_method", "url")

        if launch_method == "lti":
            # Launch as LTI 1.1
            launch_url = tool_config.get("launch_url")
            consumer_key = tool_config.get("consumer_key")

            # Generate LTI parameters
            lti_params = {
                "oauth_consumer_key": consumer_key,
                "resource_link_id": launch_request.resource_id or str(user.id),
                "user_id": str(user.id),
                "lis_person_name_full": user.full_name(),
                "lis_person_contact_email_primary": user.email,
                "roles": "Instructor" if "instructor" in user_roles else "Learner",
                "context_id": str(launch_request.context_id) if launch_request.context_id else "1",
                "tool_consumer_instance_guid": os.getenv("LMS_INSTANCE_GUID", "yourlms.com"),
                "launch_presentation_document_target": "iframe",
            }

            # Include custom parameters
            if launch_request.custom_params:
                for key, value in launch_request.custom_params.items():
                    lti_params[f"custom_{key}"] = value

            # Generate launch form HTML
            form_html = f"""
            <html>
                <body onload="document.getElementById('lti_form').submit();">
                    <form id="lti_form" method="post" action="{launch_url}">
            """

            for key, value in lti_params.items():
                form_html += f'<input type="hidden" name="{key}" value="{value}" />\n'

            form_html += """
                    </form>
                </body>
            </html>
            """

            return HTMLResponse(content=form_html)

        else:
            # Simple URL launch
            launch_url = tool_config.get("launch_url")

            # Add any query parameters
            if launch_request.custom_params:
                query_params = "&".join([f"{key}={value}" for key, value in launch_request.custom_params.items()])
                launch_url = f"{launch_url}?{query_params}"

            return {"launch_url": launch_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error launching external tool: {str(e)}")
        raise HTTPException(status_code=500, detail="Error launching external tool")


# Helper functions for LTI
async def map_lti_user(lti_user_id: str, lti_params: Dict) -> Dict:
    """Map LTI user to internal user"""
    # This would lookup or create an internal user based on LTI user info
    # Simplified implementation for demonstration
    return {
        "id": lti_user_id,
        "name": lti_params.get("lis_person_name_full", "Unknown"),
        "email": lti_params.get("lis_person_contact_email_primary", "unknown@example.com"),
        "roles": lti_params.get("roles", "").split(","),
    }


async def map_lti_context(context_id: str, context_data: Dict) -> str:
    """Map LTI context to internal course ID"""
    # This would lookup or create an internal course based on LTI context
    # Simplified implementation for demonstration
    return context_id


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("Starting Integration Service")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("Shutting down Integration Service")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)