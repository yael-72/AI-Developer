"""
סנדבוקס Docker — הרצה מבודדת, חד-פעמית ומבוקרת של פקודות CLI.

כל פקודה רצה בתוך קונטיינר Alpine נפרד עם:
  --rm                    קונטיינר נמחק מיד לאחר הרצה
  --cap-drop=ALL          ללא כל הרשאות Linux
  --security-opt          ללא הסלמת הרשאות
  --memory=64m            מגבלת זיכרון
  --cpus=0.5              מגבלת מעבד
  --user=65534            הרצה כ-nobody
  --network=none          ניתוק רשת (למעט פקודות רשת)

בנייה חד-פעמית לפני השימוש:
  docker build -f Dockerfile.sandbox -t proptproject-sandbox .
"""

import subprocess

from proptproject.evaluator import SAFE_COMMANDS, evaluate

SANDBOX_TIMEOUT = 10
DOCKER_IMAGE = "proptproject-sandbox:latest"

# תרגום פקודות Windows לפקודות Linux מקבילות
_WIN_TO_LINUX: dict[str, str] = {
    "dir":      "ls -la",
    "ipconfig": "ip addr show",
    "tasklist": "ps aux",
    "systeminfo": "uname -a",
    "ver":      "uname -r",
    "cls":      ":",
    "type":     "cat",
    "where":    "which",
    "path":     "echo $PATH",
    "set":      "env",
    "tracert":  "traceroute",
    "fc":       "diff",
    "comp":     "diff",
}

# פקודות שדורשות גישה לרשת
_NETWORK_CMDS = {"ping", "tracert", "traceroute", "nslookup", "netstat", "ipconfig"}


def _translate(command: str) -> str:
    """ממיר פקודת Windows לפקודת Linux מקבילה."""
    tokens = command.strip().split(None, 1)
    if not tokens:
        return command
    win_cmd = tokens[0].lower().rstrip("/\\")
    rest = tokens[1] if len(tokens) > 1 else ""
    linux_cmd = _WIN_TO_LINUX.get(win_cmd, win_cmd)
    return f"{linux_cmd} {rest}".strip()


def _image_exists() -> bool:
    result = subprocess.run(
        ["docker", "--context=default", "image", "inspect", DOCKER_IMAGE],
        capture_output=True,
    )
    return result.returncode == 0


def run_in_sandbox(command: str) -> str:
    if not command.strip():
        return ""

    result = evaluate(command)
    first_token = command.strip().split()[0].lower().rstrip("/\\")

    if result.safety_level == "dangerous":
        return "🔴 פקודה מסוכנת — חסומה לחלוטין. לא תורץ."

    if result.safety_level == "risky":
        return (
            "🟡 פקודה זו משנה קבצים או מצב המערכת.\n"
            "לא מורצת אוטומטית — בדקי את הפקודה ידנית לפני הרצה."
        )

    if not result.runnable or first_token not in SAFE_COMMANDS:
        return "⚠️ פקודה זו אינה ניתנת לאימות בסביבת הסנדבוקס."

    try:
        if not _image_exists():
            return (
                "❌ תמונת Docker לסנדבוקס לא נמצאה.\n"
                "הרץ תחילה:\n"
                "  docker build -f Dockerfile.sandbox -t proptproject-sandbox ."
            )
    except FileNotFoundError:
        return "❌ Docker אינו מותקן או אינו נגיש ב-PATH."

    linux_command = _translate(command)
    needs_network = first_token in _NETWORK_CMDS

    docker_cmd = [
        "docker", "--context=default", "run", "--rm",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--memory=64m",
        "--cpus=0.5",
        "--user=65534",
    ]
    if not needs_network:
        docker_cmd.append("--network=none")

    docker_cmd += [DOCKER_IMAGE, "sh", "-c", linux_command]

    try:
        proc = subprocess.run(
            docker_cmd,
            capture_output=True,
            timeout=SANDBOX_TIMEOUT,
        )
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        output = stdout or stderr or "(אין פלט)"
        exit_code = proc.returncode
        status = "✅ הצליח" if exit_code == 0 else f"❌ שגיאה (exit {exit_code})"
        return f"{status}\n\n{output.strip()}"

    except subprocess.TimeoutExpired:
        return f"⏱️ הפקודה חרגה מ-{SANDBOX_TIMEOUT} שניות."
    except Exception as exc:
        return f"שגיאה בהרצה: {exc}"
