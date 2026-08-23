# Drone-simulation

시각장애인이 음성으로 키오스크를 주문할 수 있게 돕는 드론 프로젝트의 개발 환경입니다.

실제 드론 없이, 팀원 모두가 똑같은 환경에서 개발하기 위한 저장소입니다.
리눅스 · 윈도우(WSL) · 맥에서 같은 명령으로 동작합니다.

---

## 지금까지 구현한 것

- 가상 공간에서 MAVSDK로 드론을 조종하기 -> 나중에는 ROS2 로 트론 조작.
- 드론 깊이 카메라(컬러 · 깊이 · 3D 점) 영상을 받아오기
- 드론 상태(위치 · 기울기 · 속도 · 배터리) 실시간으로 받아오기
- 위 영상들을 브라우저에서 보기 — 드론 시점과 맵 카메라 시점 둘 다

---

## Installation

Docker 하나뿐입니다.

**윈도우 · 맥**
[Docker Desktop](https://www.docker.com/products/docker-desktop/) 을 설치합니다.

**리눅스**
```bash
sudo apt install docker.io docker-compose-v2
sudo usermod -aG docker $USER      # 이후 로그아웃했다 다시 로그인
```
`usermod` 를 하지 않으면 모든 명령에 `sudo` 를 붙여야 하고, 나중에 문제가 생깁니다.

---

## Quickstart

```bash
git clone https://github.com/s0nh/Drone-simulation.git
cd Drone-simulation

cp .env.example .env     # 설정 파일 만들기
docker compose up -d     # 시작
```

### 제대로 됐는지 확인

MAVSDK 코드로 드론이 뜨고, 8초 제자리 비행하고, 내려옵니다.

```bash
docker compose exec drone python3 tests/takeoff_test.py
```

마지막 줄에 **PASS** 가 나오면 준비 완료입니다.

```bash
docker compose down      # 끄기
```

---

## 화면으로 보기

브라우저에서 **http://localhost:8080** 을 엽니다. 아래 목록이 나옵니다.

| 이름 | 보이는 것 |
|---|---|
| `/spectator/image_raw` | **3인칭** — 드론을 바깥에서 비추는 고정 카메라 |
| `/camera/image_raw` | 드론이 보는 컬러 영상 |
| `/camera/depth_view` | 드론이 보는 깊이 영상 (가까울수록 밝게) |

3인칭 화면을 띄워 둔 채로 위의 이륙 테스트를 돌리면 드론이 뜨고 내려오는 게 보입니다.

관전 카메라 위치는 `sim/worlds/kiosk.sdf` 의 `spectator_camera` 항목에서 숫자 여섯 개를
고치면 바뀝니다.

### QGroundControl 연결 (선택)

드론 관제 프로그램으로 보고 싶다면, 한 번만 연결을 만들어 주면 됩니다.

`Application Settings` → `Comm Links` → `Add`
- Type: `UDP`
- Server: `127.0.0.1:14550`

---

## 어떻게 돌아가는가

컨테이너 하나로 돌아가고, 그 안에서 아래 다섯 가지가 함께 돕니다.

| 무엇 | 하는 일 |
|---|---|
| PX4 + Gazebo | 비행 제어와 물리 시뮬레이션. 드론과 가상 공간 |
| uXRCE-DDS 통로 | 드론 상태 데이터를 우리 코드가 읽는 형식으로 옮김 |
| 깊이 영상 변환 | 깊이 데이터에 색을 입혀 시각화 |
| 브라우저 뷰어 | 위 영상들을 웹 주소로 열어줌 |

컨테이너가 켜지면 `docker/drone/start.sh` 가 이 순서로 실행합니다.

```
1. 직접 만든 가상 공간·물체를 Gazebo 가 찾을 수 있게 연결
2. 드론 상태 데이터 통로 열기
3. 카메라 영상 중계 시작
4. 깊이 영상 변환 시작
5. 브라우저 뷰어 시작
6. 드론과 가상 공간 띄우기
```

### 이미지 구성

바탕은 PX4 공식 이미지이고, 그 위에 ROS 2 와 우리에게 필요한 도구를 얹었습니다.
설치는 처음 한 번만 실행되고, 우리가 짠 코드는 이미지에 넣지 않고 폴더째로
연결하므로 코드를 고쳐도 다시 빌드하지 않습니다.

---

## ROS2 Topic 이름

### 카메라

| 이름 | 내용 |
|---|---|
| `/camera/image_raw` | 컬러 영상 (1920×1080) |
| `/camera/camera_info` | 렌즈 정보 — 화각, 초점거리. 거리 계산에 필요 |
| `/camera/depth` | 깊이 데이터 (640×480) |
| `/camera/points` | 3D 점 덩어리 — 주변 공간의 입체 형태 |
| `/camera/depth_view` | 깊이 데이터에 색을 입힌 것. 사람이 보는 용도 |
| `/spectator/image_raw` | 관전 카메라 |

### 드론 상태

`/fmu/out/` 으로 시작하는 이름들입니다. 자주 쓸 것은 아래와 같습니다.

| 이름 | 내용 |
|---|---|
| `/fmu/out/vehicle_local_position_v1` | 출발점 기준 현재 위치와 속도 |
| `/fmu/out/vehicle_attitude` | 기울기 |
| `/fmu/out/vehicle_status_v4` | 비행 모드, 시동 상태 |
| `/fmu/out/battery_status_v1` | 배터리 |

---

## 폴더 구조

```
compose.yaml            시뮬레이션 실행 구성
.env.example            설정 템플릿 (.env 로 복사해서 사용)

docker/drone/
  Dockerfile            이미지에 무엇을 설치하는지
  start.sh              컨테이너가 켜질 때 무엇을 어떤 순서로 실행하는지

sim/
  worlds/kiosk.sdf      우리가 쓰는 가상 공간
  models/               직접 만든 가상 물체 — 키오스크 모형이 여기 들어갑니다

vision/
  depth_view.py         깊이 데이터 시각화

tests/
  takeoff_test.py       환경이 정상 작동하는지 확인하는 테스트
```

---

## 새로 만들 때

**가상 공간을 추가하려면**
`sim/worlds/` 에 `.sdf` 파일을 넣고, `.env` 의 `PX4_GZ_WORLD` 에 파일 이름(확장자 제외)을
적습니다. Gazebo 가 기본 제공하는 공간(`default`, `baylands`, `walls` 등)도 이름만 적으면
그대로 쓸 수 있습니다.

**물체를 추가하려면**
`sim/models/` 에 모델 폴더를 넣고, 공간 파일에서 불러옵니다.

**센서를 추가하려면**
`docker/drone/start.sh` 안의 목록에 항목을 하나 더 씁니다.
`gz_topic_name` 이 Gazebo 쪽 원래 이름, `ros_topic_name` 이 우리가 쓸 이름입니다.

**상시 실행할 프로그램을 추가하려면**
`docker/drone/start.sh` 의 6번(드론 시작) 앞에 같은 방식으로 한 줄 추가합니다.

**설치할 도구가 늘어나면**
`docker/drone/Dockerfile` 에 추가하고 `docker compose build drone` 을 한 번 실행합니다.

---

## 실제 장비와의 대응

| 실제 장비 | 시뮬레이션 |
|---|---|
| Holybro X500 V2 + Pixhawk 6C | PX4 시뮬레이터의 `gz_x500_depth` 기체 |
| Intel RealSense D435i (깊이 카메라) | Gazebo 의 깊이 카메라 센서 |


---

## 정해야 할 것

**PX4 버전.** 지금은 `v1.18.0-beta2` 입니다. 아직 정식 버전이 아니라 나중에 바꿔야
할 수 있습니다. 기준은 하나입니다 — **시뮬레이션 PX4 버전 = 실제 드론에 넣을 펌웨어 버전.**
실제 드론 펌웨어를 정하면 `.env` 의 `PX4_IMAGE` 도 같이 맞춥니다.

---

## 앞으로 할 일

1. 가상 공간에 키오스크 세우기 (화면은 Flutter 로 만든 키오스크 이미지를 붙입니다)
2. companion computer 구현 및 드론에 막대기, 라즈베리파이 부착?
3. SLAM, Vision, Ai Agent 개발
4. 음성 명령 받아 주문까지 할 수 있게 연결 
5. 통신이 느려졌을 때 어디까지 버티는지 측정
6. 로봇팔 붙이기 ← 2차 목표
