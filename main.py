import os, sys, json, pika, bleach
from dotenv import load_dotenv
from moodle_service import MoodleService
from github_repository import GitHubRepository
from llm_code_reviewer import LLMCodeReviewer

# Load environment variables from .env file
load_dotenv()

# Message queue and GitHub configuration
MQ_HOST = os.getenv("MQ_HOST")
QUEUE = os.getenv("QUEUE")
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')


def main() -> None:
    """
    Connects to RabbitMQ and continuously listens for new assignment submissions.

    When a message is received, it processes the submission by:
    - Cleaning and parsing the submission data.
    - Fetching the student’s GitHub repository.
    - Running an LLM-based code review using the provided rubric.
    - Sending structured grading feedback back to Moodle.
    """

    # Connect to RabbitMQ
    connection = pika.BlockingConnection( pika.ConnectionParameters(host=MQ_HOST))
    channel = connection.channel()

    # Ensure the target queue exists
    channel.queue_declare(queue=QUEUE, durable=True)
    print(f"✅ Connected to RabbitMQ at {MQ_HOST}, listening on queue: {QUEUE}")

    # Define the message callback handler
    def callback(channel, method, properties, body):
        """
        Callback function executed whenever a message (submission) arrives in the queue.

        Args:
            channel: The communication channel with RabbitMQ.
            method: RabbitMQ delivery metadata.
            properties: Message properties.
            body (bytes): The JSON-encoded submission data.
        """

        print("📦 New submission received...")
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

            print("🔍 Fetching repository files...")
            repo = GitHubRepository(github_link, GITHUB_TOKEN)
            repo_files = repo.get_files()

            print("🤖 Running AI code review...")
            code_reviewer = LLMCodeReviewer(
                files=repo_files, 
                rubric=json.dumps(assignment_rubric), 
                activity_instruction=activity_instruction, 
                output_template=output_template
            )
            review_result = code_reviewer.get_structured_review()
            
            print("🎓 Sending grading results to Moodle...")
            MoodleService.save_grade(assignmentid, userid, review_result)

            # Acknowledge message as processed successfully
            channel.basic_ack(delivery_tag = method.delivery_tag)
            print("✅ Submission processed successfully.\n")
        except Exception as e:
            # Log and report any failures
            print(f"❌ Error processing submission: {e}")
            print(f"----- TASK FAILED -----\n")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    # Start consuming messages 
    print("📡 Waiting for new submissions. Press CTRL+C to stop.\n")
    channel.basic_consume(queue=QUEUE, on_message_callback=callback)

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Interrupted by user. Shutting down gracefully...")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

