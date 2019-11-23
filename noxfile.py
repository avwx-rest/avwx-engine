import nox


@nox.session(python=["3.6", "3.7", "3.8"])
def tests(session):
    session.install("-e", ".[scipy]")
    session.install("pytest~=5.3")
    session.run("pytest", "--disable-warnings")
