from datetime import date

from financeos_core.imports.dedupe import select_new_transactions, transaction_key
from financeos_core.imports.models import ParsedTransaction
from financeos_core.money import Money


def tx(
    amount: int = -10000,
    description: str = "Test Cafe",
    external_id: str | None = None,
    day: int = 4,
) -> ParsedTransaction:
    return ParsedTransaction(date(2025, 3, day), Money(amount, "INR"), description, external_id)


def keys_of(*stored: ParsedTransaction) -> dict:  # type: ignore[type-arg]
    counts: dict = {}  # type: ignore[type-arg]
    for t in stored:
        counts[transaction_key(t)] = counts.get(transaction_key(t), 0) + 1
    return counts


def test_first_import_adds_everything() -> None:
    incoming = [tx(), tx(description="Test Shop")]
    result = select_new_transactions(incoming, existing_keys={}, existing_external_ids=set())
    assert result.new == tuple(incoming)
    assert result.already_present == ()


def test_reimporting_the_same_file_adds_nothing() -> None:
    incoming = [tx(), tx(), tx(description="Test Shop")]
    result = select_new_transactions(
        incoming, existing_keys=keys_of(*incoming), existing_external_ids=set()
    )
    assert result.new == ()
    assert len(result.already_present) == 3


def test_two_real_purchases_in_one_file_stay_distinct() -> None:
    incoming = [tx(), tx()]
    result = select_new_transactions(incoming, existing_keys={}, existing_external_ids=set())
    assert len(result.new) == 2


def test_overlapping_statement_adds_only_the_extra_occurrence() -> None:
    result = select_new_transactions(
        [tx(), tx(), tx()], existing_keys=keys_of(tx(), tx()), existing_external_ids=set()
    )
    assert len(result.new) == 1
    assert len(result.already_present) == 2


def test_key_ignores_case_and_spacing_in_description() -> None:
    assert transaction_key(tx(description="Test  CAFE")) == transaction_key(tx())


def test_different_amount_or_date_is_a_different_transaction() -> None:
    stored = keys_of(tx())
    result = select_new_transactions(
        [tx(amount=-10001), tx(day=5)], existing_keys=stored, existing_external_ids=set()
    )
    assert len(result.new) == 2


def test_external_id_matches_on_id_alone() -> None:
    incoming = [tx(external_id="A1", description="Renamed Cafe")]
    result = select_new_transactions(
        incoming, existing_keys={}, existing_external_ids={"A1"}
    )
    assert result.new == ()


def test_repeated_external_id_within_one_file_is_added_once() -> None:
    result = select_new_transactions(
        [tx(external_id="A1"), tx(external_id="A1")],
        existing_keys={},
        existing_external_ids=set(),
    )
    assert len(result.new) == 1
    assert len(result.already_present) == 1


def test_distinct_external_ids_keep_look_alike_rows() -> None:
    result = select_new_transactions(
        [tx(external_id="A1"), tx(external_id="A2")],
        existing_keys={},
        existing_external_ids=set(),
    )
    assert len(result.new) == 2


def test_is_new_mask_lines_up_with_input_order() -> None:
    incoming = [tx(), tx(description="Test Shop"), tx()]
    result = select_new_transactions(
        incoming, existing_keys=keys_of(tx()), existing_external_ids=set()
    )
    assert result.is_new == (False, True, True)
