#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import sys
import subprocess
import os
import time
from datetime import datetime

# Enable UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_status(args):
    """Display comprehensive system status and health information."""
    try:
        from core.component_health import get_health_monitor, HealthStatus
        from state_machine.state_engine import StateMachine
        import platform

        # Print header
        print("\n" + "=" * 70)
        print("🛰️  AstraGuard AI - System Status Report")
        print("=" * 70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
        print(f"Python: {platform.python_version()}")
        print("=" * 70)

        # System Health Section
        print("\n📊 COMPONENT HEALTH STATUS")
        print("-" * 70)

        health_monitor = get_health_monitor()
        components = health_monitor.get_all_health()

        # Initialize counts
        healthy_count = 0
        degraded_count = 0
        failed_count = 0

        if not components:
            print("  ⚠️  No components registered yet")
            print("     Run the API server or dashboard to initialize components")
        else:
            # Calculate overall health
            healthy_count = sum(1 for c in components.values() if c["status"] == "healthy")
            degraded_count = sum(1 for c in components.values() if c["status"] == "degraded")
            failed_count = sum(1 for c in components.values() if c["status"] == "failed")

            # Print summary
            total = len(components)
            print(f"  Total Components: {total}")
            print(f"  Healthy: {healthy_count}  |  Degraded: {degraded_count}  |  Failed: {failed_count}")
            print()

            # Print each component
            for name, status_info in sorted(components.items()):
                status = status_info["status"]

                # Choose icon based on status (lowercase comparison)
                if status == "healthy":
                    icon = "✅"
                elif status == "degraded":
                    icon = "⚠️ "
                elif status == "failed":
                    icon = "❌"
                else:
                    icon = "❓"

                # Component line
                print(f"  {icon} {name:30s} {status:10s}", end="")

                # Additional info if available
                if status_info.get("fallback_active"):
                    print("  [FALLBACK MODE]", end="")
                if status_info.get("error_count", 0) > 0:
                    print(f"  (Errors: {status_info['error_count']})", end="")

                print()  # New line

                # Show last error if in verbose mode
                if args.verbose and status_info.get("last_error"):
                    print(f"       Last Error: {status_info['last_error']}")

        # Mission Phase Section
        print("\n🚀 MISSION PHASE")
        print("-" * 70)
        try:
            state_machine = StateMachine()
            current_phase = state_machine.current_phase
            print(f"  Current Phase: {current_phase.value}")
            print(f"  Description:   {_get_phase_description(current_phase.value)}")
        except Exception as e:
            print(f"  ⚠️  Unable to determine mission phase: {e}")

        # Configuration Section
        print("\n⚙️  CONFIGURATION")
        print("-" * 70)

        # Check for important files
        config_files = [
            ("Mission Policies", "config/mission_phase_response_policy.yaml"),
            ("Recovery Config", "config/recovery.yaml"),
            ("Recovery Policies", "config/recovery_policies.yaml"),
        ]

        for name, filepath in config_files:
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  ✅ {name:30s} ({size:,} bytes)")
            else:
                print(f"  ❌ {name:30s} NOT FOUND")

        # Quick Health Check Section
        print("\n🔍 QUICK HEALTH CHECKS")
        print("-" * 70)

        checks = [
            ("Python Version", lambda: sys.version_info >= (3, 9), "Python 3.9+ required"),
            ("Requirements File", lambda: os.path.exists("requirements.txt"), "requirements.txt found"),
            ("Virtual Environment", lambda: hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix), "Running in venv"),
        ]

        for check_name, check_func, success_msg in checks:
            try:
                result = check_func()
                if result:
                    print(f"  ✅ {check_name:30s} {success_msg}")
                else:
                    print(f"  ⚠️  {check_name:30s} Check failed")
            except Exception as e:
                print(f"  ❌ {check_name:30s} Error: {e}")

        # Recommendations Section
        print("\n💡 RECOMMENDATIONS")
        print("-" * 70)

        if degraded_count > 0 or failed_count > 0:
            print("  ⚠️  Some components are not healthy:")
            print("     • Check component logs for detailed error messages")
            print("     • Run with --verbose flag for more details")
            print("     • Review error handling configuration")
        else:
            print("  ✅ All systems operational - no action needed")

        print("\n" + "=" * 70)
        print("For more details, run: python cli.py status --verbose")
        print("=" * 70 + "\n")

        # Return exit code based on health
        if failed_count > 0:
            sys.exit(1)  # Exit with error if any component failed
        elif degraded_count > 0:
            sys.exit(2)  # Exit with warning if any component degraded
        else:
            sys.exit(0)  # Success

    except ImportError as e:
        print(f"\n❌ Error: Unable to import required modules: {e}")
        print("   Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(3)
    except Exception as e:
        print(f"\n❌ Unexpected error while checking status: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(4)


def _get_phase_description(phase):
    """Get human-readable description for mission phase."""
    descriptions = {
        "LAUNCH": "Rocket ascent and orbital insertion",
        "DEPLOYMENT": "System stabilization and checkout",
        "NOMINAL_OPS": "Standard mission operations",
        "PAYLOAD_OPS": "Science/mission payload operations",
        "SAFE_MODE": "Minimal power survival mode",
    }
    return descriptions.get(phase, "Unknown phase")


def run_telemetry():
    subprocess.run(
        [sys.executable, os.path.join("astraguard", "telemetry", "telemetry_stream.py")]
    )


def run_dashboard():
    subprocess.run(["streamlit", "run", os.path.join("dashboard", "app.py")])


def run_simulation():
    subprocess.run([sys.executable, os.path.join("simulation", "attitude_3d.py")])


def run_classifier():
    subprocess.run([sys.executable, os.path.join("classifier", "fault_classifier.py")])


def run_logs(args):
    cmd = [sys.executable, os.path.join("logs", "timeline.py")]
    if args.export:
        cmd.extend(["--export", args.export])
    subprocess.run(cmd)


def run_api(args):
    cmd = [sys.executable, "run_api.py"]
    if args.host:
        cmd.extend(["--host", args.host])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.reload:
        cmd.append("--reload")
    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(
        description="AstraGuard-AI: Unified CLI\nUse `cli.py <subcommand>`"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status and health")
    status_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed error messages and component information"
    )

    subparsers.add_parser("telemetry", help="Run telemetry stream generator")
    subparsers.add_parser("dashboard", help="Run Streamlit dashboard UI")
    subparsers.add_parser("simulate", help="Run 3D attitude simulation")
    subparsers.add_parser("classify", help="Run fault classifier tests")
    logs_parser = subparsers.add_parser("logs", help="Event log utilities")
    logs_parser.add_argument(
        "--export",
        metavar="PATH",
        help="Export event log to file (same as logs/timeline.py)",
    )

    api_parser = subparsers.add_parser("api", help="Run REST API server")
    api_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    api_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    api_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()
    if args.command == "status":
        run_status(args)
    elif args.command == "telemetry":
        run_telemetry()
    elif args.command == "dashboard":
        run_dashboard()
    elif args.command == "simulate":
        run_simulation()
    elif args.command == "classify":
        run_classifier()
    elif args.command == "logs":
        run_logs(args)
    elif args.command == "api":
        run_api(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
