class AnketaError(Exception):
    pass


class Person:

    def __init__(self, fio_raw: str, email_raw: str, phone_raw: str):
        self.fio = self.validate_fio(fio_raw)
        self.email = self.validate_email(email_raw)
        self.phone_digits, self.phone_display = self.validate_phone(phone_raw)

    @classmethod
    def parse(cls, raw_line: str):
        """Разбирает строку вида 'type;fio;email;phone[;extra]' и создаёт объект."""
        parts = raw_line.split(";")
        if len(parts) < 4:
            raise AnketaError("недостаточно полей в строке")

        kind = parts[0].strip().lower()
        fio = parts[1]
        email = parts[2]
        phone = parts[3]

        if kind == "s":
            if len(parts) < 5:
                raise AnketaError("у студента должна быть указана группа")
            return Student(fio, email, phone, parts[4])
        elif kind == "t":
            if len(parts) < 5:
                raise AnketaError("у преподавателя должна быть указана кафедра")
            return Teacher(fio, email, phone, parts[4])
        elif kind == "p":
            return cls(fio, email, phone)
        else:
            raise AnketaError(f"неизвестный тип: {kind}")

    @staticmethod
    def validate_fio(fio_raw: str) -> str:
        words = fio_raw.strip().split()
        if len(words) < 2:
            raise AnketaError("в ФИО меньше двух слов")
        normalized_words = [
            "-".join(part.capitalize() for part in word.split("-"))
            for word in words
        ]
        return " ".join(normalized_words)

    @staticmethod
    def validate_email(email_raw: str) -> str:
        email = email_raw.strip().lower()
        if any(c.isspace() for c in email):
            raise AnketaError("в почте не должно быть пробелов")
        if email.count("@") != 1:
            raise AnketaError("некорректная почта (нет '@' или их больше одной)")

        user, domain = email.split("@")
        if not user or not domain or "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise AnketaError("некорректный формат почтового домена")
        return email

    @staticmethod
    def validate_phone(phone_raw: str) -> tuple[str, str]:
        digits = "".join(c for c in phone_raw if c.isdigit())
        if len(digits) != 11 or digits[0] not in ("7", "8"):
            raise AnketaError(f"некорректный телефон (цифр: {len(digits)})")

        masked = f"+7 ({digits[1:4]}) ***-**-{digits[9:11]}"
        return digits, masked

    def short_fio(self) -> str:
        return self.fio

    def masked_phone(self) -> str:
        return self.phone_display

    def role(self) -> str:
        return "лицо"

    def extra(self) -> str:
        return ""

    def __str__(self) -> str:
        return f"{self.fio} ({self.role()})"

    def __lt__(self, other) -> bool:
        if isinstance(other, Person):
            return self.fio < other.fio
        return NotImplemented


class Student(Person):

    def __init__(self, fio_raw: str, email_raw: str, phone_raw: str, group_raw: str):
        super().__init__(fio_raw, email_raw, phone_raw)
        self.group = self.validate_group(group_raw)

    @staticmethod
    def validate_group(group_raw: str) -> str:
        group = group_raw.strip()
        if not group:
            raise AnketaError("пустая группа")
        return group

    def role(self) -> str:
        return "студент"

    def extra(self) -> str:
        return self.group


class Teacher(Person):

    def __init__(self, fio_raw: str, email_raw: str, phone_raw: str, department_raw: str):
        super().__init__(fio_raw, email_raw, phone_raw)
        self.department = self.validate_department(department_raw)

    @staticmethod
    def validate_department(dept_raw: str) -> str:
        dept = dept_raw.strip()
        if not dept:
            raise AnketaError("пустая кафедра")
        return dept

    def role(self) -> str:
        return "преподаватель"

    def extra(self) -> str:
        return self.department
