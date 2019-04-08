from ..django_conf import Conf


class CeleryConf(Conf):
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
