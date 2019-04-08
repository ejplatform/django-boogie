"""
Random Phrases
--------------

Generate human-friendly random strings. Phrases are usually of the form
"adjective" + "subjective". We try to use mostly characters from Science and
Science fiction movies.

The main entry point is the :func:`phrase` function, that simply returns a
random phrase. If you want to learn more, read the source :)

.. autofunction :: phrase
"""

import random

from faker import Factory

fake = Factory.create("en-us")

star_wars_characters = [
    "Han Solo",
    "Darth Vader",
    "C3PO",
    "R2D2",
    "Luke Skywalker",
    "Princess Leia",
    "Jabba",
    "Obi Wan",
    "Yoda",
    "Jar Jar Binks",
]
famous_scientists = [
    # Physicists
    "Einstein",
    "Newton",
    "Dirac",
    "Bohr",
    "Rutherford",
    "Heisenberg",
    "Curie",
    "Langevin",
    "Boltzmann",
    # Mathematicians
    "Pythagoras",
    "Peano",
    "Hilbert",
    "Gauss",
    "Galois",
    # Computer science
    "Knuth",
    "Turing",
    "Tim",
    # Biology
    "Darwin",
    "Mendel",
    "Lamarck",
    "Mayr",
    "Dobzhansky",
]
adjective_list = [
    "grumpy",
    "heroic",
    "coward",
    "brave",
    "treacherous",
    "powerful",
    "influential",
]
phrase_groups = []


def is_phase_provider(func):
    phrase_groups.append(func)
    return func


def phrase(maker=None):
    """
    A random easy to memorize phrase.
    """
    maker = random.choice(phrase_groups)
    return maker()


def phrase_lower(maker=None):
    """
    Like phrase, but normalize to lowercase results.
    """
    maker = random.choice(phrase_groups)
    return maker().lower()


def subjective_adjective_phrase(subjectives=None, adjectives=None):
    """
    Return a new subjective-adjective phrase such as "Grumpy Einstein" from a
    list of subjectives and adjectives.
    """
    subjective = random.choice(subjectives or famous_scientists)
    adjective = random.choice(adjectives or adjective_list)
    return "%s %s" % (adjective.title(), subjective)


@is_phase_provider
def random_star_wars_phrase():
    """
    Random phrase based on Star Wars ;-)
    """
    return subjective_adjective_phrase(star_wars_characters)


@is_phase_provider
def random_scientist_phrase():
    """
    Random phrase using important scientists.
    """
    return subjective_adjective_phrase(famous_scientists)


@is_phase_provider
def random_fake_phrase():
    """
    Use fake-factory names.
    """
    return subjective_adjective_phrase([fake.first_name()])


@is_phase_provider
def random_fake_catch():
    """
    Catch phrases
    """
    return fake.catch_phrase()
