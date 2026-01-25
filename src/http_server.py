import logging
from flask import Flask, Response, jsonify
from truenas_api_client import Client
from options import Options
from job_fetcher import fetch_all_jobs

logger = logging.getLogger(__name__)


def create_app(options: Options) -> Flask:
    """
    Creates and configures the Flask application.
    
    :param options: The parsed options for the application.
    :return: A configured Flask app instance.
    """
    app = Flask(__name__)

    @app.route(f'/{options.calendar_name}', methods=['GET'])
    def get_calendar():
        """
        HTTP GET endpoint that returns an iCalendar representation of TrueNAS jobs.
        """
        try:
            logger.info(f"Received request for calendar: {options.calendar_name}")
            
            # Connect to TrueNAS and fetch jobs
            with Client(
                uri=f"wss://{options.truenas_host}/api/current",
                verify_ssl=options.truenas_host_verify_ssl
            ) as truenas_client:
                login_result = truenas_client.call("auth.login_with_api_key", options.truenas_api_key)
                
                if not login_result:
                    logger.error("Failed to authenticate with TrueNAS.")
                    return jsonify({"error": "Failed to authenticate with TrueNAS"}), 500
                
                logger.info("Successfully logged into TrueNAS.")
                
                # Fetch jobs and create calendar
                cal = fetch_all_jobs(options, truenas_client)
                
                # Return iCalendar response
                ical_string = cal.to_ical().decode('utf-8')
                logger.info(f"Returning iCalendar with {len(cal.subcomponents)} events.")
                
                return Response(
                    ical_string,
                    mimetype='text/calendar; charset=utf-8',
                    headers={
                        'Content-Disposition': f'attachment; filename="{options.calendar_name}.ics"'
                    }
                )
        
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint.
        """
        return jsonify({"status": "healthy"}), 200

    return app


def run_server(options: Options):
    """
    Starts the HTTP server.
    
    :param options: The parsed options for the application.
    """
    app = create_app(options)
    logger.info(f"Starting HTTP server on port {options.http_port}")
    logger.info(f"Calendar endpoint: http://localhost:{options.http_port}/{options.calendar_name}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=options.http_port, debug=False)
