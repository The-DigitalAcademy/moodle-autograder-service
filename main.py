import os, sys, json, pika, bleach, logging
from dotenv import load_dotenv
from moodle_service import MoodleService
from github_repository import GitHubRepository
from llm_code_reviewer import LLMCodeReviewer
from status_report_service import StatusReportService

# Load environment variables from .env file
load_dotenv()

# Message queue and GitHub configuration
MQ_HOST = os.getenv("MQ_HOST")
QUEUE = os.getenv("QUEUE")
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "autograder.log")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Only show WARNING and ERROR from Pika
logging.getLogger("pika").setLevel(logging.WARNING)

# ---------------------------------------------------------
# Main Application Logic
# ---------------------------------------------------------
def main() -> None:
    """
    Connects to RabbitMQ and continuously listens for new assignment submissions.

    When a message is received, it processes the submission by:
    - Cleaning and parsing the submission data.
    - Fetching the student’s GitHub repository.
    - Running an LLM-based code review using the provided rubric.
    - Sending structured grading feedback back to Moodle.
    """
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=MQ_HOST))
        channel = connection.channel()

        # Ensure the target queue exists
        channel.queue_declare(queue=QUEUE, durable=True)
        logger.info(f"✅ Connected to RabbitMQ at %s, listening on queue: %s", MQ_HOST, QUEUE)
    except Exception as e:
        logger.exception(f"Failed to connect to RabbitMQ: {e}")
        sys.exit(1)

    def callback(channel, method, properties, body):
        """
        Callback function executed whenever a message (submission) arrives in the queue.

        Args:
            channel: The communication channel with RabbitMQ.
            method: RabbitMQ delivery metadata.
            properties: Message properties.
            body (bytes): The JSON-encoded submission data.
        """

        logger.info("📦 New submission received...")
        try:
            # Parse message from JSON
            submission_data = json.loads(body)

            # Extract relevant fields
            assignmentid = submission_data['assignmentid']
            userid = submission_data['userid']
            assignment_rubric = submission_data["assignmentrubric"]['criteria']

            # Clean potentially unsafe HTML input from Moodle
            github_link = bleach.clean(submission_data["onlinetext"], strip=True)
            activity_instruction = bleach.clean(submission_data["assignmentactivity"], strip=True)

            # Define expected LLM response format
            output_template = """{
                "criteria_results": [ 
                    {
                        "criteria": "<criteriondescription>",
                        "criterionid": "<criterionid>",
                        "remark": "<remarks>",
                        "levelid": "<levelid>"
                    },
                    # // ... more criterions
                ],
                "feedback_comment": "<overall-feedback-comment>"
            }"""

            logger.info("🔍 Fetching repository files from url: %s", github_link)
            repo = GitHubRepository(github_link, GITHUB_TOKEN)
            repo_files = repo.get_files()

            logger.info("🤖 Running AI code review...")
            code_reviewer = LLMCodeReviewer(
                files=repo_files, 
                rubric=json.dumps(assignment_rubric), 
                activity_instruction=activity_instruction, 
                output_template=output_template
            )
            review_result = code_reviewer.get_structured_review()

            logger.info("🎓 Sending grading results to Moodle...")
            MoodleService.save_grade(assignmentid, userid, review_result)

            # Acknowledge message as processed successfully
            channel.basic_ack(delivery_tag = method.delivery_tag)
            logger.info("✅ Submission processed successfully.")

            try:
                StatusReportService.send_report(submission_data, "success", "Autograde completed successfully.")
                logger.info("📝 Sent status report to Autograder Dashboard.")
            except Exception as sub_e:
                logger.warning("📝 Failed to send status report to Autograder Dashboard: %s", sub_e)


        except Exception as e:
            logger.exception("❌ Error processing submission: %s", e)

            # Send autograding report to Autograder Dashboard 
            try:
                StatusReportService.send_report(submission_data, "fail", f"Error autograding submission. {e}")
                channel.basic_ack(delivery_tag = method.delivery_tag)
                logger.info("📝 Sent failure status report for manual intervention.")
            except Exception as sub_e:
                logger.error("📝 Failed to send failure status report: %s", sub_e)
                logger.info("🔄 Requeuing task...")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    # Start consuming messages 
    logger.info("📡 Waiting for new submissions. Press CTRL+C to stop.")
    channel.basic_consume(queue=QUEUE, on_message_callback=callback)

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user. Shutting down gracefully...")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

