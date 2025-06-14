#!/usr/bin/env python
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram_backend.settings')

import django
django.setup()

from django.contrib.auth import get_user_model

def main():
    User = get_user_model()
    usernames_list = [
        "vasya.ivanov", "second-user", "third-user-username", "NoEmail",
        "NoFirstName", "NoLastName", "NoPassword", "TooLongEmail",
        "the-username-that-is-150-characters-long-and-should-not-pass-validation-if-the-serializer-is-configured-correctly-otherwise-the-current-test-will-fail-",
        "TooLongFirstName", "TooLongLastName", "InvalidU$ername", "EmailInUse"
    ]
    deleted, _ = User.objects.filter(username__in=usernames_list).delete()
    if deleted:
        print(f"Удалено {deleted} тестовых пользователей.")
        sys.exit(0)
    else:
        print("Не найдено ни одного тестового пользователя для удаления.")
        sys.exit(1)

if __name__ == "__main__":
    main()
