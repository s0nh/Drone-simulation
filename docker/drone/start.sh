#!/usr/bin/env bash
#
# 컨테이너가 켜질 때 실행되는 스크립트.
#
# 실행 순서
#   1. 직접 만든 가상 공간과 물체를 Gazebo 가 찾을 수 있게 연결한다
#   2. 드론 상태 데이터 통로를 연다  (uXRCE-DDS. 위치·기울기·배터리 등이 나가는 창구)
#   3. 카메라 영상 중계를 켠다        (Gazebo 카메라 → ROS 2 형식)
#   4. 깊이 영상에 색을 입히는 프로그램을 켠다
#   5. 브라우저 뷰어를 켠다           (http://localhost:8080)
#   6. 드론(PX4)과 가상 공간을 띄운다
#
# 2~5번은 뒤에서 조용히 돌고, 화면에 보이는 것은 6번의 드론 로그다.
# 2~5번의 기록은 logs/ 폴더에 기능별 파일로 쌓인다.
#
# 상시 실행할 기능을 추가하려면 6번 앞에 같은 방식으로 한 줄 추가하면 된다.
#
set -e

# ROS 2 는 Gazebo 라이브러리 사본을 함께 들고 온다.
# 그것을 전체 환경에 적용하면 PX4 가 쓰는 Gazebo 와 섞여서 시뮬레이터가 아예 뜨지 않는다.
# 그래서 ROS 환경은 ROS 프로그램을 실행할 때만 적용한다.
ros_run() {
  ( source /opt/ros/jazzy/setup.bash && exec "$@" )
}

echo "[1/6] 직접 만든 가상 공간·물체 연결"
# 이렇게 연결해 두면 Gazebo 가 기본 제공하는 공간과 우리가 만든 공간을
# 둘 다 이름으로 고를 수 있다.
ln -sf /work/sim/worlds/*.sdf /opt/px4-gazebo/share/gz/worlds/ 2>/dev/null || true
ln -sfn /work/sim/models/*   /opt/px4-gazebo/share/gz/models/ 2>/dev/null || true

WORLD="${PX4_GZ_WORLD:-default}"

# Gazebo 안에서 드론에 붙는 이름.
# PX4_SIM_MODEL 이 gz_x500_depth 이면 실제 이름은 x500_depth_0 이 된다.
MODEL="${PX4_SIM_MODEL#gz_}_0"
CAMERA="/world/${WORLD}/model/${MODEL}/link/camera_link/sensor/IMX214"

# Gazebo 가 내보내는 카메라 데이터를 우리가 쓸 이름으로 바꿔 옮기는 목록.
#   gz_topic_name  = Gazebo 쪽 원래 이름 (길고 기체 이름이 섞여 있다)
#   ros_topic_name = 우리 코드가 쓸 이름
# 센서를 더 연결하려면 여기에 항목을 추가한다.
cat > /tmp/camera_bridge.yaml <<EOF
- ros_topic_name: "/camera/image_raw"
  gz_topic_name: "${CAMERA}/image"
  ros_type_name: "sensor_msgs/msg/Image"
  gz_type_name: "gz.msgs.Image"
  direction: GZ_TO_ROS

- ros_topic_name: "/camera/camera_info"
  gz_topic_name: "${CAMERA}/camera_info"
  ros_type_name: "sensor_msgs/msg/CameraInfo"
  gz_type_name: "gz.msgs.CameraInfo"
  direction: GZ_TO_ROS

- ros_topic_name: "/camera/depth"
  gz_topic_name: "/depth_camera"
  ros_type_name: "sensor_msgs/msg/Image"
  gz_type_name: "gz.msgs.Image"
  direction: GZ_TO_ROS

- ros_topic_name: "/camera/points"
  gz_topic_name: "/depth_camera/points"
  ros_type_name: "sensor_msgs/msg/PointCloud2"
  gz_type_name: "gz.msgs.PointCloudPacked"
  direction: GZ_TO_ROS

# 드론을 바깥에서 비추는 관전 카메라. kiosk 공간에만 있다.
- ros_topic_name: "/spectator/image_raw"
  gz_topic_name: "/spectator"
  ros_type_name: "sensor_msgs/msg/Image"
  gz_type_name: "gz.msgs.Image"
  direction: GZ_TO_ROS
EOF

echo "[2/6] 드론 상태 데이터 통로 (uXRCE-DDS)"
MicroXRCEAgent udp4 -p "${XRCE_PORT:-8888}" > /work/log/data-link.log 2>&1 &

echo "[3/6] 카메라 영상 중계 (기체: ${MODEL}, 공간: ${WORLD})"
ros_run ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=/tmp/camera_bridge.yaml \
  > /work/log/camera-bridge.log 2>&1 &

echo "[4/6] 깊이 영상 보기용 변환"
ros_run python3 /work/vision/depth_view.py > /work/log/depth-view.log 2>&1 &

echo "[5/6] 브라우저 뷰어 → http://localhost:${VIEWER_PORT:-8080}"
ros_run ros2 run web_video_server web_video_server \
  --ros-args -p port:=8080 \
  > /work/log/viewer.log 2>&1 &

echo "[6/6] 드론 시작"
exec /opt/px4-gazebo/bin/px4-entrypoint.sh "$@"
