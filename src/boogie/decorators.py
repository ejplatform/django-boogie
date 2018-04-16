def api_fields(fields):
    """
    Decorator that marks the API fields in a class.

    Usage:

        .. code-block:: python

            from boogie.decorators import api_fields
            from boogie import models


            @api_fields(['title', 'author'])
            class Book(models.Model):
                title = models.CharField(max_length=50)
                author = models.CharField(max_length=50)
                isbn = models.CharField(max_length=50)
    """
    def decorator(cls):
        cls._api_fields = {
            'fields': fields,
        }
        return cls
    return decorator
