import nox

@nox.session(python=['3.6', '3.7'])
def tests(session):
    session.install('.')
    session.install('pytest')
    session.run('pytest')
