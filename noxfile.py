import nox


@nox.session(python=["3.6", "3.7"])
def tests(session):
    session.install("-e", ".[scipy]")
    session.install("pytest~=5.0")
    session.run("pytest", "--disable-warnings")
