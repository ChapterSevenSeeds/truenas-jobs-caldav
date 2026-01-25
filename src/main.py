import logging
from options import Options
from http_server import run_server
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the TrueNAS Jobs HTTP server.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Parse options from environment variables
    try:
        options = Options.from_env()
        logger.info(f"Configuration loaded successfully.")
        logger.info(f"Calendar name: {options.calendar_name}")
        logger.info(f"HTTP port: {options.http_port}")
        logger.info(f"TrueNAS host: {options.truenas_host}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

    # Start HTTP server
    try:
        run_server(options)
    except Exception as e:
        logger.error(f"Error running HTTP server: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
