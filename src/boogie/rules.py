import rules as _rules


class Rules:
    """
    Implement the "rules" attribute of a model.

    This attribute decouples all business rules regarding authorization from the
    model class. The goal is to implement thinner models.
    """

    def __init__(self, model=None):
        self.model = model

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        if self.model:
            return self
        return Rules(instance)

    def _test_multilple(self, user, rule_list, reducer, test):
        """
        Common implementation to test() and test_any()
        """
        model = self.model
        return user.is_superuser or reducer(
            test(rule, user, model) for rule in rule_list
        )

    def test(self, user, *rules):
        """
        Return True if user has all given permissions.
        """
        return self._test_multilple(user, rules, all, _rules.test_rule)

    def test_any(self, user, *rules):
        """
        Return True if user has any of the given permissions.
        """
        return self._test_multilple(user, rules, any, _rules.test_rule)

    def has_perm(self, user, *rules):
        """
        Return True if user has all given permissions.
        """
        return self._test_multilple(user, rules, all, _rules.has_perm)

    def has_perm_any(self, user, *rules):
        """
        Return True if user has any of the given permissions.
        """
        return self._test_multilple(user, rules, any, _rules.has_perm)
