import nox


@nox.session(python=["3.6", "3.7"])
def tests(session):
    session.install("-e", ".[scipy]")
    session.install("pytest")
    session.run("pytest", "--disable-warnings")
