-- SQL Server schema for CookSmart application
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/* =========================
   users
   ========================= */
IF OBJECT_ID('dbo.users','U') IS NULL
BEGIN
  CREATE TABLE dbo.users (
    userid        INT            NOT NULL IDENTITY(1,1) PRIMARY KEY,
    username      NVARCHAR(255)  NULL,
    password_hash NVARCHAR(255)  NULL,
    Email         NVARCHAR(255)  NULL,
    Phone         NVARCHAR(50)   NULL
  );
END
GO

/* =========================
   recipes
   ========================= */
IF OBJECT_ID('dbo.recipes','U') IS NULL
BEGIN
  CREATE TABLE dbo.recipes (
    recipeid       INT            NOT NULL IDENTITY(1,1) PRIMARY KEY,
    name           NVARCHAR(255)  NULL,
    category       NVARCHAR(100)  NULL,
    area           NVARCHAR(100)  NULL,
    instructions   TEXT           NULL,         -- kept as TEXT for compatibility
    thumbnail_url  NVARCHAR(1024) NULL,
    ingredients    TEXT           NULL          -- kept as TEXT for compatibility
  );
END
GO

/* =========================
   favorites
   ========================= */
IF OBJECT_ID('dbo.favorites','U') IS NULL
BEGIN
  CREATE TABLE dbo.favorites (
    userid   INT NOT NULL,
    recipeid INT NOT NULL,
    CONSTRAINT PK_favorites PRIMARY KEY (userid, recipeid),
    CONSTRAINT FK_favorites_users
      FOREIGN KEY (userid) REFERENCES dbo.users(userid) ON DELETE CASCADE,
    CONSTRAINT FK_favorites_recipes
      FOREIGN KEY (recipeid) REFERENCES dbo.recipes(recipeid) ON DELETE CASCADE
  );
END
GO

/* =========================
   documents
   ========================= */
IF OBJECT_ID('dbo.documents','U') IS NULL
BEGIN
  CREATE TABLE dbo.documents (
    doc_id     INT            NOT NULL IDENTITY(1,1) PRIMARY KEY,
    title      NVARCHAR(255)  NULL,
    source     NVARCHAR(255)  NULL,
    created_at DATETIME       NULL DEFAULT(GETDATE())
  );
END
GO

/* =========================
   chunks
   ========================= */
IF OBJECT_ID('dbo.chunks','U') IS NULL
BEGIN
  CREATE TABLE dbo.chunks (
    chunk_id  INT            NOT NULL IDENTITY(1,1) PRIMARY KEY,
    doc_id    INT            NULL,
    content   NVARCHAR(MAX)  NULL,
    embedding NVARCHAR(MAX)  NULL,
    ord       INT            NULL,
    CONSTRAINT FK_chunks_documents
      FOREIGN KEY (doc_id) REFERENCES dbo.documents(doc_id) ON DELETE CASCADE
  );
  CREATE INDEX IX_chunks_doc_ord ON dbo.chunks(doc_id, ord);
END
GO

/* =========================
   chat_sessions
   ========================= */
IF OBJECT_ID('dbo.chat_sessions','U') IS NULL
BEGIN
  CREATE TABLE dbo.chat_sessions (
    session_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
    user_id    INT              NULL,
    created_at DATETIME         NULL DEFAULT(GETDATE()),
    CONSTRAINT FK_chat_sessions_users
      FOREIGN KEY (user_id) REFERENCES dbo.users(userid)
  );
END
GO

/* =========================
   chat_messages
   ========================= */
IF OBJECT_ID('dbo.chat_messages','U') IS NULL
BEGIN
  CREATE TABLE dbo.chat_messages (
    msg_id     INT              NOT NULL IDENTITY(1,1) PRIMARY KEY,
    session_id UNIQUEIDENTIFIER NULL,
    role       NVARCHAR(50)     NULL,
    content    NVARCHAR(MAX)    NULL,
    created_at DATETIME         NULL DEFAULT(GETDATE()),
    CONSTRAINT FK_chat_messages_sessions
      FOREIGN KEY (session_id) REFERENCES dbo.chat_sessions(session_id) ON DELETE CASCADE
  );
  CREATE INDEX IX_chat_messages_session_time ON dbo.chat_messages(session_id, created_at);
END
GO

/* =========================
   logs
   ========================= */
IF OBJECT_ID('dbo.logs','U') IS NULL
BEGIN
  CREATE TABLE dbo.logs (
    logid    INT          NOT NULL IDENTITY(1,1) PRIMARY KEY,
    userid   INT          NULL,
    action   VARCHAR(255) NULL,
    details  TEXT         NULL,     -- kept as TEXT for compatibility
    log_time DATETIME     NULL DEFAULT(GETDATE()),
    CONSTRAINT FK_logs_users
      FOREIGN KEY (userid) REFERENCES dbo.users(userid)
  );
END
GO

/* =========================
   events (Event Store)
   ========================= */
IF OBJECT_ID('dbo.events','U') IS NULL
BEGIN
  CREATE TABLE dbo.events (
    event_id        BIGINT         NOT NULL IDENTITY(1,1) PRIMARY KEY,
    aggregate_type  NVARCHAR(50)   NOT NULL,
    aggregate_id    BIGINT         NULL,
    event_type      NVARCHAR(50)   NOT NULL,
    event_version   INT            NOT NULL,
    payload         NVARCHAR(MAX)  NULL,
    occurred_at     DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
    user_id         INT            NULL,
    CONSTRAINT FK_events_users
      FOREIGN KEY (user_id) REFERENCES dbo.users(userid)
  );

  -- Recommended indexes for event sourcing
  CREATE UNIQUE INDEX UX_events_agg_ver
    ON dbo.events(aggregate_type, aggregate_id, event_version);

  CREATE INDEX IX_events_time
    ON dbo.events(occurred_at DESC);
END
GO
