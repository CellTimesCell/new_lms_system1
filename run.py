# run.py
import uvicorn
import os
import argparse
import subprocess


def run_server(host="0.0.0.0", port=8000, reload=True):
    """Run the FastAPI server"""
    print(f"Starting server on http://{host}:{port}")
    uvicorn.run("core.lms_core.main:app", host=host, port=port, reload=reload)


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
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")

    args = parser.parse_args()

    if args.setup:
        setup_database()

    # Run server
    run_server(host=args.host, port=args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()