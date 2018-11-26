================================
Business logic: values and rules
================================

Even though Django claims to be an MVC, the way it split the "model", "view" and
"controller" parts is not typical of most MVC frameworks. It a way, that is a
symptom of MVC being more like a meta-architecture/principle than a
concrete way of organizing code. This is specially confusing in the case of most big
frameworks written in dynamic languages. The role of the "model" layer is
greatly simplified by having most interactions with the database automatically
derived from the model declaration. Similarly, the "view logic" is delegated to
powerful templating languages, which leave us with the bulk of our application
in the "controller" bin. By placing no further structure in our controllers,
we are in for a tangled mess of code and a very bad, but formally correct MVC
architecture.

Django claims that the "controller" is the framework itself, with all the
automatic wiring between different parts. While this may be partially true, it
leaves an important aspect out: where code pertaining the business logic should
live? In most Django projects, developers have to decide between two evils:
the "fat views" (i.e., the greater evil) or "fat models" (the lesser evil)
approaches.

Ideally, business logic should live in a separate module in order to promote better
separation of concerns. Boogie favors the approach introduced by a third part
app called django-rules_. Rules model requirements as simple functions that
return boolean values. This is great for many
situations: give/deny authorization to a resource, check if user has some
permission, determine if some service or resource is available to a user, etc.
Boogie expands on this idea, but let us talk about the rules module first.

.. _django-rules: https://pypi.org/project/rules/

Rules start their life as a decorated function that returns a boolean value
(possibly in a rules.py file inside your app). Those types of functions are
known as predicates

.. code-block:: python

    import rules

    @rules.predicate
    def is_closed(classroom):
        return classroom.is_closed

    @rules.predicate
    def is_full(classroom):
        return classroom.students.count() < classroom.max_students

    @rules.predicate(bind=True)
    def is_allowed_to_join(self, classroom, student):
        if student is None:
            return None
        return not classroom.is_blocked(student)

    rules.add_rule('classroom.accept_subscription',
             ~is_closed & ~is_full & is_allowed_to_join)

We can easily test a rule in other parts of our code by invoking it from its
name:

.. ignore-next-block
.. code-block:: python

    if rules.test_rule('classroom.accept_subscription', classroom, user):
        subscribe_user(classroom, user)
    else:
        show_error(classroom, user)


Predicate functions can have any of 3 signatures::

    func()            -> global boolean value
    func(obj)         -> test object capability
    func(obj, target) -> test a object relationship with target resource

This framework is great for modelling permissions and generic authorization
rules. In fact, if the subject of the rule is a User instance, Rules make it
possible to integrate with Django's permission system. In order
to do so, use ``rules.add_perm`` instead of ``rules.add_rule`` and the rule will
be tested using the builtin ``user.has_perm('rule name', target)`` method.

With rules, we have a predictable place to put business logic that can be
declared by defining and composing very simple predicate functions. While this
is very convenient, it has a shortcoming: predicate functions only provide
boolean values. This leaves all business logic that requires more sophisticated
data out of the framework.

Following a similar logic, boogie defines "value" functions that compute any
arbitrary value from arbitrary objects. Similarly to rules, value functions can
have 3 types of signatures

    func()          -> constant or global value
    func(obj)       -> a value associated with the object
    func(obj, user) -> a value associated with the object when accessed by user

Like predicates in django rules, value variables can be composed further using
simple mathematical operations.

.. code-block:: python

    # A drop-in replacement to the original module
    from boogie import rules

    @rules.value
    def total_points(user):
        return PointsGiven.objects.filter(user=user).sum()

    @rules.value
    def programming_points(user):
        return PointsGiven.objects.filter(user=user, category='programming').sum()

    rules.add_value('programming_fraction', programming_points / total_points)

Now we can use those functions to extract information about a user:

>>> rules.compute('programming_fraction', user)                 # doctest: +SKIP
0.42
