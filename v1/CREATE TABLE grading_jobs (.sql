CREATE TABLE grading_jobs (
    id SERIAL PRIMARY KEY,
    userid TEXT NOT NULL,
    github_link TEXT NOT NULL,
    question TEXT NOT NULL,
    rubric JSONB,
    assignmentid TEXT,
    assignmentname TEXT,
    assignmentintro TEXT,
    status TEXT DEFAULT 'queued',
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trigger function for LISTEN/NOTIFY
CREATE OR REPLACE FUNCTION notify_new_grading_job() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('new_grading_job', NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER grading_job_insert_trigger
AFTER INSERT ON grading_jobs
FOR EACH ROW
EXECUTE FUNCTION notify_new_grading_job();
