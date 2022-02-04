import nox


@nox.session(python=["3.7", "3.8", "3.9", "3.10"])
def tests(session):
    session.install(".[all]")
    session.install(".[tests]")
    session.run("pytest", "--disable-warnings", "--asyncio-mode=auto")
