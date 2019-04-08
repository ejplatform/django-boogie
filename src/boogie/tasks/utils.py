import os


def execute(func: callable, *, watch=False, background=False, **kwargs):
    """
    Execute function. It can perform execution on the background or schedule
    execution by watching changes under some given path in the filesystem.

    Args:
        func (callable):
            A callable that receives no arguments.
        watch (bool):
            If True, execute in watch mode. You probably will want to specify
            an optional path argument to determine the watch location.
        background (bool):
            If True, runs in a background thread.

    See Also:
        See :func:`watch` for options on executing in watch mode.
    """

    if watch and background:
        go = lambda: _watch(func, **kwargs)
        return execute(go, background=True)
    elif watch:
        return _watch(func, **kwargs)
    elif background:
        from threading import Thread

        def go():
            try:
                func()
            except KeyboardInterrupt:
                pass

        thread = Thread(target=go, daemon=True)
        thread.start()
    else:
        func()


def watch(  # noqa: C901
    func: callable, path: str = None, *, poll_time=0.5, skip_first=False, name=None
):
    """
    Execute function and re-execute if everytime a file under the given path
    changes.
    """

    import time
    from watchdog.observers import Observer
    from watchdog.events import (
        FileSystemEventHandler,
        FileCreatedEvent,
        FileDeletedEvent,
        FileModifiedEvent,
        FileMovedEvent,
    )

    # Create the dispatch function that throttles execution so func is
    # executed at most every poll_time seconds
    file_event = (FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent)
    last = time.time()

    def dispatch(ev):
        nonlocal last

        if (
            ev.src_path.endswith("__")
            or ev.src_path.startswith("__")
            or ev.src_path.startswith("~")
            or ev.src_path.startswith(".")
        ):
            return

        if isinstance(ev, file_event):
            last = start = time.time()
            time.sleep(poll_time)
            if last == start:
                print(f"File modified: {ev.src_path}")
                func()

    # Initialize observer and mokey-match the instance dispatch method
    observer = Observer()
    handler = FileSystemEventHandler()
    handler.dispatch = dispatch
    observer.schedule(handler, path or os.getcwd(), recursive=True)
    observer.start()
    name = name or func.__name__

    # Starts execution loop
    print(f"Running {name} in watch mode.")
    if not skip_first:
        func()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


_watch = watch
