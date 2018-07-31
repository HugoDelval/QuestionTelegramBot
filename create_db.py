import model
import subprocess

if __name__ == "__main__":
    subprocess.call(["rm", "-f", model.db_name])
    model.create_db()
