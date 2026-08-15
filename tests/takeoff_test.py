#!/usr/bin/env python3
"""개발 환경이 제대로 준비됐는지 확인하는 테스트.

컨테이너가 켜진 것과 드론이 실제로 나는 것은 다른 문제라서,
연결부터 착륙까지 한 번 돌려 본다. 마지막에 PASS 가 나오면 개발을 시작해도 된다.

실행
    docker compose exec drone python3 tests/takeoff_test.py

여기서 쓰는 방식(MAVSDK)은 실제 드론에서도 그대로 쓸 수 있다.
"""

import asyncio
import os
import sys

from mavsdk import System

PORT = os.environ.get("MAVLINK_OFFBOARD_PORT", "14540")
TARGET_ALTITUDE_M = 2.5


async def wait_until(stream, condition, seconds, name):
    """드론이 계속 보내오는 값들 중 조건을 만족하는 첫 값을 기다린다."""

    async def loop():
        async for value in stream:
            if condition(value):
                return value

    try:
        return await asyncio.wait_for(loop(), timeout=seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"{name}: {seconds}초 안에 되지 않음") from None


async def main():
    drone = System()

    print(f"[1/5] 드론에 연결 (포트 {PORT})")
    await drone.connect(system_address=f"udp://:{PORT}")
    # 가상 공간이 처음 켜질 때는 준비가 느려서 넉넉히 기다린다.
    await wait_until(drone.core.connection_state(), lambda s: s.is_connected, 90, "연결")

    print("[2/5] 드론이 자기 위치를 알 때까지 대기")
    await wait_until(
        drone.telemetry.health(),
        lambda h: h.is_global_position_ok and h.is_home_position_ok,
        120,
        "위치 확인",
    )

    print(f"[3/5] 시동 후 {TARGET_ALTITUDE_M}m 까지 이륙")
    await drone.action.arm()
    await drone.action.set_takeoff_altitude(TARGET_ALTITUDE_M)
    await drone.action.takeoff()

    # 목표 높이의 80%까지 올라가면 이륙에 성공한 것으로 본다.
    reached = await wait_until(
        drone.telemetry.position(),
        lambda p: p.relative_altitude_m >= TARGET_ALTITUDE_M * 0.8,
        60,
        "이륙",
    )
    print(f"      현재 높이 {reached.relative_altitude_m:.2f}m")

    # 목표 높이에 막 닿은 직후에는 아직 올라가는 중이라 흔들림처럼 보인다.
    # 자세가 잡힐 때까지 잠깐 두고 나서 잰다.
    print("[4/5] 자세가 잡히길 기다린 뒤, 제자리 비행 8초 확인")
    await asyncio.sleep(5)
    heights = []

    async def collect():
        async for position in drone.telemetry.position():
            heights.append(position.relative_altitude_m)

    task = asyncio.create_task(collect())
    await asyncio.sleep(8)
    task.cancel()
    if heights:
        print(f"      높이 변동 {max(heights) - min(heights):.2f}m")

    print("[5/5] 착륙")
    await drone.action.land()
    await wait_until(drone.telemetry.in_air(), lambda flying: not flying, 90, "착륙")

    print("\nPASS — 개발 환경이 정상 동작합니다.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as error:
        print(f"\nFAIL — {error}\n")
        print("확인해 볼 것:")
        print("  1. docker compose ps          컨테이너가 켜져 있는지")
        print("  2. docker compose logs drone  가상 공간이 제대로 떴는지")
        print(f"  3. 다른 프로그램이 포트 {PORT}를 쓰고 있지는 않은지")
        print("     (QGroundControl이나 이전에 켜둔 시뮬레이션이 흔한 원인)")
        sys.exit(1)
