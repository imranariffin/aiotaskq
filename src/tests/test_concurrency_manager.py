from aiotaskq.exceptions import ConcurrencyTypeNotSupported
from aiotaskq.concurrency_manager import ConcurrencyManagerSingleton
from aiotaskq.interfaces import ConcurrencyType


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


def test_singleton():
    # When getting the concurrency_manager instance more than once
    instance_1 = ConcurrencyManagerSingleton.get(
        concurrency_type=ConcurrencyType.MULTIPROCESSING,
        concurrency=4,
    )
    instance_2 = ConcurrencyManagerSingleton.get(
        concurrency_type=ConcurrencyType.MULTIPROCESSING,
        concurrency=4,
    )

    # Then the both instances should be the identical instance
    assert instance_1 is instance_2
