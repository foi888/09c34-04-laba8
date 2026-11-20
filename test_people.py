import pytest
from people import AnketaError, Person, Student, Teacher
from registry import Registry


# 1. ФИО приводится к одному виду (parametrize, не меньше четырёх наборов: разный регистр, лишние пробелы)
@pytest.mark.parametrize(
    "raw_fio, expected",
    [
        ("иванов иван иванович", "Иванов Иван Иванович"),
        ("ИВАНОВ ИВАН ИВАНОВИЧ", "Иванов Иван Иванович"),
        ("   иванов   иван   иванович   ", "Иванов Иван Иванович"),
        ("  иВаНоВ   иВаН  ", "Иванов Иван"),
    ],
)
def test_fio_normalized(raw_fio, expected):
    assert Person.validate_fio(raw_fio) == expected


# 2. ФИО из одного слова отклоняется (pytest.raises(AnketaError))
def test_fio_single_word_rejected():
    with pytest.raises(AnketaError):
        Person.validate_fio("Иванов")


# 3. Почта приводится к нижнему регистру (parametrize, не меньше двух наборов)
@pytest.mark.parametrize(
    "raw_email, expected",
    [
        ("User@Example.COM", "user@example.com"),
        ("  IVAN.PETROV@MAIL.RU  ", "ivan.petrov@mail.ru"),
        ("Admin@Domain.Org", "admin@domain.org"),
    ],
)
def test_email_lowercase(raw_email, expected):
    assert Person.validate_email(raw_email) == expected


# 4. Плохая почта отклоняется (parametrize + pytest.raises, не меньше четырёх видов брака)
@pytest.mark.parametrize(
    "bad_email",
    [
        "",
        "no-at-symbol.ru",
        "user@domain",
        "@domain.ru",
        "user@",
        "user@a@b.ru",
    ],
)
def test_bad_email_rejected(bad_email):
    with pytest.raises(AnketaError):
        Person.validate_email(bad_email)


# 5. Телефон приводится к одному виду (parametrize: все четыре записи дают один результат)
@pytest.mark.parametrize(
    "raw_phone",
    [
        "+7 (999) 123-45-67",
        "89991234567",
        "8 (999) 123 45 67",
        "7-999-123-45-67",
    ],
)
def test_phone_normalized_to_one_form(raw_phone):
    _, masked = Person.validate_phone(raw_phone)
    assert masked == "+7 (999) ***-**-67"


# 6. Плохой телефон отклоняется (parametrize + pytest.raises)
@pytest.mark.parametrize(
    "bad_phone",
    [
        "",
        "12345",
        "+7999123456789",
        "29991234567",
    ],
)
def test_bad_phone_rejected(bad_phone):
    with pytest.raises(AnketaError):
        Person.validate_phone(bad_phone)


# 7. Телефон выводится с маской (обычный assert)
def test_masked_phone():
    s = Student("Иванов Иван", "test@example.com", "+79991234567", "09.02.07-1")
    assert s.masked_phone() == "+7 (999) ***-**-67"


# 8. ФИО сокращается до инициалов (обычный assert)
def test_short_fio():
    s = Student("иванов иван иванович", "test@example.com", "+79991234567", "09.02.07-1")
    assert s.short_fio() == "Иванов Иван Иванович"


# 9. Студент и преподаватель отвечают по-разному (проверить role() у обоих)
def test_roles_differ():
    student = Student("Иванов Иван", "s@example.com", "+79991234567", "09.02.07-1")
    teacher = Teacher("Петров Пётр", "t@example.com", "+79997654321", "Кафедра ИТ")
    assert student.role() != teacher.role()
    assert student.role() == "студент"
    assert teacher.role() == "преподаватель"


# 10. Студент без группы отклоняется (pytest.raises)
def test_student_without_group_rejected():
    with pytest.raises(AnketaError):
        Student("Иванов Иван", "s@example.com", "+79991234567", "   ")


# 11. Строка файла разбирается верно (два теста: студент и преподаватель, с проверкой типа)
def test_parse_line_student(tmp_path):
    f = tmp_path / "student.txt"
    f.write_text("s;Иванов Иван;ivan@mail.ru;+79991234567;ИБ-21\n", encoding="utf-8")
    reg = Registry()
    assert reg.load(str(f)) is True
    assert len(reg.accepted) == 1
    assert isinstance(reg.accepted[0], Student)
    assert reg.accepted[0].extra() == "ИБ-21"


def test_parse_line_teacher(tmp_path):
    f = tmp_path / "teacher.txt"
    f.write_text("t;Смирнова Анна;anna@mail.ru;89991234567;Высшая математика\n", encoding="utf-8")
    reg = Registry()
    assert reg.load(str(f)) is True
    assert len(reg.accepted) == 1
    assert isinstance(reg.accepted[0], Teacher)
    assert reg.accepted[0].extra() == "Высшая математика"


# 12. Плохая строка отклоняется (parametrize: неизвестный тип, мало полей, пустая строка)
@pytest.mark.parametrize(
    "bad_line",
    [
        "x;Иванов Иван;ivan@mail.ru;+79991234567;ИБ-21",
        "s;Иванов Иван;ivan@mail.ru",
        "",
        "   ",
    ],
)
def test_bad_line_rejected(tmp_path, bad_line):
    f = tmp_path / "bad.txt"
    f.write_text(bad_line + "\n", encoding="utf-8")
    reg = Registry()
    reg.load(str(f))
    assert len(reg.accepted) == 0
    if bad_line.strip():
        assert len(reg.rejected) == 1


def test_dvoynaya_familiya():
    person = Person.parse(
        "s;петров-водкин кузьма;petrov@mail.ru;89123456789;09с34"
    )
    assert person.fio == "Петров-Водкин Кузьма"
    assert isinstance(person, Student)
    assert person.group == "09с34"


def test_mail_s_probelom_vnutri():
    with pytest.raises(AnketaError):
        Person.parse(
            "t;соколов алексей;soko  lov@voenmeh.ru;8 (921) 333-22-11;Кафедра И9"
        )
