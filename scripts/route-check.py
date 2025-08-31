#!/usr/bin/env python3
"""
Comprehensive Route Check Utility for Gary Zero
Validates all routes, API endpoints, and health checks
"""

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import aiohttp


@dataclass
class RouteTest:
    path: str
    method: str
    expected_status: int
    requires_auth: bool = False
    test_data: dict[str, Any] = None
    description: str = ""


@dataclass
class RouteResult:
    path: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error: str = ""
    response_size: int = 0


class RouteChecker:
    def __init__(self, base_url: str = "http://localhost:8080", auth_token: str = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.results: list[RouteResult] = []

    async def check_route(
        self, session: aiohttp.ClientSession, route_test: RouteTest
    ) -> RouteResult:
        """Check a single route and return the result"""
        url = f"{self.base_url}{route_test.path}"
        headers = {}

        if route_test.requires_auth and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        start_time = time.time()

        try:
            async with session.request(
                route_test.method,
                url,
                headers=headers,
                json=route_test.test_data,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                response_time = (time.time() - start_time) * 1000
                response_text = await response.text()

                success = response.status == route_test.expected_status or (
                    route_test.expected_status == 200 and 200 <= response.status < 300
                )

                return RouteResult(
                    path=route_test.path,
                    method=route_test.method,
                    status_code=response.status,
                    response_time_ms=response_time,
                    success=success,
                    response_size=len(response_text.encode("utf-8")),
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return RouteResult(
                path=route_test.path,
                method=route_test.method,
                status_code=0,
                response_time_ms=response_time,
                success=False,
                error=str(e),
            )

    def discover_api_routes(self) -> list[RouteTest]:
        """Discover API routes from framework/api directory"""
        routes = []
        api_dir = Path("framework/api")

        if not api_dir.exists():
            print(f"Warning: {api_dir} not found")
            return routes

        for py_file in api_dir.glob("*.py"):
            if py_file.stem == "__init__":
                continue

            route_name = py_file.stem
            routes.append(
                RouteTest(
                    path=f"/{route_name}",
                    method="POST",
                    expected_status=200,
                    requires_auth=True,
                    description=f"API endpoint for {route_name}",
                )
            )

        return routes

    def get_static_routes(self) -> list[RouteTest]:
        """Get list of static routes to test"""
        return [
            RouteTest(
                "/", "GET", 200, requires_auth=True, description="Main index page"
            ),
            RouteTest("/health", "GET", 200, description="Health check endpoint"),
            RouteTest("/ready", "GET", 200, description="Readiness check endpoint"),
            RouteTest("/privacy", "GET", 200, description="Privacy policy page"),
            RouteTest("/terms", "GET", 200, description="Terms of service page"),
            RouteTest("/favicon.ico", "GET", 200, description="Favicon"),
            RouteTest("/nonexistent", "GET", 404, description="404 error test"),
        ]

    async def run_checks(self) -> dict[str, Any]:
        """Run all route checks and return comprehensive results"""
        static_routes = self.get_static_routes()
        api_routes = self.discover_api_routes()
        all_routes = static_routes + api_routes

        print(f"🔍 Checking {len(all_routes)} routes...")
        print(f"   - {len(static_routes)} static routes")
        print(f"   - {len(api_routes)} API routes")

        async with aiohttp.ClientSession() as session:
            tasks = [self.check_route(session, route) for route in all_routes]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        valid_results = [r for r in results if isinstance(r, RouteResult)]
        failed_checks = [r for r in results if isinstance(r, Exception)]

        success_count = sum(1 for r in valid_results if r.success)
        total_checks = len(valid_results)

        # Calculate statistics
        avg_response_time = (
            sum(r.response_time_ms for r in valid_results) / len(valid_results)
            if valid_results
            else 0
        )

        report = {
            "timestamp": time.time(),
            "summary": {
                "total_routes": total_checks,
                "successful": success_count,
                "failed": total_checks - success_count,
                "success_rate": (
                    (success_count / total_checks * 100) if total_checks > 0 else 0
                ),
                "avg_response_time_ms": avg_response_time,
            },
            "results": [asdict(r) for r in valid_results],
            "exceptions": [str(e) for e in failed_checks],
            "route_breakdown": {
                "static_routes": {
                    "total": len(static_routes),
                    "successful": sum(
                        1
                        for r in valid_results
                        if r.path in [sr.path for sr in static_routes] and r.success
                    ),
                },
                "api_routes": {
                    "total": len(api_routes),
                    "successful": sum(
                        1
                        for r in valid_results
                        if r.path in [ar.path for ar in api_routes] and r.success
                    ),
                },
            },
        }

        return report

    def print_results(self, report: dict[str, Any]):
        """Print formatted results to console"""
        summary = report["summary"]

        print("\n" + "=" * 60)
        print("🛣️  ROUTE CHECK RESULTS")
        print("=" * 60)

        print("📊 Summary:")
        print(f"   Total Routes: {summary['total_routes']}")
        print(f"   Successful: {summary['successful']} ✅")
        print(f"   Failed: {summary['failed']} ❌")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Avg Response Time: {summary['avg_response_time_ms']:.1f}ms")

        # Print detailed results
        print("\n📋 Detailed Results:")
        for result in report["results"]:
            status_icon = "✅" if result["success"] else "❌"
            print(
                f"   {status_icon} {result['method']} {result['path']} - {result['status_code']} ({result['response_time_ms']:.1f}ms)"
            )
            if result.get("error"):
                print(f"      Error: {result['error']}")

        # Print failures
        if summary["failed"] > 0:
            print("\n❌ Failed Routes:")
            for result in report["results"]:
                if not result["success"]:
                    print(
                        f"   {result['method']} {result['path']}: {result.get('error', 'Status ' + str(result['status_code']))}"
                    )


async def main():
    parser = argparse.ArgumentParser(description="Check all Gary Zero routes")
    parser.add_argument(
        "--url", default="http://localhost:8080", help="Base URL to test"
    )
    parser.add_argument("--auth-token", help="Authentication token")
    parser.add_argument("--output", "-o", help="Output file for JSON results")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    checker = RouteChecker(args.url, args.auth_token)

    try:
        report = await checker.run_checks()

        if not args.quiet:
            checker.print_results(report)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Results saved to {args.output}")

        # Exit with error code if there were failures
        sys.exit(0 if report["summary"]["failed"] == 0 else 1)

    except KeyboardInterrupt:
        print("\n⏹️  Route check interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Route check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
