import os
import sys

#Comandos predefinidos pelo Django
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Projeto_appw.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
