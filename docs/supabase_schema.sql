-- ============================================================
-- TeamTeam 데이터베이스 스키마
-- 테이블명: 소문자 snake_case (PostgreSQL 권장 컨벤션)
-- ============================================================

-- 1. user 테이블
CREATE TABLE "user" (
    id               SERIAL PRIMARY KEY,
    email            VARCHAR(255) NOT NULL UNIQUE,
    password         VARCHAR(255) NOT NULL,
    name             VARCHAR(50)  NOT NULL,
    department       VARCHAR(100),
    student_id       VARCHAR(100),
    profile_image_url TEXT,
    residence        VARCHAR(100),
    intro            TEXT,
    created_at       TIMESTAMP DEFAULT NOW()
);

-- 2. team 테이블
CREATE TABLE team (
    id           SERIAL PRIMARY KEY,
    team_name    VARCHAR(100) NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    invite_code  VARCHAR(50)  NOT NULL UNIQUE,
    status       VARCHAR(50)  NOT NULL DEFAULT '진행중',
    deadline     DATE,
    leader_id    INTEGER      NOT NULL REFERENCES "user"(id),
    created_at   TIMESTAMP DEFAULT NOW()
);

-- 3. team_member 테이블
CREATE TABLE team_member (
    id        SERIAL PRIMARY KEY,
    team_id   INTEGER NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    user_id   INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (team_id, user_id)
);

-- 4. ai_schedule_session 테이블
CREATE TABLE ai_schedule_session (
    id         SERIAL PRIMARY KEY,
    team_id    INTEGER      NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    goal       VARCHAR(255) NOT NULL,
    deadline   DATE,
    status     VARCHAR(50)  DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. ai_schedule_task 테이블
CREATE TABLE ai_schedule_task (
    id         SERIAL PRIMARY KEY,
    session_id INTEGER      NOT NULL REFERENCES ai_schedule_session(id) ON DELETE CASCADE,
    task_name  VARCHAR(100) NOT NULL,
    start_date DATE,
    due_date   DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. task 테이블
CREATE TABLE task (
    id          SERIAL PRIMARY KEY,
    team_id     INTEGER      NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    assignee_id INTEGER      REFERENCES "user"(id),
    task_name   VARCHAR(100) NOT NULL,
    due_date    DATE,
    status      VARCHAR(50)  DEFAULT 'To do',
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- 7. notice 테이블
CREATE TABLE notice (
    id               SERIAL PRIMARY KEY,
    team_id          INTEGER      NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    author_id        INTEGER      NOT NULL REFERENCES "user"(id),
    title            VARCHAR(100) NOT NULL,
    content          TEXT         NOT NULL,
    is_leader_notice BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP DEFAULT NOW()
);

-- 8. evaluation 테이블
CREATE TABLE evaluation (
    id                    SERIAL PRIMARY KEY,
    team_id               INTEGER  NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    evaluator_id          INTEGER  NOT NULL REFERENCES "user"(id),
    evaluatee_id          INTEGER  NOT NULL REFERENCES "user"(id),
    score_participation   SMALLINT CHECK (score_participation   BETWEEN 1 AND 5),
    score_responsibility  SMALLINT CHECK (score_responsibility  BETWEEN 1 AND 5),
    score_communication   SMALLINT CHECK (score_communication   BETWEEN 1 AND 5),
    score_collaboration   SMALLINT CHECK (score_collaboration   BETWEEN 1 AND 5),
    score_creativity      SMALLINT CHECK (score_creativity      BETWEEN 1 AND 5),
    comment               TEXT,
    created_at            TIMESTAMP DEFAULT NOW(),
    UNIQUE (team_id, evaluator_id, evaluatee_id)
);

-- 9. reference_room 테이블
CREATE TABLE reference_room (
    id          SERIAL PRIMARY KEY,
    team_id     INTEGER      NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    uploader_id INTEGER      NOT NULL REFERENCES "user"(id),
    file_name   VARCHAR(255) NOT NULL,
    file_url    TEXT         NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 10. chat_room 테이블
CREATE TABLE chat_room (
    id         SERIAL PRIMARY KEY,
    team_id    INTEGER     NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    room_name  VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 11. chat_room_member 테이블
CREATE TABLE chat_room_member (
    room_id   INTEGER NOT NULL REFERENCES chat_room(id) ON DELETE CASCADE,
    user_id   INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (room_id, user_id)
);

-- 12. chat_message 테이블
CREATE TABLE chat_message (
    id              SERIAL PRIMARY KEY,
    room_id         INTEGER NOT NULL REFERENCES chat_room(id) ON DELETE CASCADE,
    sender_id       INTEGER NOT NULL REFERENCES "user"(id),
    message_content TEXT    NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 성능 인덱스
-- ============================================================
CREATE INDEX idx_task_assignee_status  ON task(assignee_id, status);
CREATE INDEX idx_team_invite_code      ON team(invite_code);
CREATE INDEX idx_team_member_user      ON team_member(user_id);
CREATE INDEX idx_notice_team           ON notice(team_id, created_at DESC);
CREATE INDEX idx_chat_message_room     ON chat_message(room_id, created_at);