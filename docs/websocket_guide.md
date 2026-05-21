# 실시간 채팅 WebSocket 연동 가이드

본 문서는 프론트엔드 개발자가 채팅방 실시간 통신(WebSocket)을 연동하기 위해 필요한 정보를 제공합니다.

## 1. 엔드포인트

WebSocket 서버는 다음 URL을 통해 연결을 수립합니다.

```text
ws://<API_서버_주소>/ws/chat-rooms/{room_id}?user_id={user_id}
```

* `room_id`: 연결하고자 하는 채팅방의 ID
* `user_id`: 현재 로그인한 사용자의 ID (현재 데모 버전에서는 JWT를 대신하여 쿼리 파라미터로 직접 `user_id`를 전달합니다.)

**예시:**
```text
ws://localhost:8000/ws/chat-rooms/42?user_id=7
```

---

## 2. 메시지 송수신 포맷

WebSocket 통신은 모두 **JSON 문자열** 형태로 이루어집니다. `JSON.stringify()` 와 `JSON.parse()` 를 사용해주세요.

### 2.1. 메시지 전송 (클라이언트 ➡ 서버)

사용자가 채팅방에 메시지를 보낼 때 사용하는 포맷입니다.

```json
{
  "message_content": "안녕하세요! 프로젝트 회의 시작할까요?"
}
```

### 2.2. 메시지 수신 (서버 ➡ 클라이언트 브로드캐스트)

누군가 메시지를 보내면, 채팅방에 연결된 **모든 사용자(본인 포함)** 에게 메시지가 브로드캐스트됩니다. 이 구조를 받아 UI에 렌더링하세요.

```json
{
  "id": 153,
  "room_id": 42,
  "sender_id": 7,
  "sender_name": "홍길동",
  "message_content": "안녕하세요! 프로젝트 회의 시작할까요?",
  "created_at": "2026-05-21T14:00:00.123456+00:00"
}
```

---

## 3. 에러 핸들링

잘못된 형식의 데이터를 보내거나, 서버에서 처리 중 문제가 발생할 경우 에러 메시지가 JSON 포맷으로 내려옵니다.
이벤트 리스너의 `onmessage` 에서 에러 필드를 확인해주세요.

```json
{
  "error": "메시지 내용이 없습니다."
}
```

또한, 연결 권한이 없거나 사용자를 찾을 수 없는 경우 다음과 같은 HTTP/WebSocket Close 코드로 연결이 종료될 수 있습니다.
* **Code 4001**: 쿼리 파라미터 유효성 에러 (토큰/user_id 오류)
* **Code 4003**: 해당 채팅방의 멤버가 아니거나 사용자를 찾을 수 없음

---

## 4. 프론트엔드 연동 예제 (JavaScript / TypeScript)

React/Vue 등에서 사용하기 위한 간단한 연동 예제입니다.

```javascript
const roomId = 42;
const userId = 7;
const wsUrl = `ws://localhost:8000/ws/chat-rooms/${roomId}?user_id=${userId}`;

// 1. WebSocket 연결 수립
const socket = new WebSocket(wsUrl);

socket.onopen = () => {
  console.log('채팅방에 성공적으로 연결되었습니다.');
};

// 2. 메시지 수신 처리
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.error) {
    console.error('서버 에러:', data.error);
    return;
  }
  
  // UI 렌더링 함수 호출
  console.log(`[${data.sender_name}]: ${data.message_content}`);
  // appendMessageToUI(data);
};

// 3. 연결 종료 및 에러 처리
socket.onclose = (event) => {
  console.log('채팅방 연결이 종료되었습니다.', event.code, event.reason);
  // 재연결 로직 추가 권장 (Reconnecting WebSocket)
};

socket.onerror = (error) => {
  console.error('웹소켓 통신 에러 발생:', error);
};

// 4. 메시지 전송 함수
function sendMessage(text) {
  if (socket.readyState === WebSocket.OPEN) {
    const payload = { message_content: text };
    socket.send(JSON.stringify(payload));
  } else {
    console.error('WebSocket이 아직 연결되지 않았습니다.');
  }
}

// 사용 예시
// sendMessage("다들 진행상황 어떠신가요?");
```

## 5. 주의 사항

1. **자동 재연결(Auto-Reconnect)**: 네트워크 불안정 등으로 연결이 끊길 수 있으므로, 프론트엔드 측에서 재연결 로직을 구현하는 것을 권장합니다.
2. **이전 대화 기록**: WebSocket은 **연결된 이후의 메시지만** 수신합니다. 방에 입장할 때는 기존 REST API (`GET /api/chat-rooms/{room_id}/messages`)를 호출하여 이전 대화 내역을 먼저 불러온 후 화면에 채워 넣어야 합니다.
