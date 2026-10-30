"""
Unit tests for Shared Kernel Domain Base Classes & Abstractions.
"""

import asyncio
import unittest
from dataclasses import dataclass

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.domain_event import DomainEvent
from shared.kernel.entity import Entity
from shared.kernel.result import Error, Result
from shared.kernel.specification import Specification
from shared.kernel.value_objects import (
    Email,
    EntityId,
    Language,
    MoneyAmount,
    Score,
    Timestamp,
    Version,
)


class SampleEntityId(EntityId):
    pass


class SampleEntity(Entity[SampleEntityId]):
    pass


@dataclass(frozen=True)
class SampleDomainEvent(DomainEvent):
    payload: str = "test"


class SampleAggregateRoot(AggregateRoot[SampleEntityId]):
    def do_something(self) -> None:
        self._raise_event(SampleDomainEvent(payload="done"))


class ActiveSpec(Specification[SampleAggregateRoot]):
    def is_satisfied_by(self, candidate: SampleAggregateRoot) -> bool:
        return True


@dataclass(frozen=True)
class DoWorkCommand(Command):
    message: str


class DoWorkHandler(CommandHandler[DoWorkCommand, str]):
    async def handle(self, command: DoWorkCommand) -> Result[str]:
        if not command.message:
            return Result.fail(Error("INVALID_INPUT", "Message empty"))
        return Result.ok(f"Processed: {command.message}")


class TestSharedKernel(unittest.TestCase):
    def test_entity_equality_and_identity(self) -> None:
        e_id = SampleEntityId()
        e1 = SampleEntity(id=e_id)
        e2 = SampleEntity(id=e_id)

        self.assertEqual(e1, e2)
        self.assertEqual(hash(e1), hash(e2))
        self.assertEqual(e1.id, e_id)

    def test_aggregate_root_events(self) -> None:
        agg = SampleAggregateRoot(id=SampleEntityId())
        self.assertEqual(len(agg.domain_events), 0)

        agg.do_something()
        events = agg.domain_events
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload, "done")

        cleared = agg.clear_events()
        self.assertEqual(len(cleared), 1)
        self.assertEqual(len(agg.domain_events), 0)

    def test_value_objects(self) -> None:
        email = Email("user@example.com")
        self.assertEqual(email.value, "user@example.com")
        with self.assertRaises((AttributeError, TypeError)):
            email.value = "other@example.com"  # type: ignore[misc]

        money1 = MoneyAmount(1000, "USD")
        money2 = MoneyAmount(500, "USD")
        self.assertEqual((money1 + money2).amount_cents, 1500)

        score = Score(0.95)
        self.assertEqual(score.value, 0.95)

        lang = Language("en-US")
        self.assertEqual(lang.code, "en-US")

        ver = Version(1)
        self.assertEqual(ver.value, 1)

        ts = Timestamp.now()
        self.assertIsNotNone(ts.value)

    def test_result_monad(self) -> None:
        res_ok = Result.ok("SUCCESS")
        self.assertTrue(res_ok.is_success)
        self.assertFalse(res_ok.is_failure)
        self.assertEqual(res_ok.value, "SUCCESS")

        err = Error("FAIL_CODE", "Failure occurred")
        res_err = Result.fail(err)
        self.assertTrue(res_err.is_failure)
        self.assertEqual(res_err.error.code, "FAIL_CODE")

    def test_cqrs_handler(self) -> None:
        handler = DoWorkHandler()

        async def run() -> None:
            res = await handler.handle(DoWorkCommand(message="Hello CQRS"))
            self.assertTrue(res.is_success)
            self.assertEqual(res.value, "Processed: Hello CQRS")

            err_res = await handler.handle(DoWorkCommand(message=""))
            self.assertTrue(err_res.is_failure)
            self.assertEqual(err_res.error.code, "INVALID_INPUT")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
