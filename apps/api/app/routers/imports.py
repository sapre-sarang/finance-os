import hashlib
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from financeos_core.imports.csv_parser import CsvLayout, inspect_csv
from financeos_core.imports.errors import StatementParseError
from financeos_db.models import Account, ImportBatch, Transaction
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.deps import AppSettings, CurrentUser, DbSession
from app.services.accounts import get_owned_account
from app.services.imports import ImportPlan, lock_account, plan_csv_import

router = APIRouter(prefix="/imports", tags=["imports"])


@dataclass(frozen=True, slots=True)
class LayoutFields:
    date_column: str
    description_column: str
    date_format: str
    amount_column: str | None
    debit_column: str | None
    credit_column: str | None
    reference_column: str | None

    def to_layout(self, currency: str) -> CsvLayout:
        try:
            return CsvLayout(
                currency=currency,
                date_column=self.date_column,
                description_column=self.description_column,
                date_format=self.date_format,
                amount_column=self.amount_column,
                debit_column=self.debit_column,
                credit_column=self.credit_column,
                reference_column=self.reference_column,
            )
        except ValueError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                {"problems": [str(error)]},
            ) from None


def _blank_to_none(value: str | None) -> str | None:
    return value.strip() or None if value else None


def layout_fields(
    date_column: Annotated[str, Form()],
    description_column: Annotated[str, Form()],
    date_format: Annotated[str, Form()],
    amount_column: Annotated[str | None, Form()] = None,
    debit_column: Annotated[str | None, Form()] = None,
    credit_column: Annotated[str | None, Form()] = None,
    reference_column: Annotated[str | None, Form()] = None,
) -> LayoutFields:
    return LayoutFields(
        date_column,
        description_column,
        date_format,
        _blank_to_none(amount_column),
        _blank_to_none(debit_column),
        _blank_to_none(credit_column),
        _blank_to_none(reference_column),
    )


def _read_upload(file: UploadFile, max_bytes: int) -> bytes:
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            {"problems": [f"File is larger than {max_bytes // (1024 * 1024)} MB"]},
        )
    return data


def _problems(error: StatementParseError) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, {"problems": list(error.problems)})


class InspectOut(BaseModel):
    headers: list[str]
    sample_rows: list[list[str]]


class PreviewRow(BaseModel):
    index: int
    occurred_on: date
    amount_minor: int
    currency: str
    description: str
    already_imported: bool


class PreviewOut(BaseModel):
    rows: list[PreviewRow]
    new_count: int
    already_imported_count: int


class CommitOut(BaseModel):
    added: int
    already_imported: int
    skipped_by_you: int


def _parse_skip(skip_rows: str) -> set[int]:
    try:
        return {int(part) for part in skip_rows.split(",") if part.strip()}
    except ValueError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, {"problems": ["skip_rows must be numbers"]}
        ) from None


@router.post("/inspect", response_model=InspectOut)
def inspect(
    user: CurrentUser, settings: AppSettings, file: Annotated[UploadFile, File()]
) -> InspectOut:
    try:
        headers, rows = inspect_csv(
            _read_upload(file, settings.max_upload_bytes), max_bytes=settings.max_upload_bytes
        )
    except StatementParseError as error:
        raise _problems(error) from None
    return InspectOut(headers=headers, sample_rows=rows)


def _plan(
    session: DbSession,
    account: Account,
    file: UploadFile,
    fields: LayoutFields,
    max_bytes: int,
) -> tuple[ImportPlan, bytes]:
    data = _read_upload(file, max_bytes)
    try:
        plan = plan_csv_import(
            session, account, data, fields.to_layout(account.currency), max_bytes
        )
    except StatementParseError as error:
        raise _problems(error) from None
    return plan, data


@router.post("/preview", response_model=PreviewOut)
def preview(
    user: CurrentUser,
    session: DbSession,
    settings: AppSettings,
    fields: Annotated[LayoutFields, Depends(layout_fields)],
    account_id: Annotated[uuid.UUID, Form()],
    file: Annotated[UploadFile, File()],
) -> PreviewOut:
    account = get_owned_account(session, user, account_id)
    plan, _ = _plan(session, account, file, fields, settings.max_upload_bytes)
    rows = [
        PreviewRow(
            index=index,
            occurred_on=t.occurred_on,
            amount_minor=t.amount.minor,
            currency=t.amount.currency,
            description=t.description,
            already_imported=not plan.dedupe.is_new[index],
        )
        for index, t in enumerate(plan.parsed)
    ]
    return PreviewOut(
        rows=rows,
        new_count=len(plan.dedupe.new),
        already_imported_count=len(plan.dedupe.already_present),
    )


@router.post("/commit", response_model=CommitOut)
def commit(
    user: CurrentUser,
    session: DbSession,
    settings: AppSettings,
    fields: Annotated[LayoutFields, Depends(layout_fields)],
    account_id: Annotated[uuid.UUID, Form()],
    file: Annotated[UploadFile, File()],
    skip_rows: Annotated[str, Form()] = "",
) -> CommitOut:
    account = get_owned_account(session, user, account_id)
    lock_account(session, account.id)
    # Re-parse and re-check duplicates here: the server never trusts rows the client previewed.
    plan, data = _plan(session, account, file, fields, settings.max_upload_bytes)
    skipped = _parse_skip(skip_rows)

    batch = ImportBatch(
        account_id=account.id,
        file_sha256=hashlib.sha256(data).hexdigest(),
        rows_in_file=len(plan.parsed),
        rows_added=0,
    )
    session.add(batch)
    session.flush()

    added = 0
    skipped_by_you = 0
    for index, parsed in enumerate(plan.parsed):
        if not plan.dedupe.is_new[index]:
            continue
        if index in skipped:
            skipped_by_you += 1
            continue
        session.add(
            Transaction(
                account_id=account.id,
                occurred_on=parsed.occurred_on,
                amount_minor=parsed.amount.minor,
                currency=parsed.amount.currency,
                description=parsed.description,
                external_id=parsed.external_id,
                import_batch_id=batch.id,
            )
        )
        added += 1
    batch.rows_added = added

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"problems": ["The file repeats a bank reference already used in this account"]},
        ) from None
    return CommitOut(
        added=added,
        already_imported=len(plan.dedupe.already_present),
        skipped_by_you=skipped_by_you,
    )
