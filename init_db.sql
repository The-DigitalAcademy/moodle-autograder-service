CREATE TABLE IF NOT EXISTS grading_jobs (
    id SERIAL PRIMARY KEY,
    userid TEXT,
    question TEXT,
    github_link TEXT,
    rubric JSONB,
    assignmentid TEXT,
    assignmentname TEXT,
    assignmentintro TEXT,
    status TEXT DEFAULT 'queued',
    attempts INTEGER DEFAULT 0,
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trigger function for notify
CREATE OR REPLACE FUNCTION notify_new_grading_job() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('new_grading_job', NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS grading_job_insert_trigger ON grading_jobs;
CREATE TRIGGER grading_job_insert_trigger
AFTER INSERT ON grading_jobs
FOR EACH ROW
EXECUTE FUNCTION notify_new_grading_job();
