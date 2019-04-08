import os

from invoke import task


@task
def clean(ctx):
    """
    Clean pyc files and build assets.
    """
    join = os.path.join
    rm_files = []
    rm_dirs = []
    for base, subdirs, files in os.walk("."):
        if "__pycache__" in subdirs:
            rm_dirs.append(join(base, "__pycache__"))
        elif os.path.basename(base) == "__pycache__":
            rm_files.extend(join(base, f) for f in files)

    print("Removing compiled bytecode files")
    for path in rm_files:
        os.unlink(path)
    for path in rm_dirs:
        os.rmdir(path)
