#!/usr/bin/env python3
"""깊이 영상을 눈으로 볼 수 있게 색을 입혀 다시 내보낸다.

깊이 카메라가 주는 원본(/camera/depth)은 그림이 아니라 숫자다.
각 점의 값이 "그 방향으로 몇 미터 떨어져 있는가"라서, 그대로 화면에 그리면
값이 3.5 정도라 거의 검게 보인다. 거리 계산에는 이 원본을 써야 하고,
사람이 확인할 때는 이 프로그램이 만든 /camera/depth_view 를 보면 된다.

색 규칙
    가까움 → 밝음,  멈  → 어두움,  닿는 곳 없음 → 검정

실행 (컨테이너가 켜질 때 자동으로 함께 실행된다)
    ros2 run 없이 그냥:  python3 vision/depth_view.py
"""

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

# 이 범위를 벗어나는 거리는 양 끝 색으로 몰아서 표시한다.
NEAR_M = 0.3
FAR_M = 10.0


class DepthView(Node):
    def __init__(self):
        super().__init__("depth_view")
        self.publisher = self.create_publisher(Image, "/camera/depth_view", 1)
        self.create_subscription(Image, "/camera/depth", self.on_depth, 1)

    def on_depth(self, msg: Image) -> None:
        # 원본은 픽셀 하나가 32비트 실수(미터)로 들어 있다.
        distances = np.frombuffer(msg.data, dtype=np.float32).reshape(msg.height, msg.width)

        # 닿는 곳이 없는 방향은 무한대나 빈 값으로 온다. 가장 먼 거리로 취급한다.
        distances = np.nan_to_num(distances, nan=FAR_M, posinf=FAR_M, neginf=FAR_M)

        # 거리 범위를 밝기 0~255 로 옮긴다. 가까울수록 밝게.
        clipped = np.clip(distances, NEAR_M, FAR_M)
        brightness = (1.0 - (clipped - NEAR_M) / (FAR_M - NEAR_M)) * 255.0

        out = Image()
        out.header = msg.header
        out.height = msg.height
        out.width = msg.width
        out.encoding = "mono8"
        out.step = msg.width
        out.data = brightness.astype(np.uint8).tobytes()
        self.publisher.publish(out)


def main() -> None:
    rclpy.init()
    node = DepthView()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
