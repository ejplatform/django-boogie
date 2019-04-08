import os
import sys

from invoke import task

python = sys.executable


@task
def run(ctx, no_toolbar=False):
    """
    Run development server
    """
    env = {}
    if no_toolbar:
        env["DISABLE_DJANGO_DEBUG_TOOLBAR"] = "true"
    else:
        manage(ctx, "runserver 0.0.0.0:8000", env=env)


@task
def gunicorn(ctx, debug=None, environment="production", port=8000, workers=4):
    """
    Run application using gunicorn for production deploys.

    It assumes that static media is served by a reverse proxy.
    """

    from gunicorn.app.wsgiapp import run as run_gunicorn

    directory = ""

    env = {
        "DISABLE_DJANGO_DEBUG_TOOLBAR": str(not debug),
        "PYTHONPATH": "src",
        "DJANGO_ENVIRONMENT": environment,
    }
    if debug is not None:
        env["DJANGO_DEBUG"] = str(debug).lower()
    os.environ.update(env)
    args = [
        "ej.wsgi",
        "-w",
        str(workers),
        "-b",
        f"0.0.0.0:{port}",
        "--error-logfile=-",
        "--access-logfile=-",
        "--log-level",
        "info",
        f"--pythonpath={directory}/src",
    ]
    sys.argv = ["gunicorn", *args]
    run_gunicorn()


@task
def clean_migrations(ctx, all=False, yes=False):
    """
    Remove all automatically created migrations.
    """
    import re

    auto_migration = re.compile(r"\d{4}_auto_\w+.py")
    all_migration = re.compile(r"\d{4}\w+.py")

    rm_list = []
    for app in os.listdir("src"):
        migrations_path = f"src/{app}/migrations/"
        if os.path.exists(migrations_path):
            migrations = os.listdir(migrations_path)
            if "__pycache__" in migrations:
                migrations.remove("__pycache__")
            if all:
                rm_list.extend(
                    [
                        f"{migrations_path}{f}"
                        for f in migrations
                        if all_migration.fullmatch(f)
                    ]
                )
            elif sorted(migrations) == ["__init__.py", "0001_initial.py"]:
                rm_list.append(f"{migrations_path}/0001_initial.py")
            else:
                rm_list.extend(
                    [
                        f"{migrations_path}/{f}"
                        for f in migrations
                        if auto_migration.fullmatch(f)
                    ]
                )
    remove_files(rm_list, yes)


def remove_files(remove_files, yes):
    print("Listing auto migrations")
    for file in remove_files:
        print(f"* {file}")
    if all:
        print(
            "REMOVING ALL MIGRATIONS IS DANGEROUS AND SHOULD ONLY BE " "USED IN TESTING"
        )
    if yes or input("Remove those files? (y/N)").lower() == "y":
        for file in remove_files:
            os.remove(file)


#
# DB management
#
@task
def db(ctx, migrate_only=False):
    """
    Perform migrations
    """
    if not migrate_only:
        manage(ctx, "makemigrations")
    manage(ctx, "migrate")


@task
def db_reset(ctx):
    """
    Reset data in database and optionally fill with fake data
    """
    ctx.run("rm -f local/db/db.sqlite3")
    manage(ctx, "migrate")


@task
def db_fake(ctx, users=True, conversations=True, admin=True, safe=False, theme=None):
    """
    Adds fake data to the database
    """
    set_theme(theme)
    msg_error = "Release build. No fake data will be created!"

    if safe:
        if os.environ.get("FAKE_DB") == "true":
            print("Creating fake data...")
        else:
            return print(msg_error)
    if users:
        manage(ctx, "createfakeusers", admin=admin)
    if conversations:
        manage(ctx, "createfakeconversations")


#
# Utility functions
#
def manage(ctx, cmd, env=None, **kwargs):
    """
    Call python manage.py in a more robust way
    """
    kwargs = {k.replace("_", "-"): v for k, v in kwargs.items() if v is not False}
    opts = " ".join(f'--{k} {"" if v is True else v}' for k, v in kwargs.items())
    cmd = f"{python} manage.py {cmd} {opts}"
    env = {**os.environ, **(env or {})}
    path = env.get("PYTHONPATH", ":".join(sys.path))
    env.setdefault("PYTHONPATH", f"src:{path}")
    ctx.run(cmd, pty=True, env=env)


set_theme = lambda *args: None
