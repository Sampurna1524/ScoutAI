import threading
import time
from typing import Optional
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from models.job import Job
from models.scout_session import ScoutSession
from services.browser_service import BrowserService
from services.crawler_service import CrawlerService
from services.extractor_service import ExtractorService
from services.link_extractor_service import LinkExtractorService
from services import session_store
from services.verification_service import VerificationService


class JobAgent:

    MAX_JOBS_PER_LISTING = 10

    @staticmethod
    def search_jobs(query, filters: Optional[dict] = None, candidate_profile: Optional[dict] = None, interactive=True):
        session = JobAgent.start_search(query, filters=filters, candidate_profile=candidate_profile)
        if interactive:
            JobAgent.prompt_user_until_done(session)
        else:
            JobAgent.wait_until_done(session)
        return session

    @staticmethod
    def start_search(query: str, filters: Optional[dict] = None, candidate_profile: Optional[dict] = None) -> ScoutSession:
        session = ScoutSession()
        session.query = query
        if filters:
            session.filters = filters
        if candidate_profile:
            session.candidate_profile = candidate_profile
        session.status = "searching"
        session_store.save(session)

        worker = threading.Thread(
            target=JobAgent._run_search,
            args=(session, query),
            name=f"scout-{session.session_id[:8]}",
            daemon=True,
        )
        worker.start()
        return session

    @staticmethod
    def _run_search(session: ScoutSession, query: str):
        try:
            session.append_event("search_start", f"Searching for: {query}")
            recency = session.filters.get("posted_within") if session.filters else None

            with sync_playwright() as p:
                context = BrowserService.launch_persistent(p, headless=False)
                session.browser = None
                session.context = context

                # Execute multi-platform parallel discovery across all job portals and ATS sites
                search_page = context.new_page()
                search_results = BrowserService.search_multi_source(
                    search_page,
                    query,
                    filters=session.filters,
                    recency=recency,
                )
                search_page.close()

                # Prepopulate session.jobs immediately with all discovered results so the list is full
                with session.lock:
                    for res in search_results:
                        if not any(j.apply_url == res.url for j in session.jobs):
                            initial_job = Job(
                                title=res.title,
                                apply_url=res.url,
                                source=urlparse(res.url).netloc,
                                status="success",
                                description=f"Job posting from {urlparse(res.url).netloc}",
                            )
                            if session.candidate_profile:
                                try:
                                    from services.profile_service import ProfileService, CandidateProfile
                                    cand = CandidateProfile(**session.candidate_profile)
                                    initial_job = ProfileService.evaluate_match(cand, initial_job)
                                except Exception:
                                    pass
                            session.jobs.append(initial_job)

                    if session.candidate_profile:
                        session.jobs.sort(key=lambda j: (j.match_score is not None, j.match_score or 0), reverse=True)

                # Process and enrich top candidate job pages
                for result in search_results:
                    if session.unresolved_tasks():
                        break
                    JobAgent._drain_user_actions(session)
                    JobAgent._read_result(session, context, result)

                session.agent_finished = True
                session.append_event("agent_finished", f"Finished reading reachable job pages. Discovered {len(session.jobs)} jobs.")

                if session.unresolved_tasks():
                    with session.lock:
                        session.status = "waiting_on_user"
                    session.append_event(
                        "waiting_on_user",
                        "Waiting for you to complete or skip login/verification tasks",
                    )

                while session.unresolved_tasks():
                    JobAgent._drain_user_actions(session)
                    session.wake.wait(timeout=0.5)
                    session.wake.clear()

                with session.lock:
                    session.status = "completed"
                session.append_event("search_completed", "Results are ready")

                # Send top 5 matches via email if configured
                try:
                    from services.notification_service import NotificationService
                    recipient = (session.filters.get("notification_email") if session.filters else None) or NotificationService.get_default_recipient()
                    send_email_flag = session.filters.get("send_email", True) if session.filters else True
                    if send_email_flag and recipient and NotificationService.is_configured() and session.jobs:
                        sorted_jobs = sorted(session.jobs, key=lambda j: (j.match_score is not None, j.match_score or 0), reverse=True)
                        sent = NotificationService.send_top_matches(
                            recipient=recipient,
                            query=session.query,
                            jobs=sorted_jobs,
                            candidate_profile=session.candidate_profile,
                            total_discovered=len(session.jobs),
                        )
                        if sent:
                            session.append_event("email_sent", f"Top 5 matching jobs emailed to {recipient}", {"recipient": recipient})
                except Exception as ne:
                    print(f"[JobAgent] Notification dispatch notice: {ne}")

                context.close()
                session.browser = None
                session.context = None
                session.pages = {}

        except Exception as e:
            session.error = str(e)
            with session.lock:
                session.status = "failed"
            session.append_event("search_failed", str(e))
            session.agent_finished = True

    @staticmethod
    def _next_tab(session: ScoutSession) -> int:
        with session.lock:
            tab_index = session.next_tab_index
            session.next_tab_index += 1
        return tab_index

    MAX_JOBS_PER_LISTING = 15

    @staticmethod
    def _read_result(session: ScoutSession, context, result):
        if len(session.jobs) >= 80:
            return

        print(f"\n[Reading] {result.title} ({result.url})")
        tab_index = JobAgent._next_tab(session)
        page = context.new_page()
        session.pages[tab_index] = page

        page_text = CrawlerService.get_page_text(page, result.url)
        final_url = CrawlerService.current_url(page) or result.url
        gate = VerificationService.detect_from_page(page, final_url, page_text)

        if gate:
            print(f"[Gate] {gate}: {final_url}")
            VerificationService.enqueue(
                session,
                url=final_url,
                reason=gate,
                tab_index=tab_index,
                title=result.title,
            )
            return

        if not page_text.strip():
            print("[Warn] Empty page text; keeping search result reference.")
            with session.lock:
                already = any(j.apply_url == final_url for j in session.jobs)
                if not already:
                    session.jobs.append(
                        Job(
                            title=result.title,
                            apply_url=final_url,
                            source=urlparse(final_url).netloc,
                            status="success",
                            description="Direct listing from search results.",
                        )
                    )
            JobAgent._close_tab(session, tab_index)
            return

        # 1. Always extract the parent search result / listing page itself so search results are never lost
        JobAgent._extract_into_session(
            session,
            page_text,
            final_url,
            fallback_title=result.title,
        )

        # 2. Extract and drill into any individual job links found on this page
        job_links = LinkExtractorService.extract_job_links(
            page,
            final_url,
            limit=JobAgent.MAX_JOBS_PER_LISTING,
        )

        JobAgent._close_tab(session, tab_index)

        if job_links:
            print(f"[Discovery] Found {len(job_links)} individual sub-job links; drilling into details...")
            for link in job_links[: JobAgent.MAX_JOBS_PER_LISTING]:
                if len(session.jobs) >= 80:
                    break
                JobAgent._drain_user_actions(session)
                JobAgent._read_job_detail(session, context, link, fallback_title=result.title)

    @staticmethod
    def _read_job_detail(session: ScoutSession, context, url: str, fallback_title: str = ""):
        with session.lock:
            if any(j.apply_url == url for j in session.jobs):
                return

        print(f"\n[Detail] {url}")
        tab_index = JobAgent._next_tab(session)
        page = context.new_page()
        session.pages[tab_index] = page

        page_text = CrawlerService.get_page_text(page, url)
        final_url = CrawlerService.current_url(page) or url
        gate = VerificationService.detect_from_page(page, final_url, page_text)

        if gate:
            print(f"[Gate] {gate}: {final_url}")
            VerificationService.enqueue(
                session,
                url=final_url,
                reason=gate,
                tab_index=tab_index,
                title=fallback_title,
            )
            return

        if not page_text.strip():
            with session.lock:
                already = any(j.apply_url == final_url for j in session.jobs)
                if not already:
                    session.jobs.append(
                        Job(
                            title=fallback_title,
                            apply_url=final_url,
                            source=urlparse(final_url).netloc,
                            status="success",
                            description="Individual job posting reference.",
                        )
                    )
            JobAgent._close_tab(session, tab_index)
            return

        JobAgent._extract_into_session(
            session,
            page_text,
            final_url,
            fallback_title=fallback_title,
        )
        JobAgent._close_tab(session, tab_index)

    @staticmethod
    def _extract_into_session(
        session: ScoutSession,
        page_text: str,
        url: str,
        fallback_title: str = "",
    ):
        try:
            job = ExtractorService.extract_job(
                page_text,
                url,
                session=session,
                fallback_title=fallback_title,
            )

            # If candidate profile is attached, evaluate match
            if session.candidate_profile:
                try:
                    from services.profile_service import ProfileService, CandidateProfile
                    cand = CandidateProfile(**session.candidate_profile)
                    job = ProfileService.evaluate_match(cand, job)
                except Exception as pe:
                    print(f"[Match Score Warning] {pe}")

            score_str = f" (Match: {job.match_score}%)" if job.match_score is not None else ""
            print(f"[OK] Extracted ({len(session.jobs)}): {job.title}{score_str}")

            with session.lock:
                # If this job exists in pre-populated list, update it in place
                updated = False
                for idx, existing in enumerate(session.jobs):
                    if existing.apply_url == job.apply_url:
                        session.jobs[idx] = job
                        updated = True
                        break

                if not updated:
                    # Check if duplicate title+company
                    if not any(j.title and job.title and j.title.lower() == job.title.lower() and j.company and job.company and j.company.lower() == job.company.lower() for j in session.jobs):
                        session.jobs.append(job)

                if session.candidate_profile:
                    session.jobs.sort(key=lambda j: (j.match_score is not None, j.match_score or 0), reverse=True)
        except Exception as e:
            print(f"[Error] Extraction notice: {e}")

    @staticmethod
    def _close_tab(session: ScoutSession, tab_index: int):
        page = session.pages.pop(tab_index, None)
        if page is None:
            return
        try:
            page.close()
        except Exception:
            pass

    @staticmethod
    def _drain_user_actions(session: ScoutSession):
        with session.lock:
            tasks = list(session.pending_verifications)

        for task in tasks:
            page = session.pages.get(task.tab_index)

            if task.status == "accepted" and not task.brought_to_front and page is not None:
                try:
                    page.bring_to_front()
                except Exception:
                    pass
                with session.lock:
                    task.brought_to_front = True

            if task.status == "declined" and not task.extracted:
                JobAgent._close_tab(session, task.tab_index)
                VerificationService.mark_skipped_job(session, task)
                with session.lock:
                    task.extracted = True

            if task.status == "completed" and not task.extracted:
                JobAgent._extract_verified_tab(session, task)

    @staticmethod
    def _extract_verified_tab(session: ScoutSession, task):
        page = session.pages.get(task.tab_index)
        if page is None:
            with session.lock:
                session.jobs.append(
                    Job(
                        title=task.title,
                        apply_url=task.url,
                        source=task.site,
                        status="blocked",
                        error="Browser tab was already closed",
                    )
                )
                task.extracted = True
            return

        try:
            page_text = page.locator("body").inner_text()
            final_url = CrawlerService.current_url(page) or task.url
        except Exception as e:
            with session.lock:
                session.jobs.append(
                    Job(
                        title=task.title,
                        apply_url=task.url,
                        source=task.site,
                        status="blocked",
                        error=f"Could not read tab after verification: {e}",
                    )
                )
                task.extracted = True
            JobAgent._close_tab(session, task.tab_index)
            return

        still_gated = VerificationService.detect_from_page(page, final_url, page_text)
        if still_gated:
            with session.lock:
                session.jobs.append(
                    Job(
                        title=task.title,
                        apply_url=final_url,
                        source=task.site,
                        status="blocked",
                        error=f"Still requires {still_gated} after the task was marked complete",
                    )
                )
                task.extracted = True
            JobAgent._close_tab(session, task.tab_index)
            return

        JobAgent._extract_into_session(
            session,
            page_text,
            final_url,
            fallback_title=task.title,
        )
        with session.lock:
            task.extracted = True
        JobAgent._close_tab(session, task.tab_index)

    @staticmethod
    def wait_until_done(session: ScoutSession, timeout: float = 900):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if session.status in ("completed", "failed"):
                return session
            time.sleep(0.4)
        raise TimeoutError("Scout session did not finish in time")

    @staticmethod
    def prompt_user_until_done(session: ScoutSession):
        prompted = set()
        print("\nAgent is searching in the background.")
        print("If a site needs login or human verification, you will be asked here.\n")

        while session.status not in ("completed", "failed"):
            with session.lock:
                tasks = list(session.pending_verifications)

            for task in tasks:
                if task.task_id in prompted:
                    continue
                if task.status != "pending":
                    continue

                prompted.add(task.task_id)
                print("-" * 60)
                print(f"Task: {task.reason} on {task.site}")
                if task.title:
                    print(f"Page: {task.title}")
                print(f"URL:  {task.url}")
                answer = input("Complete this in the open browser window? [y/n]: ").strip().lower()

                if answer in ("n", "no"):
                    try:
                        VerificationService.set_status(session, task.task_id, "declined")
                    except ValueError:
                        pass
                    print("Skipped. The agent keeps working.\n")
                    continue

                try:
                    VerificationService.set_status(session, task.task_id, "accepted")
                except ValueError:
                    continue

                print("Complete login or verification in the Chromium window.")
                print("The agent will keep processing other pages in the background.")
                done = input("Press Enter when finished, or type skip to decline: ").strip().lower()
                try:
                    if done in ("skip", "n", "no"):
                        VerificationService.set_status(session, task.task_id, "declined")
                    else:
                        VerificationService.set_status(session, task.task_id, "completed")
                except ValueError:
                    pass

            if session.status in ("completed", "failed"):
                break
            time.sleep(0.4)

        if session.status == "failed":
            print(f"\nSearch failed: {session.error}")
        else:
            print("\nResults are ready.")
