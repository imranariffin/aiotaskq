import subprocess


def test_simple_app():
    proc_aiotaskq = subprocess.run(
        ["sh", "./demo-sample-apps-simple-app-aiotaskq.sh"],
        check=False,
    )
    proc_celery = subprocess.run(
        ["sh", "./demo-sample-apps-simple-app-celery.sh"],
        check=False,
    )
    assert proc_aiotaskq.returncode == proc_celery.returncode == 0
