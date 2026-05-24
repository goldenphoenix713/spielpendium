# Gunicorn configuration file for Spielpendium
# Reference: https://docs.gunicorn.org/en/stable/configure.html

# Worker timeout in seconds.
# PDF catalog generation for large collections can be CPU-intensive (especially image processing).
# We increase the timeout to 120 seconds to prevent worker terminations.
timeout = 120

# Number of worker processes.
# Render's resource constraints usually function best with 2-4 workers.
workers = 4
