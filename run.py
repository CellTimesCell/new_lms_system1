# run.py
import uvicorn
import os
import argparse
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def run_server(service="core", host="0.0.0.0", port=8000, reload=True):
    """Run a service"""
    print(f"Starting {service} service on http://{host}:{port}")

    if service == "core":
        uvicorn.run("core.lms_core.main:app", host=host, port=port, reload=reload)
    elif service == "analytics":
        uvicorn.run("microservices.analytics_service.main:app", host=host, port=port, reload=reload)
    elif service == "content":
        uvicorn.run("microservices.content_service.main:app", host=host, port=port, reload=reload)
    elif service == "notification":
        uvicorn.run("microservices.notification_service.main:app", host=host, port=port, reload=reload)
    elif service == "ai":
        uvicorn.run("microservices.ai_service.main:app", host=host, port=port, reload=reload)
    elif service == "gamification":
        uvicorn.run("microservices.gamification_service.main:app", host=host, port=port, reload=reload)
    elif service == "integration":
        uvicorn.run("microservices.integration_service.main:app", host=host, port=port, reload=reload)
    else:
        print(f"Unknown service: {service}")


def setup_database():
    """Setup database and create sample data"""
    print("Setting up database...")
    # Run migrations
    subprocess.run(["alembic", "upgrade", "head"])

    # Create sample data
    subprocess.run(["python", "scripts/create_sample_data.py"])


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="LMS System Runner")
    parser.add_argument("--setup", action="store_true", help="Setup database and sample data")
    parser.add_argument("--service", type=str, default="core",
                        help="Service to run (core, analytics, content, notification, ai, gamification, integration)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")

    args = parser.parse_args()

    if args.setup:
        setup_database()

    # Run server
    run_server(service=args.service, host=args.host, port=args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()