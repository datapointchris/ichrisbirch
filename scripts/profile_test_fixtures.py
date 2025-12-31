#!/usr/bin/env python
"""Profile test fixture performance to identify optimization opportunities.

This script measures:
1. Table drop/create time (DDL operations)
2. Sequence reset time
3. Individual fixture overhead

Run: uv run python scripts/profile_test_fixtures.py
"""

import contextlib
import statistics
import time
from dataclasses import dataclass
from dataclasses import field

from sqlalchemy import text

from ichrisbirch.database.base import Base
from ichrisbirch.database.session import get_db_engine
from tests.conftest import SEQUENCES_TO_RESET
from tests.utils.database import test_settings


@dataclass
class TimingResult:
    """Container for timing measurements."""

    name: str
    times: list[float] = field(default_factory=list)

    @property
    def mean(self) -> float:
        return statistics.mean(self.times) if self.times else 0

    @property
    def stdev(self) -> float:
        return statistics.stdev(self.times) if len(self.times) > 1 else 0

    @property
    def min(self) -> float:
        return min(self.times) if self.times else 0

    @property
    def max(self) -> float:
        return max(self.times) if self.times else 0

    def __str__(self) -> str:
        return (
            f'{self.name}: mean={self.mean * 1000:.2f}ms, '
            f'std={self.stdev * 1000:.2f}ms, '
            f'min={self.min * 1000:.2f}ms, max={self.max * 1000:.2f}ms'
        )


def time_operation(func, iterations: int = 5) -> TimingResult:
    """Time an operation multiple times and return statistics."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
    return TimingResult(name=func.__name__, times=times)


def profile_table_operations():
    """Profile table create/drop operations."""
    print('=' * 60)
    print('TABLE OPERATION PROFILING')
    print('=' * 60)

    engine = get_db_engine(test_settings)

    def drop_all_tables():
        Base.metadata.drop_all(engine)

    def create_all_tables():
        Base.metadata.create_all(engine)

    # First, ensure tables exist
    create_all_tables()

    # Profile drop
    drop_result = time_operation(drop_all_tables, iterations=3)
    print(f'\n{drop_result}')

    # Profile create
    create_result = time_operation(create_all_tables, iterations=3)
    print(create_result)

    # Profile drop + create cycle (typical session scope)
    def drop_and_create():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    cycle_result = time_operation(drop_and_create, iterations=3)
    print(cycle_result)

    return drop_result, create_result, cycle_result


def profile_sequence_resets():
    """Profile sequence reset operations."""
    print('\n' + '=' * 60)
    print('SEQUENCE RESET PROFILING')
    print('=' * 60)

    engine = get_db_engine(test_settings)

    # Ensure tables exist
    Base.metadata.create_all(engine)

    def reset_all_sequences():
        with engine.connect() as conn:
            for seq in SEQUENCES_TO_RESET:
                with contextlib.suppress(Exception):
                    conn.execute(text(f'ALTER SEQUENCE {seq} RESTART WITH 1'))
            conn.commit()

    def reset_single_sequence():
        with engine.connect() as conn:
            with contextlib.suppress(Exception):
                conn.execute(text(f'ALTER SEQUENCE {SEQUENCES_TO_RESET[0]} RESTART WITH 1'))
            conn.commit()

    # Profile all sequences
    all_result = time_operation(reset_all_sequences, iterations=10)
    print(f'\nReset all {len(SEQUENCES_TO_RESET)} sequences: {all_result}')

    # Profile single sequence
    single_result = time_operation(reset_single_sequence, iterations=10)
    print(f'Reset single sequence: {single_result}')

    # Calculate per-sequence overhead
    per_seq_overhead = (all_result.mean - single_result.mean) / (len(SEQUENCES_TO_RESET) - 1)
    print(f'\nPer-sequence overhead: {per_seq_overhead * 1000:.2f}ms')

    return all_result, single_result


def profile_connection_overhead():
    """Profile database connection establishment."""
    print('\n' + '=' * 60)
    print('CONNECTION OVERHEAD PROFILING')
    print('=' * 60)

    engine = get_db_engine(test_settings)

    def establish_connection():
        conn = engine.connect()
        conn.close()

    def connection_with_transaction():
        conn = engine.connect()
        txn = conn.begin()
        txn.rollback()
        conn.close()

    conn_result = time_operation(establish_connection, iterations=20)
    print(f'\n{conn_result}')

    txn_result = time_operation(connection_with_transaction, iterations=20)
    print(txn_result)

    return conn_result, txn_result


def count_tables_and_sequences():
    """Count the number of tables and sequences in the schema."""
    print('\n' + '=' * 60)
    print('SCHEMA STATISTICS')
    print('=' * 60)

    engine = get_db_engine(test_settings)

    # Create tables to ensure they exist
    Base.metadata.create_all(engine)

    with engine.connect() as conn:
        # Count tables
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            AND table_type = 'BASE TABLE'
        """
            )
        )
        table_count = result.scalar()

        # Count sequences
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) FROM information_schema.sequences
            WHERE sequence_schema NOT IN ('pg_catalog', 'information_schema')
        """
            )
        )
        sequence_count = result.scalar()

        # Get table names by schema
        result = conn.execute(
            text(
                """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name
        """
            )
        )
        tables = result.fetchall()

    print(f'\nTotal tables: {table_count}')
    print(f'Total sequences: {sequence_count}')
    print(f'Sequences tracked for reset: {len(SEQUENCES_TO_RESET)}')

    print('\nTables by schema:')
    current_schema = None
    for schema, table in tables:
        if schema != current_schema:
            current_schema = schema
            print(f'  {schema}:')
        print(f'    - {table}')

    return table_count, sequence_count


def profile_user_lookup():
    """Profile user lookup operations (get_test_user)."""
    print('\n' + '=' * 60)
    print('USER LOOKUP PROFILING')
    print('=' * 60)

    from tests.utils.database import get_test_user

    engine = get_db_engine(test_settings)
    Base.metadata.create_all(engine)

    # Insert login users if they don't exist
    from sqlalchemy import select

    from ichrisbirch import models
    from tests.utils.database import create_session
    from tests.utils.database import get_test_login_users

    with create_session(test_settings) as session:
        for user_data in get_test_login_users():
            existing = session.execute(select(models.User).where(models.User.email == user_data['email'])).scalar_one_or_none()
            if not existing:
                session.add(models.User(**user_data))
        session.commit()

    def lookup_regular_user():
        return get_test_user('testloginregular@testuser.com')

    def lookup_admin_user():
        return get_test_user('testloginadmin@testadmin.com')

    # Profile uncached lookups
    regular_result = time_operation(lookup_regular_user, iterations=20)
    admin_result = time_operation(lookup_admin_user, iterations=20)

    print(f'\nUncached user lookup (regular): {regular_result}')
    print(f'Uncached user lookup (admin): {admin_result}')

    # Simulate cached lookup
    cached_users: dict = {}

    def cached_lookup_regular():
        if 'regular' not in cached_users:
            cached_users['regular'] = get_test_user('testloginregular@testuser.com')
        return cached_users['regular']

    def cached_lookup_admin():
        if 'admin' not in cached_users:
            cached_users['admin'] = get_test_user('testloginadmin@testadmin.com')
        return cached_users['admin']

    # Warm the cache
    cached_lookup_regular()
    cached_lookup_admin()

    cached_regular_result = time_operation(cached_lookup_regular, iterations=20)
    cached_admin_result = time_operation(cached_lookup_admin, iterations=20)

    print(f'\nCached user lookup (regular): {cached_regular_result}')
    print(f'Cached user lookup (admin): {cached_admin_result}')

    print('\nPotential savings per test (2 lookups):')
    uncached_per_test = regular_result.mean + admin_result.mean
    cached_per_test = cached_regular_result.mean + cached_admin_result.mean
    savings = uncached_per_test - cached_per_test
    print(f'  Uncached: {uncached_per_test * 1000:.2f}ms')
    print(f'  Cached: {cached_per_test * 1000:.2f}ms')
    print(f'  Savings: {savings * 1000:.2f}ms ({savings / uncached_per_test * 100:.1f}%)')

    return regular_result, admin_result, cached_regular_result, cached_admin_result


def profile_api_creation():
    """Profile API app creation overhead."""
    print('\n' + '=' * 60)
    print('API APP CREATION PROFILING')
    print('=' * 60)

    from ichrisbirch.api.main import create_api

    def create_fresh_api():
        return create_api(settings=test_settings)

    # Profile fresh API creation
    fresh_result = time_operation(create_fresh_api, iterations=5)
    print(f'\nFresh API creation: {fresh_result}')

    # Simulate cached API access
    cached_api = None

    def get_cached_api_simulated():
        nonlocal cached_api
        if cached_api is None:
            cached_api = create_api(settings=test_settings)
        return cached_api

    # Warm the cache
    get_cached_api_simulated()

    cached_result = time_operation(get_cached_api_simulated, iterations=20)
    print(f'Cached API access: {cached_result}')

    savings = fresh_result.mean - cached_result.mean
    print(f'\nSavings per test: {savings * 1000:.2f}ms')

    return fresh_result, cached_result


def estimate_optimization_impact():
    """Estimate the impact of various optimizations."""
    print('\n' + '=' * 60)
    print('OPTIMIZATION IMPACT ESTIMATES')
    print('=' * 60)

    engine = get_db_engine(test_settings)

    # Run profiling to get base measurements
    Base.metadata.create_all(engine)

    # Measure current per-test overhead (sequence reset)
    def reset_all_sequences():
        with engine.connect() as conn:
            for seq in SEQUENCES_TO_RESET:
                with contextlib.suppress(Exception):
                    conn.execute(text(f'ALTER SEQUENCE {seq} RESTART WITH 1'))
            conn.commit()

    reset_result = time_operation(reset_all_sequences, iterations=10)

    # Measure connection + transaction overhead
    def connection_with_transaction():
        conn = engine.connect()
        txn = conn.begin()
        txn.rollback()
        conn.close()

    txn_result = time_operation(connection_with_transaction, iterations=20)

    print('\nCurrent per-test overhead:')
    print(f'  Sequence reset: {reset_result.mean * 1000:.2f}ms')
    print(f'  Transaction setup/rollback: {txn_result.mean * 1000:.2f}ms')
    print(f'  Total per-test: {(reset_result.mean + txn_result.mean) * 1000:.2f}ms')

    # Estimate with 100 tests
    test_count = 100
    current_total = (reset_result.mean + txn_result.mean) * test_count

    print(f'\nEstimated overhead for {test_count} tests:')
    print(f'  Current: {current_total:.2f}s')

    # If we skip sequence resets (parallel mode)
    parallel_total = txn_result.mean * test_count
    print(f'  With no sequence resets: {parallel_total:.2f}s (save {current_total - parallel_total:.2f}s)')

    # Estimate session-level table operations
    def drop_and_create():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    ddl_result = time_operation(drop_and_create, iterations=3)
    print(f'\nSession-level DDL overhead: {ddl_result.mean:.2f}s')

    return reset_result, txn_result, ddl_result


def main():
    """Run all profiling operations."""
    print('\n' + '=' * 60)
    print('TEST FIXTURE PERFORMANCE PROFILING')
    print('=' * 60)
    print(f'Database: {test_settings.sqlalchemy.host}:{test_settings.sqlalchemy.port}')
    print('=' * 60)

    try:
        count_tables_and_sequences()
        profile_table_operations()
        profile_sequence_resets()
        profile_connection_overhead()
        profile_user_lookup()
        profile_api_creation()
        estimate_optimization_impact()
    except Exception as e:
        print(f'\nError: {e}')
        print('Ensure the test database is running: ./cli/ichrisbirch testing start')
        raise


if __name__ == '__main__':
    main()
# test comment
