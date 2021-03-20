client_id = "YOUR CLIENT ID HERE"
client_secret = "YOUR CLIENT SECRET"
client_resource = "http://my-data-platform"

host = "https://my-data-platform.com"
base_path = "/api/"

# Try to use a local settings file if available
try:
    from local_settings import * # noqa
except ImportError:
    pass
