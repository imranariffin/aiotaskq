from aiotaskq.exceptions import ConcurrencyTypeNotSupported
from aiotaskq.concurrency_manager import ConcurrencyManager


def test_unsupported_concurrency_type():
    # Given an incorrect concurrency type
    incorrect_concurrency_type = "some-incorrect-concurrency-type"

    # When getting the concurrency manager
    error = None
    try:
        ConcurrencyManager._instance = None
        ConcurrencyManager.get(concurrency_type=incorrect_concurrency_type, concurrency=4)
    except ConcurrencyTypeNotSupported as e:
        error = e
    finally:
        # Then a helpful error should be raised
        assert (
            str(error) == 'Concurrency type "some-incorrect-concurrency-type" is not yet supported.'
        )
