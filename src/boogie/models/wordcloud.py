import sidekick as sk

from .queryset import QuerySet

wc = sk.import_later("wordcloud")


class WordCloudQuerySet(QuerySet):
    """
    A queryset that exposes a word_cloud() method to display a word cloud from
    some fields extracted from a queryset.
    """

    def word_cloud(self, *fields, **kwargs):
        """
        Return an word cloud from the given fields spanning all values in the
        queryset.

        See Also:
            see :func:`word_cloud` for additional options.
        """
        return word_cloud(self, fields=fields, **kwargs)


def word_cloud(qs, fields=(), lang="en", sep="\n", stop_words=None, **kwargs):
    """
    Creates a word-cloud object from queryset.

    Args:
        qs:
            Queryset
        fields:
            Fields used to extract text from queryset.
        lang:
            Language in which the word cloud is defined.
        stop_words:
            List of words that should be ignored in the final result.
        sep:
            Separator used to join content of different entries of the queryset.
            Defaults to a new line.
    """
    data = sep.join(sk.flatten(qs.values_list(*fields)))
    cloud = wc.WordCloud(**kwargs)
    return cloud.generate(data)
