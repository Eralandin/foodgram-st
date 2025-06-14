# clear_db.ps1

$env:DJANGO_SETTINGS_MODULE = "backend.settings"

# Путь к manage.py
$managePyPath = Get-ChildItem -Path .. -Recurse -Filter "manage.py" | Where-Object { $_.FullName -notmatch "env|venv" }

if ($managePyPath.Count -ne 1) {
    Write-Host "❌ Убедитесь, что в проекте содержится только один файл manage.py"
    exit 1
}

$python = "..\venv\Scripts\python.exe"
$managePath = $managePyPath.FullName

# Django shell-питон-код как строка
$script = @'
from django.contrib.auth import get_user_model
User = get_user_model()
usernames_list = [
    "vasya.ivanov", "second-user", "third-user-username", "NoEmail",
    "NoFirstName", "NoLastName", "NoPassword", "TooLongEmail",
    "the-username-that-is-150-characters-long-and-should-not-pass-validation-if-the-serializer-is-configured-correctly-otherwise-the-current-test-will-fail-",
    "TooLongFirstName", "TooLongLastName", "InvalidU$ername", "EmailInUse"
]
deleted, _ = User.objects.filter(username__in=usernames_list).delete()
exit(1) if deleted == 0 else exit(0)
'@

# Запускаем Python с shell и передаём код через -c
& $python $managePath shell -c $script

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при удалении пользователей (или не было кого удалять)"
    exit $LASTEXITCODE
}

Write-Host "✅ База данных очищена"
