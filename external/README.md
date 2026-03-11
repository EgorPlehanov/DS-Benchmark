# Vendored external libraries

This directory is used to keep third-party Dempster-Shafer libraries locally in the repository workspace for:

- reproducible profiling runs,
- source-code inspection,
- stable benchmarking against fixed revisions.

## Managed repositories

- `py_dempster_shafer` (`https://github.com/reineking/pyds.git`)
- `dst-py` (`https://github.com/geekabel/dst-py.git`)
- `dstz` (`https://github.com/ztxtech/dstz.git`)

## Bootstrap and pinning workflow

Run:

```bash
bash scripts/vendor/fetch_external_libs.sh
```

Behavior:

- If `external/versions.lock` exists, repositories are checked out to exact pinned SHAs.
- If `external/versions.lock` is missing, repositories are bootstrapped from default refs
  (`main` / `master`) and then exact SHAs are written to `external/versions.lock`.

Then install dependencies:

```bash
pip install -r requirements.txt
```

To refresh pinned versions intentionally, run:

```bash
bash scripts/vendor/fetch_external_libs.sh --update-lock
```

## Lock file format

`external/versions.lock` stores one pinned SHA per repository:

```text
py_dempster_shafer=<commit_sha>
dst-py=<commit_sha>
dstz=<commit_sha>
```

---

# Локальные внешние библиотеки

Эта директория нужна, чтобы хранить сторонние библиотеки теории Демпстера-Шейфера локально в рабочем дереве репозитория для:

- воспроизводимого профилирования,
- анализа исходного кода,
- стабильного сравнения на фиксированных версиях.

## Подключаемые репозитории

- `py_dempster_shafer` (`https://github.com/reineking/pyds.git`)
- `dst-py` (`https://github.com/geekabel/dst-py.git`)
- `dstz` (`https://github.com/ztxtech/dstz.git`)

## Bootstrap и фиксация версий

Запуск:

```bash
bash scripts/vendor/fetch_external_libs.sh
```

Поведение:

- Если `external/versions.lock` уже существует, будут установлены **ровно зафиксированные SHA**.
- Если `external/versions.lock` отсутствует, репозитории будут загружены с дефолтных веток
  (`main` / `master`), после чего текущие SHA будут автоматически записаны в `external/versions.lock`.

Далее установка зависимостей:

```bash
pip install -r requirements.txt
```

Чтобы осознанно обновить зафиксированные версии, выполните:

```bash
bash scripts/vendor/fetch_external_libs.sh --update-lock
```

## Формат lock-файла

`external/versions.lock` хранит по одному SHA на библиотеку:

```text
py_dempster_shafer=<commit_sha>
dst-py=<commit_sha>
dstz=<commit_sha>
```
