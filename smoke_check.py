import os
import sys
import importlib

def main() -> int:
    sys.path.append('.')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    try:
        import django  # noqa: F401
        django.setup()
    except Exception as e:
        print(f'DJANGO_SETUP_FAILED: {e}')
        return 1

    third_party = [
        'django',
        'rest_framework',
        'langchain',
        'langchain_openai',
        'langchain_community',
        'langchain_chroma',
        'openai',
        'tiktoken',
        'chromadb',
        'pypdf',
        'docx',
        'unstructured',
        'tavily',
        'dotenv',
        'numpy',
    ]

    api_modules = [
        'api.utils',
        'api.embeddings',
        'api.vectorstore',
        'api.retriever',
        'api.agent',
        'api.memory',
    ]

    failed = []
    for mod in third_party:
        try:
            importlib.import_module(mod)
        except Exception as e:
            failed.append((mod, str(e)))

    api_failed = []
    for mod in api_modules:
        try:
            importlib.import_module(mod)
        except Exception as e:
            api_failed.append((mod, str(e)))

    if failed:
        print('FAILED:', failed)
    else:
        print('ALL_OK')

    if api_failed:
        print('API_FAILED:', api_failed)
    else:
        print('API_ALL_OK')

    return 0 if not failed and not api_failed else 2

if __name__ == '__main__':
    raise SystemExit(main())


