import logging
import random
import string

from django.core.management import BaseCommand

from ...models import User, Order
from ...utils import chunker

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--n-users", type=int, default=1000)
        parser.add_argument("--n-orders-per-user", type=int, default=1000)
        parser.add_argument("--from-scratch", action="store_true")

    def handle(self, *args, **options):
        if options["from_scratch"]:
            _delete_all()
        _populate_users(n=options["n_users"])
        _populate_orders(n_per_user=options["n_orders_per_user"])


def _delete_all():
    r = Order.objects.all().delete()
    logger.debug("Deleted %s: %s", Order.__name__, r)
    r = User.objects.all().delete()
    logger.debug("Deleted %s: %s", User.__name__, r)


def _populate_users(n: int) -> None:
    users: list[User] = []
    username_length: int = User._meta.get_field("username").max_length
    random_username_generator = RandomStringGenerator(length=username_length)
    for _ in range(n):
        username_random: str = random_username_generator.generate()
        user = User(username=username_random)
        users.append(user)

    for user_chunk in chunker(users, size=10_000):
        User.objects.bulk_create(user_chunk)
        print(f"Bulk-created {len(user_chunk)} random User(s)")


def _populate_orders(n_per_user: int) -> None:
    user_ids: list[int] = list(User.objects.all().values_list("id", flat=True))
    order_name_length: int = Order._meta.get_field("name").max_length
    random_order_name_id_generator = RandomStringGenerator(length=order_name_length)

    for user_ids_chunk in chunker(user_ids, size=1000):
        orders: list[Order] = []

        for user_id in user_ids_chunk:
            for _ in range(n_per_user):
                order = Order(
                    user_id=user_id,
                    name=random_order_name_id_generator.generate(),
                    price=random.uniform(0.0, 5_000.00),
                )
                orders.append(order)

        Order.objects.bulk_create(orders)
        print(f"Created {len(orders)} random Order(s) for {len(user_ids_chunk)} users")


class MaxRandomStringTryReached(Exception):
    pass


class RandomStringGenerator:
    max_tries = 10

    def __init__(self, length: int):
        self.length = length
        self.existing: set[str] = set()

    def generate(self) -> str:
        tries = 0
        while True:
            s = ''.join(
                random.choice(string.ascii_uppercase + string.digits) for _ in range(self.length)
            )
            if s not in self.existing:
                self.existing.add(s)
                return s
            tries += 1
            if tries > self.max_tries:
                raise MaxRandomStringTryReached
