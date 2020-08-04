from datetime import timedelta

from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse

from team.models import Iteration, Report, Task, Tracker, Worker


class TeamBaseTestCase(TestCase):

    def setUp(self) -> None:
        super().setUp()
        tracker = Tracker.objects.create(
            name='Jira',
            url='https://jira.test.com/browse/',
        )
        Task.objects.bulk_create([
            Task(tracker=tracker, number='XYZ-001', title='Test task #1'),
            Task(tracker=tracker, number='XYZ-002', title='Test task #2'),
            Task(tracker=tracker, number='XYZ-003', title='Test task #3'),
            Task(tracker=tracker, number='XYZ-004', title='Test task #4'),
            Task(tracker=tracker, number='XYZ-005', title='Test task #5'),
            Task(tracker=tracker, number='XYZ-006', title='Test task #6'),
        ])
        Worker.objects.bulk_create([
            Worker(name='John', email='j@test.com'),
            Worker(name='Mike', email='m@test.com'),
        ])
        self.tasks = tuple(Task.objects.all())
        self.workers = tuple(Worker.objects.all())
        self.iteration = Iteration.objects.create()

        Report.objects.bulk_create([
            Report(iteration=self.iteration, worker=self.workers[0], task=self.tasks[0]),
            Report(iteration=self.iteration, worker=self.workers[0], task=self.tasks[1], status=Report.IN_PROGRESS),
            Report(iteration=self.iteration, worker=self.workers[0], task=self.tasks[2], status=Report.DONE),
            Report(iteration=self.iteration, worker=self.workers[1], task=self.tasks[3]),
            Report(iteration=self.iteration, worker=self.workers[1], task=self.tasks[4], status=Report.IN_PROGRESS),
            Report(iteration=self.iteration, worker=self.workers[1], task=self.tasks[5], status=Report.DONE),
        ])


class ReportTestCase(TeamBaseTestCase):

    def test_update(self):
        report = Report.objects.filter(status=Report.PLANNED).first()
        comment = report.comment + '_add comment'
        status = Report.IN_PROGRESS
        delegation = Report.DELEGATION_CHOICES[0][0]  # tell
        url = '/reports/{}/update/'.format(report.id)

        self.assertNotEqual(comment, report.comment)
        self.assertNotEqual(status, report.status)
        self.assertNotEqual(delegation, report.delegation)
        self.assertNotEqual(self.workers[1].pk, report.worker_id)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

        resp = self.client.post(
            url,
            data={
                'comment': comment,
                'status': status,
                'delegation': delegation,
                'worker': self.workers[1].pk,
            },
        )
        self.assertEqual(resp.status_code, 302)

        report.refresh_from_db(fields=('comment', 'status', 'worker'))
        self.assertEqual(report.comment, comment)
        self.assertEqual(report.status, status)
        self.assertNotEqual(delegation, report.delegation)
        self.assertEqual(self.workers[1].pk, report.worker_id)

    def test_create(self):
        delegation = Report.DELEGATION_CHOICES[0][0]  # tell
        report_ids = set(Report.objects.values_list('id', flat=True))
        worker = Worker.objects.first()
        url = '/reports/create/{iteration_id}/{worker_id}/'.format(
            iteration_id=self.iteration.id,
            worker_id=worker.id,
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

        data = {
            'number': 'https://jira.test.com/browse/XYZ-007',
            'title': 'This is test comment',
            'comment': 'test comment',
            'delegation': delegation,
            'status': Report.DONE,
        }
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 302)

        r = Report.objects.filter(worker=worker).order_by('id').last()
        self.assertIsNotNone(r)
        self.assertNotIn(r.id, report_ids)
        self.assertEqual(r.status, Report.DONE)
        self.assertEqual(r.delegation, delegation)


class IterationTestCase(TeamBaseTestCase):

    def test_index(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertInHTML(str(self.iteration), resp.content.decode())

    def test_view(self):
        resp = self.client.get('/iterations/{}/'.format(self.iteration.id))
        self.assertEqual(resp.status_code, 200)
        self.assertInHTML(str(self.iteration), resp.content.decode())

    def test_create(self):
        url = '/iterations/{}/create/'.format(self.iteration.id)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

        iteration_ids = set(Iteration.objects.values_list('id', flat=True))
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)

        iteration = Iteration.objects.first()
        self.assertIsNotNone(iteration)
        self.assertNotIn(iteration.id, iteration_ids)
        self.assertEqual(iteration.start, self.iteration.stop + timedelta(days=1))

        report_ids = set(self.iteration.reports.exclude(status=Report.DONE).values_list('task_id', flat=True))
        migrated_reports = tuple(iteration.reports.values_list('task_id', 'status'))

        self.assertEqual(report_ids, {task_id for task_id, _ in migrated_reports})
        self.assertTrue(all(status == Report.PLANNED for _, status in migrated_reports))

    def test_failed_create(self):
        url = '/iterations/{}/create/'.format(self.iteration.id)
        self.assertEqual(Iteration.objects.count(), 1)

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Iteration.objects.count(), 2)

        # base iteration is not the latest
        self.client.post(url)
        self.assertEqual(Iteration.objects.count(), 2)

    def test_update(self):
        url = '/iterations/{}/update/'.format(self.iteration.id)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

        comment = self.iteration.comment + '_add comment'
        resp = self.client.post(url, data={'comment': comment})
        self.assertEqual(resp.status_code, 302)

        i = Iteration.objects.get(id=self.iteration.id)
        self.assertEqual(i.comment, comment)

    def _export(self, url: str) -> None:
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 405)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()

        for r in self.iteration.reports.select_related('worker', 'task__tracker'):
            self.assertIn(r.worker.name, content)
            task = '{} {}'.format(r.task.url, r.task.title)
            self.assertIn(task, content)

    def test_export(self):
        url = '/iterations/{}/export/'.format(self.iteration.id)
        self._export(url)

    def test_export_planned(self):
        url = '/iterations/{}/export/planned/'.format(self.iteration.id)
        self._export(url)


class FlatPagesTestCase(TestCase):

    def setUp(self) -> None:
        super().setUp()
        site = Site.objects.get(pk=settings.SITE_ID)
        self.flat_page = FlatPage.objects.create(
            url='/about/',
            title='About',
            content='about',
        )
        self.flat_page.sites.add(site)

    def test_about(self):
        url = reverse('about')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        tpl = '<title>{}</title>'
        self.assertContains(resp, tpl.format(self.flat_page.title), html=True)
