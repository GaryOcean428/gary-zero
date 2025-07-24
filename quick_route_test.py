#!/usr/bin/env python3
"""
Quick route testing script to identify 405 issues without full app initialization.
"""

import re
import sys
from pathlib import Path


def find_flask_routes():
    """Find all Flask routes in the codebase."""
    routes = []

    # Check run_ui.py for Flask routes
    try:
        with open("run_ui.py") as f:
            content = f.read()

        # Find route definitions
        route_patterns = [
            r'@webapp\.route\("([^"]+)"(?:,\s*methods=\[(.*?)\])?\)',
            r"@webapp\.route\('([^']+)'(?:,\s*methods=\[(.*?)\])?\)",
        ]

        for pattern in route_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                path = match[0]
                methods_str = match[1] if match[1] else ""

                # Parse methods
                if methods_str:
                    methods = [m.strip().strip("\"'") for m in methods_str.split(",")]
                else:
                    methods = ["GET"]  # Default Flask method

                routes.append({"path": path, "methods": methods, "file": "run_ui.py"})

    except Exception as e:
        print(f"Error reading run_ui.py: {e}")

    return routes


def find_form_actions():
    """Find form actions in HTML templates."""
    forms = []

    html_files = list(Path(".").rglob("*.html"))

    for html_file in html_files:
        try:
            with open(html_file, encoding="utf-8") as f:
                content = f.read()

            # Find form tags
            form_pattern = r'<form[^>]*?action=["\'](.*?)["\'][^>]*?(?:method=["\'](.*?)["\'][^>]*?)?>'
            matches = re.findall(form_pattern, content, re.IGNORECASE)

            for match in matches:
                action = match[0]
                method = match[1] if match[1] else "GET"

                forms.append(
                    {"action": action, "method": method.upper(), "file": str(html_file)}
                )

        except Exception as e:
            print(f"Error reading {html_file}: {e}")

    return forms


def analyze_405_potential():
    """Analyze potential 405 Method Not Allowed issues."""
    print("🔍 Analyzing Flask Routes for 405 Method Not Allowed Issues")
    print("=" * 70)

    routes = find_flask_routes()
    forms = find_form_actions()

    print(f"\n📋 Found {len(routes)} Flask routes:")
    print(f"{'Path':<30} {'Methods':<25} {'File'}")
    print("-" * 70)

    issues = []

    for route in routes:
        methods_str = ", ".join(route["methods"])
        print(f"{route['path']:<30} {methods_str:<25} {route['file']}")

        # Check for potential issues
        if "POST" not in route["methods"] and route["path"] in ["/", "/api"]:
            issues.append(f"⚠️  {route['path']} missing POST method (common for forms)")

        if "OPTIONS" not in route["methods"]:
            issues.append(
                f"⚠️  {route['path']} missing OPTIONS method (needed for CORS)"
            )

    print(f"\n📝 Found {len(forms)} HTML forms:")
    print(f"{'Action':<30} {'Method':<10} {'File'}")
    print("-" * 70)

    for form in forms:
        print(f"{form['action']:<30} {form['method']:<10} {form['file']}")

        # Check if form action matches a route
        matching_route = None
        for route in routes:
            if route["path"] == form["action"]:
                matching_route = route
                break

        if matching_route:
            if form["method"] not in matching_route["methods"]:
                issues.append(
                    f"❌ Form {form['action']} uses {form['method']} but route only allows {matching_route['methods']}"
                )
        else:
            if form["action"] not in ["", "#"]:
                issues.append(f"❌ Form action {form['action']} has no matching route")

    print(f"\n🚨 Potential 405 Issues Found: {len(issues)}")
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  ✅ No obvious 405 issues detected!")

    return issues


def check_error_handlers():
    """Check if proper error handlers exist."""
    print("\n🛠️  Checking Error Handlers:")

    try:
        with open("run_ui.py") as f:
            content = f.read()

        has_404_handler = "@webapp.errorhandler(404)" in content
        has_405_handler = "@webapp.errorhandler(405)" in content
        has_cors_handling = "handle_preflight" in content or "OPTIONS" in content

        print(f"  404 Handler: {'✅' if has_404_handler else '❌'}")
        print(f"  405 Handler: {'✅' if has_405_handler else '❌'}")
        print(f"  CORS/OPTIONS: {'✅' if has_cors_handling else '❌'}")

        return has_404_handler and has_405_handler and has_cors_handling

    except Exception as e:
        print(f"  ❌ Error checking handlers: {e}")
        return False


if __name__ == "__main__":
    issues = analyze_405_potential()
    handlers_ok = check_error_handlers()

    print("\n📊 Summary:")
    print(f"  Potential 405 Issues: {len(issues)}")
    print(f"  Error Handlers: {'✅ Complete' if handlers_ok else '❌ Missing'}")

    if issues or not handlers_ok:
        print("\n🎯 Recommended Actions:")
        if issues:
            print("  1. Fix route method mismatches")
            print("  2. Add missing POST/OPTIONS methods to routes")
            print("  3. Verify form actions match available routes")
        if not handlers_ok:
            print("  4. Add comprehensive error handlers")
            print("  5. Ensure proper CORS/OPTIONS handling")

        sys.exit(1)
    else:
        print("\n✅ Route configuration looks good!")
        sys.exit(0)
