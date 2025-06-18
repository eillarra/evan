import re
import traceback  # Moved from inside the loop

import polars as pl
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from evan.models import Event, Paper, Session, Subsession


class Command(BaseCommand):
    help = "Import papers from an Excel file for a specific event"

    def add_arguments(self, parser):
        parser.add_argument(
            "event_code",
            type=str,
            help="Event code to import papers for",
        )
        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to the Excel file to import",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without actually importing",
        )

    def handle(self, *args, **options):
        event_code = options["event_code"]
        excel_file = options["excel_file"]
        dry_run = options["dry_run"]

        try:
            event = Event.objects.get(code=event_code)
            self.stdout.write(f"Found event: {event.name} ({event.code})")
        except Event.DoesNotExist as exc:
            raise CommandError(f"Event with code '{event_code}' does not exist") from exc

        try:
            df = pl.read_excel(excel_file, sheet_name="Submissions")
            self.stdout.write(f"Read {len(df)} rows from {excel_file} (sheet: Submissions)")
        except Exception as e:
            raise CommandError(f"Error reading Excel file: {e}") from e

        self.stdout.write("\nExcel file structure:")
        self.stdout.write(f"Columns: {df.columns}")
        self.stdout.write("First few rows:")
        self.stdout.write(str(df.head(3)))

        if not dry_run:
            confirm = input("Do you want to proceed with the import? (y/N): ")
            if confirm.lower() != "y":
                self.stdout.write("Import cancelled.")
                return

        required_columns = ["#", "Title"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise CommandError(f"Missing required columns: {missing_columns}")

        imported_count = 0
        session_mappings = {}
        errors = []

        with transaction.atomic():
            for i, row in enumerate(df.iter_rows(named=True)):
                try:
                    internal_id = row.get("#", "")
                    title = row.get("Title", "")
                    if not title or not str(title).strip():
                        errors.append(f"Row {i + 1}: Missing title")
                        continue

                    title = self._clean_text(title)
                    authors = row.get("Authors", "") or ""
                    abstract = row.get("Abstract", "") or ""
                    abstract = self._clean_text(abstract)

                    extra_data = {
                        "internal_id": internal_id,
                        "authors_str": str(authors) if authors else "",
                        "authors": self._parse_authors(str(authors) if authors else ""),
                    }

                    paper = None
                    if dry_run:
                        existing_paper = Paper.objects.filter(event=event, extra_data__internal_id=internal_id).first()
                        if existing_paper:
                            self.stdout.write(
                                f"Row {i + 1}: Paper with ID {internal_id} already exists (would skip creation)"
                            )
                            paper = existing_paper
                        else:
                            self.stdout.write(f"Row {i + 1}: Would create paper '{title}' (ID: {internal_id})")
                    else:
                        existing_paper = Paper.objects.filter(event=event, extra_data__internal_id=internal_id).first()

                        if existing_paper:
                            self.stdout.write(
                                f"Row {i + 1}: Paper with ID {internal_id} already exists, updating metadata"
                            )
                            paper = existing_paper
                        else:
                            paper = Paper.objects.create(
                                event=event,
                                title=title,
                                abstract=str(abstract) if abstract else "",
                                extra_data=extra_data,
                            )
                            self.stdout.write(f"Created paper: {title} (ID: {internal_id})")

                    # Topics are ignored in this import - they can be managed separately

                    track_str = row.get("Track", "")
                    if track_str and str(track_str).strip():
                        track_text = str(track_str).strip()
                        session_code = track_text.replace(" 2025", "").strip()

                        if dry_run:
                            session = Session.objects.filter(event=event, code=session_code).first()
                            if not session:
                                self.stdout.write(
                                    f"  - Warning: Session '{session_code}' not found for paper {internal_id}"
                                )
                            else:
                                self.stdout.write(f"  - Would link to session: {session_code}")
                                session_mappings[str(internal_id)] = session_code
                        else:
                            session = Session.objects.filter(event=event, code=session_code).first()
                            if session and paper:
                                paper.session = session  # type: ignore
                                paper.save()
                                session_mappings[str(internal_id)] = session_code
                                self.stdout.write(f"  - Linked to session: {session_code}")
                            elif not session:
                                self.stdout.write(
                                    f"  - Warning: Session '{session_code}' not found for paper {internal_id}"
                                )

                    imported_count += 1

                except Exception as e:
                    errors.append(f"Row {i + 1}: Error processing row - {e}")
                    self.stdout.write(f"Row {i + 1}: Error - {e}")

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(f"\n{'DRY RUN - ' if dry_run else ''}Import completed:")
        self.stdout.write(f"- Papers {'would be' if dry_run else 'were'} imported: {imported_count}")

        if session_mappings:
            self.stdout.write(
                f"- Session mappings {'would be' if dry_run else 'were'} created: {len(session_mappings)}"
            )
            for paper_id, session_code in session_mappings.items():
                self.stdout.write(f"  * Paper {paper_id} -> Session {session_code}")

        if errors:
            self.stdout.write(f"\nErrors encountered: {len(errors)}")
            for error in errors:
                self.stdout.write(f"  - {error}")

        if dry_run:
            self.stdout.write("\nThis was a dry run. No data was actually imported.")
            self.stdout.write("Run without --dry-run to perform the actual import.")
        else:
            self.stdout.write("Import completed successfully!")

        try:
            sessions_df = pl.read_excel(excel_file, sheet_name="Main Paper Track Sessions")
            self.stdout.write(f"\nRead {len(sessions_df)} rows from {excel_file} (sheet: Main Paper Track Sessions)")
        except Exception as e:
            raise CommandError(f"Error reading sessions sheet: {e}") from e

        self.stdout.write("\nSessions sheet structure:")
        self.stdout.write(f"Columns: {sessions_df.columns}")
        self.stdout.write("First few rows:")
        self.stdout.write(str(sessions_df.head(3)))

        self.stdout.write("\nProcessing session-paper mappings from 'Main Paper Track Sessions' sheet...")
        session_paper_mappings = 0
        session_errors = []

        with transaction.atomic():
            for i, row in enumerate(sessions_df.iter_rows(named=True)):
                try:
                    title = row.get("Title", "")
                    if not title or not str(title).strip():
                        continue

                    title = str(title).strip()
                    # Extract session code from title format: "{session_code} - more text"
                    session_code = title.split(" - ")[0].strip() if " - " in title else title.strip()

                    session = Session.objects.filter(event=event, code=session_code).first()

                    if not session:
                        session_errors.append(f"Session row {i + 1}: Session '{session_code}' not found")
                        continue

                    paper_ids = []
                    for col in ["p1", "p2", "p3", "p4"]:
                        paper_id = row.get(col, "")
                        if paper_id and str(paper_id).strip():
                            paper_ids.append(str(paper_id).strip())

                    # Track valid paper IDs for program generation
                    valid_paper_ids = []

                    for paper_internal_id in paper_ids:
                        paper = Paper.objects.filter(event=event, extra_data__internal_id=paper_internal_id).first()

                        if paper:
                            valid_paper_ids.append(paper_internal_id)
                            if dry_run:
                                if paper.session:
                                    self.stdout.write(
                                        f"Row {i + 1}: Paper ID {paper_internal_id} already linked to session "
                                        f"'{paper.session.code}' (would skip)"
                                    )
                                else:
                                    self.stdout.write(
                                        f"Row {i + 1}: Would map Paper ID {paper_internal_id} to Session {session_code}"
                                    )
                            else:
                                if paper.session:
                                    self.stdout.write(
                                        f"Row {i + 1}: Paper ID {paper_internal_id} already linked to session "
                                        f"'{paper.session.code}' (skipping)"
                                    )
                                else:
                                    paper.session = session  # type: ignore
                                    paper.save()
                                    session_paper_mappings += 1
                                    self.stdout.write(
                                        f"Row {i + 1}: Mapped Paper ID {paper_internal_id} to Session {session_code}"
                                    )
                        else:
                            session_errors.append(f"Session row {i + 1}: Paper with ID '{paper_internal_id}' not found")

                    # Generate and update session program content
                    if valid_paper_ids:
                        program_content = "\n".join([f"- [paperi:{pid}]" for pid in valid_paper_ids])
                        self.stdout.write(
                            f"Row {i + 1}: Generated program for session {session_code} "
                            f"with {len(valid_paper_ids)} papers"
                        )

                        if not dry_run:
                            if session.program != program_content:
                                session.program = program_content
                                session.save(update_fields=["program"])
                                self.stdout.write(f"Row {i + 1}: Updated program for session {session_code}")
                            else:
                                self.stdout.write(f"Row {i + 1}: Program for session {session_code} already up to date")
                        else:
                            self.stdout.write(f"Row {i + 1}: Would update program for session {session_code}")

                except Exception as e:
                    session_errors.append(f"Session row {i + 1}: Error processing row - {e}")

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(f"\n{'DRY RUN - ' if dry_run else ''}Final import summary:")
        self.stdout.write(f"- Papers {'would be' if dry_run else 'were'} imported: {imported_count}")

        if session_mappings:
            self.stdout.write(
                f"- Initial session mappings {'would be' if dry_run else 'were'} created: {len(session_mappings)}"
            )

        if session_paper_mappings > 0:
            self.stdout.write(
                f"- Additional session-paper mappings {'would be' if dry_run else 'were'} "
                f"created: {session_paper_mappings}"
            )

        if errors:
            self.stdout.write(f"\nErrors encountered: {len(errors)}")
            for error in errors:
                self.stdout.write(f"  - {error}")

        if session_errors:
            self.stdout.write(f"\nSession mapping errors: {len(session_errors)}")
            for error in session_errors:
                self.stdout.write(f"  - {error}")

        if dry_run:
            self.stdout.write("\nThis was a dry run. No data was actually imported.")
            self.stdout.write("Run without --dry-run to perform the actual import.")
        else:
            self.stdout.write("Import completed successfully!")

        # Process subsession sheets
        self._process_subsession_sheets(event, excel_file, dry_run)

        # Update session timing based on subsessions (only if not dry run)
        if not dry_run:
            self.stdout.write("\nUpdating session timing based on subsessions...")
            sessions_with_subsessions = Session.objects.filter(event=event, subsessions__isnull=False).distinct()

            for session in sessions_with_subsessions:
                self._update_session_timing(session)

    def _parse_authors(self, authors_str: str) -> list[dict]:
        if not authors_str.strip():
            return []

        authors_str = authors_str.strip()
        if " and " in authors_str:
            parts = authors_str.split(" and ")
            if len(parts) == 2:
                first_authors = [name.strip() for name in parts[0].split(",") if name.strip()]
                last_author = [parts[1].strip()]
                author_names = first_authors + last_author
            else:
                author_names = [name.strip() for name in authors_str.split(",") if name.strip()]
        else:
            author_names = [name.strip() for name in authors_str.split(",") if name.strip()]

        return [{"name": name, "affiliation": None} for name in author_names if name]

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""

        text = str(text).strip()
        text = re.sub(r"[\n\r]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _process_subsession_sheets(self, event, excel_file, dry_run):
        """Process EU Workshop Sessions and Workshop Sessions sheets for subsessions."""
        sheet_names = ["EU Workshop Sessions (WIP)", "Workshop Sessions (WIP)"]

        for sheet_name in sheet_names:
            try:
                subsessions_df = pl.read_excel(excel_file, sheet_name=sheet_name)
                self.stdout.write(f"\nRead {len(subsessions_df)} rows from {excel_file} (sheet: {sheet_name})")
            except Exception as e:
                self.stdout.write(f"Warning: Could not read sheet '{sheet_name}': {e}")
                continue

            self.stdout.write(f"\n{sheet_name} structure:")
            self.stdout.write(f"Columns: {subsessions_df.columns}")
            self.stdout.write("First few rows:")
            self.stdout.write(str(subsessions_df.head(3)))

            self._process_subsessions_from_sheet(event, subsessions_df, sheet_name, dry_run)

    def _process_subsessions_from_sheet(self, event, df, sheet_name, dry_run):
        """Process individual subsession sheet."""
        subsession_count = 0
        subsession_paper_mappings = 0
        errors = []

        with transaction.atomic():
            for i, row in enumerate(df.iter_rows(named=True)):
                paper_internal_ids_for_program = []  # Initialize for current subsession's program
                title = ""  # Initialize title to ensure it's defined for error logging
                try:
                    title = row.get("Title", "")
                    if not title or not str(title).strip():
                        continue

                    title = str(title).strip()

                    parts = title.split()
                    session_code: str
                    roman_numeral: str | None
                    order: int
                    subsession_title: str

                    if len(parts) == 1:
                        session_code = parts[0]
                        roman_numeral = None
                        order = 1
                        subsession_title = ""
                    elif len(parts) >= 2:
                        session_code = parts[0]
                        potential_roman = parts[1]
                        parsed_order = self._roman_to_int(potential_roman)
                        if parsed_order is not None:
                            order = parsed_order
                            roman_numeral = potential_roman
                            if " - " in title:
                                title_parts = title.split(" - ", 1)
                                subsession_title = title_parts[1].strip() if len(title_parts) > 1 else ""
                            else:
                                subsession_title = ""
                        else:
                            roman_numeral = None
                            order = 1
                            subsession_title = " ".join(parts[1:])
                    else:
                        errors.append(f"{sheet_name} row {i + 1}: Invalid title format '{title}'")
                        continue

                    session = Session.objects.filter(event=event, code=session_code).first()
                    if not session:
                        errors.append(f"{sheet_name} row {i + 1}: Session '{session_code}' not found")
                        continue

                    date_str = row.get("Date", "")
                    start_time_str = row.get("Start Time", "")
                    end_time_str = row.get("End Time", "")

                    subsession_date = self._parse_date(date_str, event) if date_str else None
                    if not subsession_date and date_str:
                        errors.append(
                            f"{sheet_name} row {i + 1}: Could not parse date '{date_str}' for subsession '{title}'"
                        )

                    actual_subsession_instance = None

                    if dry_run:
                        existing_subsession = Subsession.objects.filter(session=session, order=order).first()
                        actual_subsession_instance = existing_subsession
                        roman_display = f" {roman_numeral}" if roman_numeral else ""
                        display_title_part = subsession_title or f"Order {order}"

                        if existing_subsession:
                            self.stdout.write(
                                f"{sheet_name} row {i + 1}: Subsession already exists for "
                                f"{session_code}{roman_display} (ID: {existing_subsession.pk}). Will check for updates."
                            )
                        else:
                            self.stdout.write(
                                f"{sheet_name} row {i + 1}: Would create subsession '{display_title_part}' "
                                f"for session {session_code}{roman_display}"
                            )
                            subsession_count += 1
                    else:
                        start_at = (
                            self._parse_datetime(date_str, start_time_str, event)
                            if date_str and start_time_str
                            else None
                        )
                        end_at = (
                            self._parse_datetime(date_str, end_time_str, event) if date_str and end_time_str else None
                        )

                        subsession_obj, created = Subsession.objects.get_or_create(
                            session=session,
                            order=order,
                            defaults={
                                "title": subsession_title,
                                "start_at": start_at,
                                "end_at": end_at,
                            },
                        )
                        actual_subsession_instance = subsession_obj
                        display_title_part = subsession_obj.title or f"Order {subsession_obj.order}"

                        if created:
                            subsession_count += 1
                            self.stdout.write(
                                f"Created subsession: {session_code} - {display_title_part} (ID: {subsession_obj.pk})"
                            )
                        else:
                            updated_fields = []
                            if subsession_title and subsession_obj.title != subsession_title:
                                subsession_obj.title = subsession_title
                                updated_fields.append("title")
                            if start_at and subsession_obj.start_at != start_at:
                                subsession_obj.start_at = start_at
                                updated_fields.append("start_at")
                            if end_at and subsession_obj.end_at != end_at:
                                subsession_obj.end_at = end_at
                                updated_fields.append("end_at")

                            if updated_fields:
                                subsession_obj.save()
                                self.stdout.write(
                                    f"Updated subsession: {session_code} - {display_title_part} "
                                    f"(ID: {subsession_obj.pk}). Fields: {', '.join(updated_fields)}"
                                )
                            else:
                                self.stdout.write(
                                    f"Found existing subsession: {session_code} - {display_title_part} "
                                    f"(ID: {subsession_obj.pk}). No changes to core fields."
                                )

                    # Process papers from columns - different sheets use different column names
                    if "Papers" in df.columns:
                        # Workshop sheets use Papers, __UNNAMED__5, etc.
                        paper_columns = ["Papers", "__UNNAMED__5", "__UNNAMED__6", "__UNNAMED__7", "__UNNAMED__8"]
                    else:
                        # Main track sheets use p1, p2, p3, p4, p5
                        paper_columns = ["p1", "p2", "p3", "p4", "p5"]

                    for col_name in paper_columns:
                        paper_id_val = row.get(col_name, "")
                        if paper_id_val and str(paper_id_val).strip():
                            paper_internal_id = str(paper_id_val).strip()
                            paper = Paper.objects.filter(event=event, extra_data__internal_id=paper_internal_id).first()

                            if paper:
                                paper_internal_ids_for_program.append(paper_internal_id)
                                self.stdout.write(
                                    f"  - Found paper {paper_internal_id} (PK: {paper.pk}) for subsession"
                                )
                                self.stdout.write(
                                    f"    DEBUG: paper_internal_ids_for_program now contains: "
                                    f"{paper_internal_ids_for_program}"
                                )

                                if dry_run:
                                    current_paper_subsession_pk = paper.subsession.pk if paper.subsession else None
                                    target_subsession_pk_str = (
                                        str(actual_subsession_instance.pk)
                                        if actual_subsession_instance
                                        else f"new (order {order})"
                                    )

                                    if (
                                        current_paper_subsession_pk
                                        and actual_subsession_instance
                                        and current_paper_subsession_pk == actual_subsession_instance.pk
                                    ):
                                        self.stdout.write(
                                            f"  - Paper {paper_internal_id} would remain linked to this subsession "
                                            f"{target_subsession_pk_str}."
                                        )
                                    elif current_paper_subsession_pk:
                                        self.stdout.write(
                                            f"  - Paper {paper_internal_id} (currently in subsession "
                                            f"{current_paper_subsession_pk}) would be moved/linked to subsession "
                                            f"{target_subsession_pk_str}."
                                        )
                                        if not paper.subsession:
                                            subsession_paper_mappings += 1
                                    else:
                                        self.stdout.write(
                                            f"  - Paper {paper_internal_id} would be linked to subsession "
                                            f"{target_subsession_pk_str}."
                                        )
                                        subsession_paper_mappings += 1
                                else:
                                    if actual_subsession_instance:
                                        sub_display = (
                                            actual_subsession_instance.title
                                            or f"Order {actual_subsession_instance.order}"
                                        )
                                        if paper.subsession != actual_subsession_instance:
                                            log_msg_prefix = "Linking"
                                            if paper.subsession is not None:
                                                log_msg_prefix = (
                                                    f"Moving Paper {paper_internal_id} from subsession "
                                                    f"{paper.subsession.pk} to"
                                                )
                                            else:  # Paper had no subsession before
                                                subsession_paper_mappings += 1

                                            paper.subsession = actual_subsession_instance  # type: ignore
                                            paper.save()
                                            self.stdout.write(
                                                f"  - {log_msg_prefix} Paper {paper_internal_id} to subsession "
                                                f"{actual_subsession_instance.pk} ('{sub_display}')."
                                            )
                                            self.stdout.write(
                                                f"    DEBUG: Paper {paper_internal_id} successfully linked to "
                                                f"subsession"
                                            )
                                        else:
                                            self.stdout.write(
                                                f"  - Paper {paper_internal_id} already correctly linked to subsession "
                                                f"{actual_subsession_instance.pk} ('{sub_display}')."
                                            )
                            else:  # Paper not found
                                errors.append(
                                    f"{sheet_name} row {i + 1}: Paper with ID '{paper_internal_id}' "
                                    f"(from column {col_name}) not found."
                                )

                    # Generate and set program for the subsession
                    self.stdout.write(
                        f"  - DEBUG: About to generate program. "
                        f"paper_internal_ids_for_program = {paper_internal_ids_for_program}"
                    )
                    if paper_internal_ids_for_program:
                        program_content = "\n".join([f"- [paperi:{pid}]" for pid in paper_internal_ids_for_program])
                        self.stdout.write(
                            f"  - Generated program with {len(paper_internal_ids_for_program)} papers: "
                            f"{paper_internal_ids_for_program}"
                        )
                        self.stdout.write(f"  - DEBUG: Generated program_content = '{program_content}'")
                    else:
                        program_content = ""
                        self.stdout.write("  - No papers found for program generation")
                        self.stdout.write(
                            f"  - DEBUG: paper_internal_ids_for_program was empty: {paper_internal_ids_for_program}"
                        )

                    # Save program to subsession (only in non-dry-run mode)
                    if not dry_run and actual_subsession_instance:
                        if actual_subsession_instance.program != program_content:
                            actual_subsession_instance.program = program_content
                            actual_subsession_instance.save(update_fields=["program"])
                            sub_title = actual_subsession_instance.title or f"Order {actual_subsession_instance.order}"
                            self.stdout.write(
                                f"  - Updated program for subsession {actual_subsession_instance.pk} ('{sub_title}')"
                            )
                    elif dry_run and program_content:
                        self.stdout.write(
                            f"  - DRY RUN: Would set program for subsession (session {session_code}, order {order})"
                        )

                except Exception as e:
                    errors.append(f"{sheet_name} row {i + 1} ('{title}'): Error processing subsession - {e}")
                    self.stdout.write(f"Error processing subsession row {i + 1} ('{title}') in {sheet_name}: {e}")
                    self.stdout.write(traceback.format_exc())

            if dry_run:
                transaction.set_rollback(True)

        # Summary for this sheet
        self.stdout.write(f"\n{sheet_name} {'DRY RUN - ' if dry_run else ''}Summary:")
        self.stdout.write(f"- Subsessions {'would be' if dry_run else 'were'} created: {subsession_count}")
        self.stdout.write(
            f"- Paper-subsession mappings {'would be' if dry_run else 'were'} created: {subsession_paper_mappings}"
        )

        if errors:
            self.stdout.write(f"- Errors in {sheet_name}: {len(errors)}")
            for error in errors:
                self.stdout.write(f"  - {error}")

    def _roman_to_int(self, roman):
        """Convert roman numeral to integer for ordering."""
        roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
        return roman_map.get(roman.upper())

    def _parse_time(self, time_str, session=None):
        """Parse time string to datetime object using session's date."""
        if not time_str or not str(time_str).strip():
            return None

        try:
            from datetime import date, datetime

            from django.utils import timezone

            time_str = str(time_str).strip()
            self.stdout.write(f"    DEBUG: Parsing time string: '{time_str}'")

            parsed_datetime = None

            # Try to parse as full datetime first (Excel format)
            datetime_formats = [
                "%Y-%m-%d %H:%M:%S",  # 1899-12-31 14:45:00
                "%Y-%m-%d %H:%M",  # 1899-12-31 14:45
                "%m/%d/%Y %H:%M:%S",  # 12/31/1899 14:45:00
                "%m/%d/%Y %H:%M",  # 12/31/1899 14:45
            ]

            for fmt in datetime_formats:
                try:
                    parsed_datetime = datetime.strptime(time_str, fmt)
                    self.stdout.write(f"    DEBUG: Parsed as datetime with format '{fmt}': {parsed_datetime}")
                    break
                except ValueError:
                    continue

            # If we got a datetime, extract just the time part
            if parsed_datetime:
                parsed_time = parsed_datetime.time()
                self.stdout.write(f"    DEBUG: Extracted time: {parsed_time}")
            else:
                # Try as time-only formats
                time_formats = [
                    "%H:%M:%S",  # 14:45:00
                    "%H:%M",  # 14:45
                    "%I:%M:%S %p",  # 2:45:00 PM
                    "%I:%M %p",  # 2:45 PM
                ]

                parsed_time = None
                for fmt in time_formats:
                    try:
                        parsed_time = datetime.strptime(time_str, fmt).time()
                        self.stdout.write(f"    DEBUG: Parsed as time with format '{fmt}': {parsed_time}")
                        break
                    except ValueError:
                        continue

                if parsed_time is None:
                    self.stdout.write(f"    DEBUG: Failed to parse time string: '{time_str}'")
                    return None

            # Use session's date
            if session and session.date:
                session_date = session.date
                self.stdout.write(f"    DEBUG: Using session date: {session_date}")
            else:
                session_date = date.today()
                self.stdout.write(f"    DEBUG: Using today as fallback: {session_date}")

            # Combine session date with parsed time
            dt = datetime.combine(session_date, parsed_time)
            aware_dt = timezone.make_aware(dt)
            self.stdout.write(f"    DEBUG: Final datetime: {aware_dt}")
            return aware_dt

        except Exception as e:
            self.stdout.write(f"    DEBUG: Exception in _parse_time: {e}")
            return None

    def _parse_date(self, date_str, event):
        """Parse date string from Excel format like '11-Aug'."""
        if not date_str or not str(date_str).strip():
            return None

        try:
            from datetime import datetime

            date_str = str(date_str).strip()
            self.stdout.write(f"    DEBUG: Parsing date string: '{date_str}'")

            # Get the event year as context
            event_year = event.start_date.year if event.start_date else datetime.now().year

            # Try different date formats
            date_formats = [
                "%d-%b",  # 11-Aug
                "%d-%B",  # 11-August
                "%b-%d",  # Aug-11
                "%B-%d",  # August-11
                "%d/%m",  # 11/08
                "%m/%d",  # 08/11
                "%Y-%m-%d",  # 2023-08-11
            ]

            for fmt in date_formats:
                try:
                    # Parse without year, then add the event year
                    parsed_date = datetime.strptime(date_str, fmt).replace(year=event_year).date()
                    self.stdout.write(f"    DEBUG: Parsed date with format '{fmt}': {parsed_date}")
                    return parsed_date
                except ValueError:
                    continue

            self.stdout.write(f"    DEBUG: Failed to parse date string: '{date_str}'")
            return None

        except Exception as e:
            self.stdout.write(f"    DEBUG: Exception in _parse_date: {e}")
            return None

    def _parse_datetime(self, date_str, time_str, event=None):
        """Parse date and time strings into a timezone-aware datetime."""
        if not date_str or not time_str:
            return None

        try:
            from datetime import datetime

            from django.utils import timezone

            # Parse the date component
            parsed_date = self._parse_date(date_str, event)
            if not parsed_date:
                return None

            # Parse the time component from Excel datetime format
            time_str = str(time_str).strip()
            self.stdout.write(f"    DEBUG: Parsing datetime - Date: {parsed_date}, Time string: '{time_str}'")

            parsed_datetime = None

            # Try to parse as full datetime first (Excel format)
            datetime_formats = [
                "%Y-%m-%d %H:%M:%S",  # 1899-12-31 14:45:00
                "%Y-%m-%d %H:%M",  # 1899-12-31 14:45
                "%m/%d/%Y %H:%M:%S",  # 12/31/1899 14:45:00
                "%m/%d/%Y %H:%M",  # 12/31/1899 14:45
            ]

            for fmt in datetime_formats:
                try:
                    parsed_datetime = datetime.strptime(time_str, fmt)
                    self.stdout.write(f"    DEBUG: Parsed time as datetime with format '{fmt}': {parsed_datetime}")
                    break
                except ValueError:
                    continue

            # If we got a datetime, extract just the time part
            if parsed_datetime:
                parsed_time = parsed_datetime.time()
                self.stdout.write(f"    DEBUG: Extracted time: {parsed_time}")
            else:
                # Try as time-only formats
                time_formats = [
                    "%H:%M:%S",  # 14:45:00
                    "%H:%M",  # 14:45
                    "%I:%M:%S %p",  # 2:45:00 PM
                    "%I:%M %p",  # 2:45 PM
                ]

                parsed_time = None
                for fmt in time_formats:
                    try:
                        parsed_time = datetime.strptime(time_str, fmt).time()
                        self.stdout.write(f"    DEBUG: Parsed as time with format '{fmt}': {parsed_time}")
                        break
                    except ValueError:
                        continue

                if parsed_time is None:
                    self.stdout.write(f"    DEBUG: Failed to parse time string: '{time_str}'")
                    return None

            # Combine date with parsed time
            dt = datetime.combine(parsed_date, parsed_time)
            aware_dt = timezone.make_aware(dt)
            self.stdout.write(f"    DEBUG: Final datetime: {aware_dt}")
            return aware_dt

        except Exception as e:
            self.stdout.write(f"    DEBUG: Exception in _parse_datetime: {e}")
            return None

    def _update_session_timing(self, session):
        """Update session start_at and end_at based on its subsessions."""
        try:
            subsessions = session.subsessions.filter(start_at__isnull=False, end_at__isnull=False).order_by("start_at")

            if not subsessions.exists():
                self.stdout.write(f"    DEBUG: No subsessions with timing for session {session.code}")
                return

            first_subsession = subsessions.first()
            last_subsession = subsessions.last()

            new_start = first_subsession.start_at
            new_end = last_subsession.end_at

            updated = False
            if session.start_at != new_start:
                session.start_at = new_start
                updated = True

            if session.end_at != new_end:
                session.end_at = new_end
                updated = True

            if updated:
                session.save()
                self.stdout.write(f"Updated session {session.code} timing: {new_start} - {new_end}")
            else:
                self.stdout.write(f"Session {session.code} timing already correct")

        except Exception as e:
            self.stdout.write(f"    DEBUG: Exception updating session timing: {e}")
