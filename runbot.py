import os
import sys
import subprocess
import requests
import time

TOKEN = "ТВОЙ_ТОКЕН"  # <=== вставь сюда токен

# ================= 1. Удаляем старый вебхук =================
print("🧹 Удаляем старый вебхук...")
r = requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
if r.ok:
    print("✅ Вебхук удалён")
else:
    print("⚠️ Не удалось удалить вебхук")

# ================= 2. Проверяем другие процессы =================
print("🔎 Проверяем, есть ли запущенные процессы бота...")
try:
    output = subprocess.check_output("tasklist", shell=True).decode()
    for line in output.splitlines():
        if "python.exe" in line and "bot.py" in line:
            pid = int(line.split()[1])
            print(f"❌ Найден процесс bot.py с PID {pid}, убиваем его...")
            os.system(f"taskkill /F /PID {pid}")
except Exception as e:
    print(f"⚠️ Ошибка при проверке процессов: {e}")

time.sleep(1)

# ================= 3. Запускаем bot.py =================
print("🚀 Запускаем bot.py...")
subprocess.run([sys.executable, "bot.py"])
