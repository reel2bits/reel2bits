from setuptools import setup

setup(
    name='reel2bits',
    version='0.1',
    license='MIT',
    long_description=open('README.md').read(),
    url="http://dev.sigpipe.me/DashieV3/reel2bits",
    author="Dashie 'Valérianne'",
    author_email="dashie@sigpipe.me",
    install_requires=[
        'WTForms',
        'WTForms-Alchemy',
        'SQLAlchemy',
        'SQLAlchemy-Searchable',
        'SQLAlchemy-Utils',
        'SQLAlchemy-Continuum',
        'Flask',
        'Flask-Bootstrap',
        'Flask-DebugToolbar',
        'Flask-Login',
        'Flask-Mail',
        'Flask-Migrate',
        'Flask-Principal',
        'Flask-Security',
        'Flask-SQLAlchemy',
        'Flask-Uploads',
        'Flask-WTF'
    ]
)

