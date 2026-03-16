import operator
from time import perf_counter

import httpx
import pendulum
import structlog
from fastapi.routing import APIRoute

from ichrisbirch import schemas
from ichrisbirch.config import Settings

logger = structlog.get_logger()

SKIP_NAMES = {'run_smoke_tests_endpoint', 'docs_redirect'}
SKIP_PREFIXES = ('/auth/',)


def discover_get_endpoints(app) -> list[dict]:
    """Discover all GET endpoints from the FastAPI app's route table."""
    endpoints = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if 'GET' not in route.methods:
            continue
        if route.name in SKIP_NAMES:
            continue
        if any(route.path.startswith(p) for p in SKIP_PREFIXES):
            continue
        if '{' in route.path:
            continue
        if any(p.required for p in route.dependant.query_params):
            continue

        endpoints.append({'path': route.path, 'name': route.name or route.path})

    endpoints.sort(key=operator.itemgetter('path'))
    return endpoints


async def run_smoke_tests(app, settings: Settings, admin_email: str) -> schemas.admin.SmokeTestReport:
    """Run smoke tests against all discovered GET endpoints."""
    endpoints = discover_get_endpoints(app)
    results: list[schemas.admin.SmokeTestResult] = []
    start = perf_counter()
    headers = {'Remote-User': admin_email, 'Remote-Email': admin_email}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://smoke-test') as client:
        for endpoint in endpoints:
            result = await _test_endpoint(client, endpoint, headers)
            results.append(result)

    total_ms = (perf_counter() - start) * 1000
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    report = schemas.admin.SmokeTestReport(
        run_at=pendulum.now().isoformat(timespec='seconds'),
        environment=settings.ENVIRONMENT,
        total=len(results),
        passed=passed,
        failed=failed,
        duration_ms=round(total_ms, 1),
        all_passed=failed == 0,
        results=results,
    )

    logger.info('smoke_tests_completed', total=report.total, passed=passed, failed=failed, duration_ms=report.duration_ms)
    return report


async def _test_endpoint(client: httpx.AsyncClient, endpoint: dict, headers: dict[str, str]) -> schemas.admin.SmokeTestResult:
    """Test a single endpoint and return the result."""
    start = perf_counter()
    try:
        response = await client.get(endpoint['path'], headers=headers, timeout=5.0)
        elapsed_ms = (perf_counter() - start) * 1000
        passed = 200 <= response.status_code < 300

        if not passed:
            logger.warning('smoke_test_failed', path=endpoint['path'], status_code=response.status_code)

        return schemas.admin.SmokeTestResult(
            path=endpoint['path'],
            name=endpoint['name'],
            status_code=response.status_code,
            response_time_ms=round(elapsed_ms, 1),
            passed=passed,
        )
    except Exception as e:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.error('smoke_test_error', path=endpoint['path'], error=str(e))
        return schemas.admin.SmokeTestResult(
            path=endpoint['path'],
            name=endpoint['name'],
            response_time_ms=round(elapsed_ms, 1),
            passed=False,
            error=str(e),
        )
