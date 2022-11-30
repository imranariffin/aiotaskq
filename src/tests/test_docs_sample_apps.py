import subprocess


def test_simple_app():
    proc_aiotaskq = subprocess.run(
        ["sh", "./demo-sample-apps-simple-app.sh"]
    )
    proc_celery = subprocess.run(
        ["sh", "./demo-sample-apps-simple-app-celery.sh"]
    )
    assert proc_aiotaskq.returncode == proc_celery.returncode == 0


def test_simple_app_implicit_instance():
    proc_aiotaskq = subprocess.run(
        ["sh", "./demo-sample-apps-simple-app-implicit-instance.sh"]
    )
    proc_celery = subprocess.run(
        ["sh", "./demo-sample-apps-simple-app-implicit-instance-celery.sh"]
    )
    assert proc_aiotaskq.returncode == proc_celery.returncode == 0
