from collections import Counter
import pytest
from registry import Registry
from people import Student


@pytest.fixture
def loaded_registry(tmp_path):
    file_path = tmp_path / "anketa.txt"
    content = "\n".join([
        "s;Яковлев Яков;yakov@mail.ru;+79991110001;ИС-101",          # строка 1 (верная)
        "t;Абрамова Анна;abramova@mail.ru;89991110002;Кафедра ОП",  # строка 2 (верная)
        "s;Петров Пётр;petrov@mail.ru;+79991110003;ИС-102",          # строка 3 (верная)
        "x;Сбой Тип;bad1@mail.ru;+79991110004;Группа1",              # строка 4 (брак: неизвестный тип)
        "s;Мало Полей;bad2@mail.ru",                                # строка 5 (брак: мало полей)
        "s;Без Группы;bad3@mail.ru;+79991110005;   ",                # строка 6 (брак: пустая группа)
    ]) + "\n"
    file_path.write_text(content, encoding="utf-8")

    reg = Registry()
    reg.load(str(file_path))
    return reg


# 1. пустой журнал имеет длину ноль
def test_empty_registry_len_zero():
    reg = Registry()
    assert len(reg) == 0


# 2. после загрузки в журнале ровно три анкеты
def test_loaded_registry_has_three_accepted(loaded_registry):
    assert len(loaded_registry) == 3


# 3. в списке брака ровно три записи
def test_rejected_has_three_records(loaded_registry):
    assert len(loaded_registry.rejected) == 3


# 4. у записей брака правильные номера строк
def test_rejected_line_numbers(loaded_registry):
    line_nums = [item[0] for item in loaded_registry.rejected]
    assert line_nums == [4, 5, 6]


# 5. загрузка несуществующего файла возвращает False и не роняет программу
def test_missing_file_returns_false(tmp_path):
    reg = Registry()
    missing = tmp_path / "no_such_file.txt"
    assert reg.load(str(missing)) is False
    assert len(reg) == 0


# 6. счётчик ролей даёт верный словарь
def test_role_counts(loaded_registry):
    counts = dict(Counter(p.role() for p in loaded_registry.accepted))
    assert counts == {"студент": 2, "преподаватель": 1}


# 7. счётчик групп считает только студентов
def test_group_counts_only_students(loaded_registry):
    student_groups = dict(
        Counter(p.extra() for p in loaded_registry.accepted if isinstance(p, Student))
    )
    assert student_groups == {"ИС-101": 1, "ИС-102": 1}


# 8. журнал перебирается циклом for
def test_iterate_accepted_with_for(loaded_registry):
    fios = []
    for person in loaded_registry.accepted:
        fios.append(person.fio)
    assert len(fios) == 3


# 9. сортировка по алфавиту ставит фамилии в правильном порядке
def test_alphabetical_sort(loaded_registry):
    surnames = [p.fio.split()[0] for p in loaded_registry.accepted]
    assert surnames == ["Абрамова", "Петров", "Яковлев"]


# 10. save_ok пишет по строке на человека
def test_save_ok_writes_line_per_person(loaded_registry, tmp_path):
    ok_path = tmp_path / "ok.txt"
    err_path = tmp_path / "errors.txt"
    loaded_registry.save_files(str(ok_path), str(err_path))

    lines = ok_path.read_text(encoding="utf-8").splitlines()
    person_lines = [line for line in lines if " | " in line and not line.startswith("№")]
    assert len(person_lines) == 3


# 11. save_errors пишет причину отказа
def test_save_errors_writes_reason(loaded_registry, tmp_path):
    ok_path = tmp_path / "ok.txt"
    err_path = tmp_path / "errors.txt"
    loaded_registry.save_files(str(ok_path), str(err_path))

    err_text = err_path.read_text(encoding="utf-8")
    assert "неизвестный тип: x" in err_text
    assert "неверное количество полей" in err_text
    assert "пустая группа" in err_text
