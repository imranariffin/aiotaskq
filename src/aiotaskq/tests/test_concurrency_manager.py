from aiotaskq.exceptions import ConcurrencyTypeNotSupported
from aiotaskq.concurrency_manager import ConcurrencyManagerSingleton


def test_unsupported_concurrency_type():
    # Given an incorrect concurrency type
    incorrect_concurrency_type = "some-incorrect-concurrency-type"

    # When getting the concurrency manager
    error = None
    try:
        ConcurrencyManagerSingleton.reset()
        ConcurrencyManagerSingleton.get(concurrency_type=incorrect_concurrency_type, concurrency=4)
    except ConcurrencyTypeNotSupported as err:
        error = err
    finally:
        # Then a helpful error should be raised
        assert (
            str(error) == 'Concurrency type "some-incorrect-concurrency-type" is not yet supported.'
        )
