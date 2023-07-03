from aiotaskq.exceptions import UrlNotSupported
from aiotaskq.pubsub import PubSub


def test_invalid_url():
    # Given an unsupported pubsub url
    unsupported_pubsub_url = "cache+memcached://127.0.0.1:11211/"

    # When getting a pubsub instance using the url
    error = None
    try:
        PubSub.get(url=unsupported_pubsub_url, poll_interval_s=1.0)
    except UrlNotSupported as err:
        error = err
    finally:
        # Then a helpful error should be raised
        assert str(error) == 'Url "cache+memcached://127.0.0.1:11211/" is currently not supported.'
