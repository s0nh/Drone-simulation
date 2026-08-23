# 이 프로젝트의 실행 환경 전체를 담은 이미지.
#
# PX4 공식 시뮬레이션 이미지를 바탕으로 하고, 그 위에 우리에게 필요한 것들을 얹는다.
# 바탕을 그대로 쓰기 때문에 비행 제어 부분은 공식 배포본과 동일하다.
#
# 얹는 것
#   ROS 2            로봇 프로그램들이 데이터를 주고받는 표준 방식
#   카메라 중계       Gazebo 카메라 영상을 ROS 2 형식으로 옮김
#   브라우저 뷰어     그 영상을 웹 주소로 볼 수 있게 함
#   상태 데이터 통로   드론의 위치·기울기·배터리 등을 내보내는 창구
#   MAVSDK           파이썬으로 드론에 명령을 보내는 라이브러리
#
# 아래 설치 단계는 처음 한 번만 실행된다. 우리가 짠 코드는 이미지에 넣지 않고
# 실행할 때 폴더를 연결하므로, 코드를 고쳐도 이미지를 다시 빌드할 필요가 없다.

ARG PX4_IMAGE
FROM ${PX4_IMAGE}

# --- ROS 2 --------------------------------------------------------------------
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl gnupg ca-certificates \
 && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc \
      | gpg --dearmor -o /usr/share/keyrings/ros.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/ros.gpg] http://packages.ros.org/ros2/ubuntu noble main" \
      > /etc/apt/sources.list.d/ros2.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      ros-jazzy-ros-gz-bridge \
      ros-jazzy-web-video-server \
      ros-jazzy-ros2cli \
      ros-jazzy-ros2run \
      ros-jazzy-ros2topic \
      python3-pip \
 && rm -rf /var/lib/apt/lists/*

# --- 드론 상태 데이터 통로 (uXRCE-DDS) ------------------------------------------
# PX4 가 공식으로 지원하는 ROS 2 연결 방식이다. 양쪽이 한 쌍으로 동작한다.
#
#   드론 쪽    uxrce_dds_client  — PX4 에 이미 내장돼 있음
#   보조 컴퓨터 쪽 MicroXRCEAgent — 여기서 설치하는 것
#
# 실제 환경에서는 보조 컴퓨터에서 도는 프로그램이라 PX4 이미지에는 들어 있지 않다.
# 미리 만들어진 패키지가 없어서 소스에서 직접 빌드한다.
ARG XRCE_AGENT_VERSION=v3.0.1
RUN apt-get update \
 && apt-get install -y --no-install-recommends git cmake build-essential \
 && git clone -b ${XRCE_AGENT_VERSION} --depth 1 \
      https://github.com/eProsima/Micro-XRCE-DDS-Agent.git /tmp/agent \
 && cmake -S /tmp/agent -B /tmp/agent/build -DCMAKE_BUILD_TYPE=Release \
 && cmake --build /tmp/agent/build -j"$(nproc)" \
 && cmake --build /tmp/agent/build --target install \
 && ldconfig \
 && rm -rf /tmp/agent /var/lib/apt/lists/*

# --- 드론 조종 MAVSDK -----------------------------------------------------------------
RUN pip install --no-cache-dir --break-system-packages "mavsdk>=2.0,<3.0"

COPY start.sh /start.sh
RUN chmod +x /start.sh

WORKDIR /work

ENTRYPOINT ["/start.sh"]
